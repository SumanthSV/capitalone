# services/smart_irrigation.py
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
from services.offline_cache import offline_cache
from services.contextual_memory import contextual_memory_service, CropStage

class IrrigationRecommendation(Enum):
    URGENT = "urgent"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    NOT_NEEDED = "not_needed"
    AVOID = "avoid"
    UNKNOWN = "unknown"  # When data is insufficient

@dataclass
class SoilMoistureData:
    surface_moisture: float  # 0-100%
    root_zone_moisture: float  # 0-100%
    deep_moisture: float  # 0-100%
    temperature: float
    timestamp: datetime
    source: str

@dataclass
class WeatherForecast:
    date: datetime
    temperature_min: float
    temperature_max: float
    humidity: float
    precipitation_mm: float
    wind_speed: float
    evapotranspiration: float
    confidence: float

@dataclass
class IrrigationDecision:
    recommendation: IrrigationRecommendation
    confidence: float
    water_amount_liters: float
    timing: str
    method: str
    reasoning: List[str]
    risk_factors: List[str]
    next_check_hours: int
    alternative_actions: List[str]
    data_availability: Dict[str, bool]  # Track what data was available

class SmartIrrigationEngine:
    """Advanced irrigation decision engine with real data only"""
    
    def __init__(self):
        self.nasa_power_base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        
        # Crop water requirements (liters per day per plant at different stages)
        self.crop_water_requirements = {
            "rice": {
                CropStage.SEEDLING: 2.0,
                CropStage.VEGETATIVE: 4.0,
                CropStage.FLOWERING: 6.0,
                CropStage.FRUITING: 5.0,
                CropStage.MATURITY: 3.0
            },
            "wheat": {
                CropStage.SEEDLING: 1.5,
                CropStage.VEGETATIVE: 3.0,
                CropStage.FLOWERING: 4.5,
                CropStage.FRUITING: 4.0,
                CropStage.MATURITY: 2.0
            },
            "cotton": {
                CropStage.SEEDLING: 2.5,
                CropStage.VEGETATIVE: 4.5,
                CropStage.FLOWERING: 7.0,
                CropStage.FRUITING: 6.5,
                CropStage.MATURITY: 3.5
            },
            "tomato": {
                CropStage.SEEDLING: 1.0,
                CropStage.VEGETATIVE: 2.5,
                CropStage.FLOWERING: 4.0,
                CropStage.FRUITING: 5.0,
                CropStage.MATURITY: 3.0
            }
        }
        
        # Soil moisture thresholds by crop
        self.moisture_thresholds = {
            "rice": {"critical": 80, "optimal": 90, "maximum": 95},
            "wheat": {"critical": 40, "optimal": 60, "maximum": 80},
            "cotton": {"critical": 45, "optimal": 65, "maximum": 85},
            "tomato": {"critical": 50, "optimal": 70, "maximum": 85}
        }
    
    def get_nasa_power_data(self, latitude: float, longitude: float, days: int = 7) -> Optional[Dict]:
        """Get NASA POWER API data - returns None if unavailable"""
        try:
            cache_key = f"nasa_power_{latitude}_{longitude}_{days}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                return cached_data
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                "parameters": "T2M,T2M_MIN,T2M_MAX,RH2M,PRECTOTCORR,WS2M,GWETROOT,GWETTOP",
                "community": "AG",
                "longitude": longitude,
                "latitude": latitude,
                "start": start_date.strftime("%Y%m%d"),
                "end": end_date.strftime("%Y%m%d"),
                "format": "JSON"
            }
            
            response = requests.get(self.nasa_power_base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache for 6 hours
            offline_cache.set(cache_key, data, expiry_hours=6)
            return data
            
        except Exception as e:
            print(f"NASA POWER API error: {str(e)}")
            return None
    
    def get_soil_moisture_estimate(self, latitude: float, longitude: float) -> Optional[SoilMoistureData]:
        """Get soil moisture data - returns None if unavailable"""
        try:
            nasa_data = self.get_nasa_power_data(latitude, longitude, days=3)
            
            if nasa_data and "properties" in nasa_data:
                parameters = nasa_data["properties"]["parameter"]
                
                # Get latest values
                latest_date = max(parameters.get("GWETTOP", {}).keys())
                
                surface_moisture = parameters.get("GWETTOP", {}).get(latest_date, None)
                root_zone_moisture = parameters.get("GWETROOT", {}).get(latest_date, None)
                temperature = parameters.get("T2M", {}).get(latest_date, None)
                
                if surface_moisture is not None and root_zone_moisture is not None:
                    return SoilMoistureData(
                        surface_moisture=surface_moisture * 100,
                        root_zone_moisture=root_zone_moisture * 100,
                        deep_moisture=root_zone_moisture * 90,  # Estimate
                        temperature=temperature or 25,
                        timestamp=datetime.now(),
                        source="nasa_power"
                    )
            
            return None
            
        except Exception as e:
            print(f"Soil moisture error: {str(e)}")
            return None
    
    def make_irrigation_decision(self, user_id: str, crop_name: str, 
                               latitude: float, longitude: float) -> IrrigationDecision:
        """Make irrigation decision with real data only"""
        try:
            # Track data availability
            data_availability = {
                "farming_context": False,
                "soil_moisture": False,
                "weather_forecast": False,
                "irrigation_history": False
            }
            
            # Get farming context
            context = contextual_memory_service.get_farming_context(user_id)
            if context:
                data_availability["farming_context"] = True
                crop_stage = context.crop_stages.get(crop_name.lower(), CropStage.VEGETATIVE)
            else:
                return self._insufficient_data_decision("No farming context available")
            
            # Get soil moisture data
            soil_moisture = self.get_soil_moisture_estimate(latitude, longitude)
            if soil_moisture:
                data_availability["soil_moisture"] = True
            
            # Get weather forecast
            from services.weather import weather_service
            weather_forecast = weather_service.get_weather_forecast(context.location, days=5)
            if weather_forecast:
                data_availability["weather_forecast"] = True
                weather_forecast_processed = self._process_weather_forecast(weather_forecast)
            else:
                weather_forecast_processed = []
            
            # Get irrigation history
            irrigation_history = contextual_memory_service.get_irrigation_history(user_id, days=14)
            if irrigation_history:
                data_availability["irrigation_history"] = True
            
            # Check if we have minimum required data
            if not data_availability["farming_context"]:
                return self._insufficient_data_decision("Please complete your farming profile first")
            
            if not data_availability["soil_moisture"] and not data_availability["weather_forecast"]:
                return self._insufficient_data_decision("Unable to access soil moisture and weather data")
            
            # Calculate water stress if we have soil moisture data
            water_stress = 0.5  # Default moderate stress
            if soil_moisture:
                water_stress = self._calculate_water_stress(
                    crop_name.lower(), crop_stage, soil_moisture, weather_forecast_processed
                )
            
            # Analyze irrigation patterns
            irrigation_pattern = self._analyze_irrigation_pattern(irrigation_history)
            
            # Make decision
            decision = self._make_irrigation_decision_logic(
                crop_name.lower(), crop_stage, soil_moisture, weather_forecast_processed,
                water_stress, irrigation_pattern, context, data_availability
            )
            
            return decision
            
        except Exception as e:
            print(f"Irrigation decision error: {str(e)}")
            return self._insufficient_data_decision(f"Error processing irrigation decision: {str(e)}")
    
    def _insufficient_data_decision(self, reason: str) -> IrrigationDecision:
        """Return decision when insufficient data is available"""
        return IrrigationDecision(
            recommendation=IrrigationRecommendation.UNKNOWN,
            confidence=0.0,
            water_amount_liters=0,
            timing="unknown",
            method="unknown",
            reasoning=[reason],
            risk_factors=["Insufficient data for accurate recommendation"],
            next_check_hours=24,
            alternative_actions=[
                "Complete your farming profile",
                "Check soil moisture manually",
                "Monitor weather forecast",
                "Observe plant stress signs"
            ],
            data_availability={}
        )
    
    def _process_weather_forecast(self, forecast_data: List[Dict]) -> List[WeatherForecast]:
        """Process weather forecast data"""
        forecasts = []
        
        for item in forecast_data[:5]:
            temp = item.get("temperature", 25)
            humidity = item.get("humidity", 60)
            wind = item.get("wind_speed", 5)
            
            et = self._calculate_evapotranspiration(temp, humidity, wind)
            
            forecasts.append(WeatherForecast(
                date=datetime.strptime(item["date"], "%Y-%m-%d"),
                temperature_min=temp - 5,
                temperature_max=temp + 5,
                humidity=humidity,
                precipitation_mm=item.get("rainfall", 0),
                wind_speed=wind,
                evapotranspiration=et,
                confidence=0.8
            ))
        
        return forecasts
    
    def _calculate_evapotranspiration(self, temperature: float, humidity: float, wind_speed: float) -> float:
        """Calculate reference evapotranspiration"""
        try:
            # Simplified ET calculation
            temp_factor = (temperature + 17.8) / 100
            humidity_factor = (100 - humidity) / 100
            wind_factor = 1 + (wind_speed * 0.1)
            
            et0 = temp_factor * humidity_factor * wind_factor * 3.5
            return max(0, min(et0, 15))  # Reasonable bounds
            
        except Exception as e:
            print(f"ET calculation error: {str(e)}")
            return 4.0  # Default ET value
    
    def _calculate_water_stress(self, crop_name: str, crop_stage: CropStage, 
                              soil_moisture: SoilMoistureData, 
                              weather_forecast: List[WeatherForecast]) -> float:
        """Calculate water stress level (0-1, where 1 is maximum stress)"""
        try:
            # Get crop-specific thresholds
            thresholds = self.moisture_thresholds.get(crop_name, 
                                                    self.moisture_thresholds["wheat"])
            
            # Current moisture stress
            current_moisture = soil_moisture.root_zone_moisture
            if current_moisture < thresholds["critical"]:
                moisture_stress = 1.0
            elif current_moisture < thresholds["optimal"]:
                moisture_stress = (thresholds["optimal"] - current_moisture) / \
                                (thresholds["optimal"] - thresholds["critical"])
            else:
                moisture_stress = 0.0
            
            # Future weather stress
            if weather_forecast:
                future_rain = sum(f.precipitation_mm for f in weather_forecast[:3])
                future_et = sum(f.evapotranspiration for f in weather_forecast[:3])
                
                water_balance = future_rain - future_et
                if water_balance < -10:
                    weather_stress = 0.8
                elif water_balance < 0:
                    weather_stress = 0.4
                else:
                    weather_stress = 0.0
            else:
                weather_stress = 0.5  # Unknown weather = moderate stress
            
            # Crop stage factor
            stage_factors = {
                CropStage.SEEDLING: 0.8,
                CropStage.VEGETATIVE: 0.6,
                CropStage.FLOWERING: 1.0,  # Most critical
                CropStage.FRUITING: 0.9,
                CropStage.MATURITY: 0.4
            }
            
            stage_factor = stage_factors.get(crop_stage, 0.6)
            
            # Combined stress
            total_stress = (moisture_stress * 0.6 + weather_stress * 0.4) * stage_factor
            
            return min(1.0, max(0.0, total_stress))
            
        except Exception as e:
            print(f"Water stress calculation error: {str(e)}")
            return 0.5  # Default moderate stress
    
    def _make_irrigation_decision_logic(self, crop_name: str, crop_stage: CropStage,
                                      soil_moisture: Optional[SoilMoistureData],
                                      weather_forecast: List[WeatherForecast],
                                      water_stress: float, irrigation_pattern: Dict,
                                      context, data_availability: Dict) -> IrrigationDecision:
        """Core irrigation decision logic with real data only"""
        reasoning = []
        risk_factors = []
        alternative_actions = []
        
        # Check data availability
        missing_data = [k for k, v in data_availability.items() if not v]
        if missing_data:
            reasoning.append(f"Limited data available: {', '.join(missing_data)}")
        
        # Get crop water requirements
        water_req = self.crop_water_requirements.get(crop_name, 
                                                   self.crop_water_requirements["wheat"])
        daily_water_need = water_req.get(crop_stage, 3.0)
        
        # Calculate water amount needed
        farm_size_acres = context.farm_size_acres
        plants_per_acre = 10000  # Rough estimate, varies by crop
        total_water_liters = daily_water_need * plants_per_acre * farm_size_acres
        
        # Decision logic based on available data
        if not soil_moisture and not weather_forecast:
            return IrrigationDecision(
                recommendation=IrrigationRecommendation.UNKNOWN,
                confidence=0.0,
                water_amount_liters=0,
                timing="unknown",
                method=context.irrigation_method,
                reasoning=["Cannot make recommendation without soil moisture or weather data"],
                risk_factors=["No real-time data available"],
                next_check_hours=6,
                alternative_actions=[
                    "Check soil moisture manually by digging 6 inches deep",
                    "Observe plant stress signs (wilting, leaf curling)",
                    "Check local weather forecast"
                ],
                data_availability=data_availability
            )
        
        # Make decision based on available data
        if soil_moisture and water_stress > 0.8:
            recommendation = IrrigationRecommendation.URGENT
            confidence = 0.9
            reasoning.append(f"High water stress detected ({water_stress:.1%})")
            reasoning.append(f"Soil moisture below critical level ({soil_moisture.root_zone_moisture:.1f}%)")
            timing = "immediately"
            
        elif soil_moisture and water_stress > 0.6:
            recommendation = IrrigationRecommendation.RECOMMENDED
            confidence = 0.8
            reasoning.append(f"Moderate water stress ({water_stress:.1%})")
            timing = "within 6 hours"
            
        elif weather_forecast:
            # Check weather forecast for rain
            rain_expected = sum(f.precipitation_mm for f in weather_forecast[:2])
            if rain_expected > 10:
                recommendation = IrrigationRecommendation.NOT_NEEDED
                confidence = 0.7
                reasoning.append(f"Rain expected ({rain_expected:.1f}mm in next 2 days)")
                timing = "wait for rain"
                total_water_liters = 0
            else:
                recommendation = IrrigationRecommendation.OPTIONAL
                confidence = 0.6
                reasoning.append("No rain expected, moderate irrigation recommended")
                timing = "evening preferred"
        else:
            recommendation = IrrigationRecommendation.UNKNOWN
            confidence = 0.3
            reasoning.append("Insufficient data for accurate recommendation")
            timing = "check data sources"
            total_water_liters = 0
        
        # Check for risk factors from weather
        if weather_forecast:
            if any(f.temperature_max > 35 for f in weather_forecast[:2]):
                risk_factors.append("High temperatures expected - increase water amount by 20%")
                total_water_liters *= 1.2
                
            if any(f.wind_speed > 15 for f in weather_forecast[:2]):
                risk_factors.append("High winds expected - avoid overhead irrigation")
        
        # Adjust for irrigation method
        irrigation_method = context.irrigation_method
        if irrigation_method == "drip":
            total_water_liters *= 0.7  # More efficient
            reasoning.append("Drip irrigation - reduced water requirement")
        elif irrigation_method == "flood":
            total_water_liters *= 1.5  # Less efficient
            reasoning.append("Flood irrigation - increased water requirement")
        
        # Alternative actions based on recommendation
        if recommendation == IrrigationRecommendation.NOT_NEEDED:
            alternative_actions.extend([
                "Monitor soil moisture daily",
                "Check weather forecast for changes"
            ])
        elif recommendation == IrrigationRecommendation.UNKNOWN:
            alternative_actions.extend([
                "Check soil moisture manually",
                "Observe plant stress indicators",
                "Consult local weather forecast"
            ])
        else:
            alternative_actions.extend([
                "Consider mulching to retain moisture",
                "Check for pest/disease issues"
            ])
        
        # Next check timing
        if recommendation in [IrrigationRecommendation.URGENT, IrrigationRecommendation.RECOMMENDED]:
            next_check_hours = 12
        elif recommendation == IrrigationRecommendation.UNKNOWN:
            next_check_hours = 6
        else:
            next_check_hours = 24
        
        return IrrigationDecision(
            recommendation=recommendation,
            confidence=confidence,
            water_amount_liters=max(0, total_water_liters),
            timing=timing,
            method=irrigation_method,
            reasoning=reasoning,
            risk_factors=risk_factors,
            next_check_hours=next_check_hours,
            alternative_actions=alternative_actions,
            data_availability=data_availability
        )
    
    def _analyze_irrigation_pattern(self, irrigation_history) -> Dict:
        """Analyze historical irrigation patterns"""
        if not irrigation_history:
            return {"frequency": 7, "effectiveness": 0.5, "pattern": "unknown"}
        
        # Calculate average frequency
        dates = [irr.irrigation_date for irr in irrigation_history]
        if len(dates) > 1:
            intervals = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            avg_frequency = sum(intervals) / len(intervals)
        else:
            avg_frequency = 7
        
        # Calculate effectiveness
        ratings = [irr.effectiveness_rating for irr in irrigation_history 
                  if irr.effectiveness_rating is not None]
        avg_effectiveness = sum(ratings) / len(ratings) if ratings else 0.5
        
        return {
            "frequency": avg_frequency,
            "effectiveness": avg_effectiveness,
            "pattern": "regular" if 5 <= avg_frequency <= 10 else "irregular"
        }

# Global smart irrigation engine
smart_irrigation_engine = SmartIrrigationEngine()
# services/weather.py
import requests
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from services.offline_cache import offline_cache
from services.error_handler import error_handler, APIError

load_dotenv()

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
        if not self.api_key:
            raise APIError("OpenWeather API key not found", "WEATHER_API_KEY_MISSING")
    
    def get_current_weather(self, location: str) -> Optional[Dict]:
        """Get current weather - returns None if unavailable"""
        if not location.strip():
            return None
            
        cache_key = f"weather_current_{location.lower()}"
        
        # Try cache first
        cached_data = offline_cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            weather_data = {
                "temperature": round(data["main"]["temp"], 1),
                "humidity": data["main"]["humidity"],
                "rainfall": data.get("rain", {}).get("1h", 0),
                "description": data["weather"][0]["description"].title(),
                "wind_speed": data["wind"]["speed"],
                "pressure": data["main"]["pressure"],
                "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                "location": location,
                "timestamp": datetime.now().isoformat(),
                "source": "openweather"
            }
            
            # Cache for 1 hour
            offline_cache.set(cache_key, weather_data, expiry_hours=1)
            return weather_data
            
        except Exception as e:
            print(f"Weather API error: {str(e)}")
            return None
    
    def get_weather_forecast(self, location: str, days: int = 7) -> Optional[List[Dict]]:
        """Get weather forecast - returns None if unavailable"""
        if not location.strip():
            return None
            
        cache_key = f"weather_forecast_{location.lower()}_{days}"
        
        # Try cache first
        cached_data = offline_cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric",
                "cnt": min(days * 8, 40)  # Max 40 forecasts (5 days)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            forecast = []
            
            for item in data["list"]:
                forecast.append({
                    "datetime": item["dt_txt"],
                    "date": datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d"),
                    "time": datetime.fromtimestamp(item["dt"]).strftime("%H:%M"),
                    "temperature": round(item["main"]["temp"], 1),
                    "humidity": item["main"]["humidity"],
                    "rainfall": item.get("rain", {}).get("3h", 0),
                    "description": item["weather"][0]["description"].title(),
                    "wind_speed": item["wind"]["speed"],
                    "pressure": item["main"]["pressure"]
                })
            
            # Cache for 3 hours
            offline_cache.set(cache_key, forecast, expiry_hours=3)
            return forecast
            
        except Exception as e:
            print(f"Weather forecast API error: {str(e)}")
            return None
    
    def get_agricultural_alerts(self, location: str, current_weather: Dict) -> List[Dict]:
        """Generate agricultural alerts based on weather conditions"""
        if not current_weather:
            return []
            
        alerts = []
        
        # Temperature alerts
        temp = current_weather.get("temperature", 0)
        if temp > 40:
            alerts.append({
                "type": "heat_wave",
                "severity": "high",
                "message": "Extreme heat warning! Increase irrigation and provide shade for crops.",
                "recommendations": [
                    "Water crops early morning or late evening",
                    "Use mulching to retain soil moisture",
                    "Consider shade nets for sensitive crops"
                ]
            })
        elif temp < 5:
            alerts.append({
                "type": "frost",
                "severity": "high", 
                "message": "Frost warning! Protect sensitive crops from cold damage.",
                "recommendations": [
                    "Cover young plants with cloth or plastic",
                    "Use smudge pots or heaters in orchards",
                    "Harvest mature crops before frost"
                ]
            })
        
        # Rainfall alerts
        rainfall = current_weather.get("rainfall", 0)
        if rainfall > 50:
            alerts.append({
                "type": "heavy_rain",
                "severity": "medium",
                "message": "Heavy rainfall expected. Take precautions against waterlogging.",
                "recommendations": [
                    "Ensure proper drainage in fields",
                    "Delay fertilizer application",
                    "Harvest ready crops if possible"
                ]
            })
        
        # Wind alerts
        wind_speed = current_weather.get("wind_speed", 0)
        if wind_speed > 15:
            alerts.append({
                "type": "high_wind",
                "severity": "medium",
                "message": "Strong winds expected. Secure crops and equipment.",
                "recommendations": [
                    "Stake tall plants and young trees",
                    "Secure greenhouse structures",
                    "Delay spraying operations"
                ]
            })
        
        return alerts

# Global weather service instance
weather_service = WeatherService()

# Backward compatibility functions
def get_current_weather(location: str) -> Optional[Dict]:
    return weather_service.get_current_weather(location)

def get_weather_forecast(location: str, days: int = 7) -> Optional[List[Dict]]:
    return weather_service.get_weather_forecast(location, days)

def get_agricultural_alerts(location: str, current_weather: Dict) -> List[Dict]:
    return weather_service.get_agricultural_alerts(location, current_weather)
# services/proactive_advisory.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from services.contextual_memory import contextual_memory_service
from services.weather import weather_service
from services.real_market_api import real_market_api
from services.notification_service import notification_service, NotificationType
from services.user_profiles import user_profile_service

class AlertType(Enum):
    WEATHER_RISK = "weather_risk"
    IRRIGATION_URGENT = "irrigation_urgent"
    DISEASE_OUTBREAK = "disease_outbreak"
    MARKET_OPPORTUNITY = "market_opportunity"
    GOVERNMENT_SCHEME = "government_scheme"
    SEASONAL_REMINDER = "seasonal_reminder"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ProactiveAlert:
    alert_id: str
    user_id: str
    alert_type: AlertType
    risk_level: RiskLevel
    title: str
    message: str
    recommendations: List[str]
    data_sources: List[str]
    confidence: float
    expires_at: datetime
    created_at: datetime

class ProactiveAdvisoryService:
    """Service for generating proactive agricultural advice and alerts"""
    
    def __init__(self):
        self.alert_cache = {}
        self.monitoring_active = False
    
    async def start_monitoring(self):
        """Start proactive monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start monitoring tasks
        asyncio.create_task(self._weather_monitoring())
        asyncio.create_task(self._irrigation_monitoring())
        asyncio.create_task(self._market_monitoring())
        asyncio.create_task(self._seasonal_monitoring())
    
    async def stop_monitoring(self):
        """Stop proactive monitoring"""
        self.monitoring_active = False
    
    async def generate_alerts_for_user(self, user_id: str) -> List[ProactiveAlert]:
        """Generate all applicable alerts for a specific user"""
        alerts = []
        
        try:
            # Get user profile and context
            profile = user_profile_service.get_profile(user_id)
            farming_context = contextual_memory_service.get_farming_context(user_id)
            
            if not profile or not farming_context:
                return alerts
            
            # Generate different types of alerts
            weather_alerts = await self._generate_weather_alerts(user_id, profile, farming_context)
            irrigation_alerts = await self._generate_irrigation_alerts(user_id, profile, farming_context)
            market_alerts = await self._generate_market_alerts(user_id, profile, farming_context)
            seasonal_alerts = await self._generate_seasonal_alerts(user_id, profile, farming_context)
            
            alerts.extend(weather_alerts)
            alerts.extend(irrigation_alerts)
            alerts.extend(market_alerts)
            alerts.extend(seasonal_alerts)
            
            # Sort by risk level and confidence
            alerts.sort(key=lambda x: (x.risk_level.value, -x.confidence), reverse=True)
            
            return alerts
            
        except Exception as e:
            print(f"Alert generation error for user {user_id}: {str(e)}")
            return alerts
    
    async def _generate_weather_alerts(self, user_id: str, profile, farming_context) -> List[ProactiveAlert]:
        """Generate weather-related alerts"""
        alerts = []
        
        try:
            # Get weather forecast
            weather_forecast = weather_service.get_weather_forecast(profile.location, days=7)
            
            if not weather_forecast:
                return alerts
            
            # Check for extreme weather
            for day in weather_forecast[:3]:  # Next 3 days
                temp = day.get('temperature', 25)
                rainfall = day.get('rainfall', 0)
                wind_speed = day.get('wind_speed', 0)
                
                # Heat wave alert
                if temp > 40:
                    alerts.append(ProactiveAlert(
                        alert_id=f"heat_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        alert_type=AlertType.WEATHER_RISK,
                        risk_level=RiskLevel.HIGH,
                        title="🌡️ Heat Wave Warning",
                        message=f"Extreme heat expected ({temp}°C) on {day['date']}. Your crops may suffer heat stress.",
                        recommendations=[
                            "Increase irrigation frequency",
                            "Provide shade protection for sensitive crops",
                            "Harvest mature crops early if possible",
                            "Apply mulching to retain soil moisture"
                        ],
                        data_sources=["weather_api"],
                        confidence=0.9,
                        expires_at=datetime.now() + timedelta(days=1),
                        created_at=datetime.now()
                    ))
                
                # Heavy rain alert
                if rainfall > 50:
                    alerts.append(ProactiveAlert(
                        alert_id=f"rain_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        alert_type=AlertType.WEATHER_RISK,
                        risk_level=RiskLevel.MEDIUM,
                        title="🌧️ Heavy Rain Alert",
                        message=f"Heavy rainfall expected ({rainfall}mm) on {day['date']}. Risk of waterlogging.",
                        recommendations=[
                            "Ensure proper field drainage",
                            "Avoid fertilizer application",
                            "Protect harvested crops from moisture",
                            "Check for fungal disease symptoms after rain"
                        ],
                        data_sources=["weather_api"],
                        confidence=0.8,
                        expires_at=datetime.now() + timedelta(days=1),
                        created_at=datetime.now()
                    ))
                
                # Strong wind alert
                if wind_speed > 20:
                    alerts.append(ProactiveAlert(
                        alert_id=f"wind_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        alert_type=AlertType.WEATHER_RISK,
                        risk_level=RiskLevel.MEDIUM,
                        title="💨 Strong Wind Warning",
                        message=f"Strong winds expected ({wind_speed} m/s) on {day['date']}. Risk of crop damage.",
                        recommendations=[
                            "Stake tall plants and young trees",
                            "Secure greenhouse structures",
                            "Delay spraying operations",
                            "Harvest ready fruits to prevent damage"
                        ],
                        data_sources=["weather_api"],
                        confidence=0.8,
                        expires_at=datetime.now() + timedelta(days=1),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            print(f"Weather alert generation error: {str(e)}")
        
        return alerts
    
    async def _generate_irrigation_alerts(self, user_id: str, profile, farming_context) -> List[ProactiveAlert]:
        """Generate irrigation-related alerts"""
        alerts = []
        
        try:
            # Check last irrigation date
            if farming_context.last_irrigation:
                days_since_irrigation = (datetime.now() - farming_context.last_irrigation).days
                
                # Check against irrigation frequency
                if days_since_irrigation > farming_context.irrigation_frequency_days + 2:
                    risk_level = RiskLevel.HIGH if days_since_irrigation > farming_context.irrigation_frequency_days + 5 else RiskLevel.MEDIUM
                    
                    alerts.append(ProactiveAlert(
                        alert_id=f"irrigation_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        alert_type=AlertType.IRRIGATION_URGENT,
                        risk_level=risk_level,
                        title="💧 Irrigation Overdue",
                        message=f"It's been {days_since_irrigation} days since your last irrigation. Your crops may need water.",
                        recommendations=[
                            "Check soil moisture levels immediately",
                            "Look for signs of water stress in plants",
                            "Consider immediate irrigation if soil is dry",
                            "Adjust irrigation schedule based on weather"
                        ],
                        data_sources=["farming_context"],
                        confidence=0.8,
                        expires_at=datetime.now() + timedelta(days=1),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            print(f"Irrigation alert generation error: {str(e)}")
        
        return alerts
    
    async def _generate_market_alerts(self, user_id: str, profile, farming_context) -> List[ProactiveAlert]:
        """Generate market opportunity alerts"""
        alerts = []
        
        try:
            # Get price trends for user's crops
            price_trends = real_market_api.get_price_trends(profile.primary_crops, days=30)
            
            if not price_trends:
                return alerts
            
            for trend in price_trends:
                crop = trend['crop']
                change_percent = trend['change_percent']
                
                # Significant price increase
                if change_percent > 15:
                    alerts.append(ProactiveAlert(
                        alert_id=f"market_up_{user_id}_{crop}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        alert_type=AlertType.MARKET_OPPORTUNITY,
                        risk_level=RiskLevel.HIGH,
                        title=f"📈 {crop} Price Surge",
                        message=f"{crop} prices have increased by {change_percent:.1f}% in the last 30 days. Consider selling if you have stock.",
                        recommendations=[
                            f"Evaluate your {crop} inventory for immediate sale",
                            "Check local mandi prices for best rates",
                            "Consider transportation costs in profit calculation",
                            "Monitor price trends for optimal selling time"
                        ],
                        data_sources=["market_api"],
                        confidence=trend.get('confidence', 0.7),
                        expires_at=datetime.now() + timedelta(days=3),
                        created_at=datetime.now()
                    ))
                
                # Significant price decrease (buying opportunity)
                elif change_percent < -15:
                    alerts.append(ProactiveAlert(
                        alert_id=f"market_down_{user_id}_{crop}_{datetime.now().strftime('%Y%m%d')}",
                        user_id=user_id,
                        alert_type=AlertType.MARKET_OPPORTUNITY,
                        risk_level=RiskLevel.MEDIUM,
                        title=f"📉 {crop} Price Drop",
                        message=f"{crop} prices have decreased by {abs(change_percent):.1f}%. Good time to buy inputs or hold existing stock.",
                        recommendations=[
                            f"Consider buying {crop} seeds/inputs at lower prices",
                            "Hold existing stock if possible - prices may recover",
                            "Evaluate storage costs vs potential price recovery",
                            "Look for government support schemes"
                        ],
                        data_sources=["market_api"],
                        confidence=trend.get('confidence', 0.7),
                        expires_at=datetime.now() + timedelta(days=3),
                        created_at=datetime.now()
                    ))
            
        except Exception as e:
            print(f"Market alert generation error: {str(e)}")
        
        return alerts
    
    async def _generate_seasonal_alerts(self, user_id: str, profile, farming_context) -> List[ProactiveAlert]:
        """Generate seasonal farming reminders"""
        alerts = []
        
        try:
            current_month = datetime.now().month
            
            # Kharif season reminders (June-September)
            if current_month == 5:  # May - prepare for Kharif
                alerts.append(ProactiveAlert(
                    alert_id=f"kharif_prep_{user_id}_{datetime.now().year}",
                    user_id=user_id,
                    alert_type=AlertType.SEASONAL_REMINDER,
                    risk_level=RiskLevel.LOW,
                    title="🌾 Kharif Season Preparation",
                    message="Kharif season is approaching. Time to prepare your fields and plan crop selection.",
                    recommendations=[
                        "Prepare fields for monsoon crops",
                        "Check and repair irrigation systems",
                        "Purchase quality seeds and fertilizers",
                        "Plan crop rotation based on last year's performance"
                    ],
                    data_sources=["seasonal_calendar"],
                    confidence=0.9,
                    expires_at=datetime.now() + timedelta(days=30),
                    created_at=datetime.now()
                ))
            
            # Rabi season reminders (October-March)
            elif current_month == 9:  # September - prepare for Rabi
                alerts.append(ProactiveAlert(
                    alert_id=f"rabi_prep_{user_id}_{datetime.now().year}",
                    user_id=user_id,
                    alert_type=AlertType.SEASONAL_REMINDER,
                    risk_level=RiskLevel.LOW,
                    title="🌾 Rabi Season Preparation",
                    message="Rabi season is approaching. Time to plan winter crops and field preparation.",
                    recommendations=[
                        "Plan winter crop selection",
                        "Prepare fields after Kharif harvest",
                        "Arrange irrigation for winter crops",
                        "Check soil health and apply necessary amendments"
                    ],
                    data_sources=["seasonal_calendar"],
                    confidence=0.9,
                    expires_at=datetime.now() + timedelta(days=30),
                    created_at=datetime.now()
                ))
            
        except Exception as e:
            print(f"Seasonal alert generation error: {str(e)}")
        
        return alerts
    
    async def _weather_monitoring(self):
        """Background weather monitoring"""
        while self.monitoring_active:
            try:
                # This would run periodically to check weather conditions
                # and generate alerts for all users
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Weather monitoring error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _irrigation_monitoring(self):
        """Background irrigation monitoring"""
        while self.monitoring_active:
            try:
                # Check irrigation schedules for all users
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Irrigation monitoring error: {str(e)}")
                await asyncio.sleep(300)
    
    async def _market_monitoring(self):
        """Background market monitoring"""
        while self.monitoring_active:
            try:
                # Monitor market price changes
                await asyncio.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                print(f"Market monitoring error: {str(e)}")
                await asyncio.sleep(300)
    
    async def _seasonal_monitoring(self):
        """Background seasonal monitoring"""
        while self.monitoring_active:
            try:
                # Check for seasonal reminders
                await asyncio.sleep(86400)  # Check daily
                
            except Exception as e:
                print(f"Seasonal monitoring error: {str(e)}")
                await asyncio.sleep(3600)

# Global proactive advisory service
proactive_advisory_service = ProactiveAdvisoryService()
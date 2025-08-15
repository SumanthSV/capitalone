# services/intelligent_data_collector.py
import asyncio
from typing import Dict, List, Optional, Any
from services.intelligent_query_router import intelligent_query_router, QueryIntent
from services.contextual_memory import contextual_memory_service
from services.real_market_api import real_market_api
from services.weather import weather_service
from services.smart_irrigation import smart_irrigation_engine
from services.user_profiles import user_profile_service

class IntelligentDataCollector:
    """Collects and processes real data from multiple APIs based on query analysis"""
    
    def __init__(self):
        self.query_router = intelligent_query_router
    
    async def collect_data_for_query(self, query_analysis, user_id: str) -> Dict[str, Any]:
        """Collect all necessary real data for the query"""
        collected_data = {
            'user_context': {},
            'api_data': {},
            'processed_insights': {}
        }
        
        try:
            # Collect user context
            collected_data['user_context'] = await self._collect_user_context(user_id, query_analysis.context_needed)
            
            # Collect API data based on intent (real data only)
            collected_data['api_data'] = await self._collect_real_api_data(query_analysis, collected_data['user_context'])
            
            # Process insights from real data
            collected_data['processed_insights'] = await self._process_real_insights(query_analysis, collected_data)
            
            return collected_data
            
        except Exception as e:
            print(f"Data collection error: {str(e)}")
            return collected_data
    
    async def _collect_user_context(self, user_id: str, context_needs: List[str]) -> Dict[str, Any]:
        """Collect user context based on needs"""
        context = {}
        
        try:
            if 'user_profile' in context_needs:
                profile = user_profile_service.get_profile(user_id)
                if profile:
                    context['profile'] = {
                        'name': profile.name,
                        'location': profile.location,
                        'primary_crops': profile.primary_crops,
                        'secondary_crops': profile.secondary_crops,
                        'farm_size': profile.farm_size.value,
                        'experience': profile.experience.value,
                        'soil_type': profile.soil_type,
                        'irrigation_type': profile.irrigation_type,
                        'preferred_language': profile.preferred_language
                    }
            
            if 'farming_context' in context_needs:
                farming_context = contextual_memory_service.get_farming_context(user_id)
                if farming_context:
                    context['farming'] = {
                        'crop_stages': {k: v.value for k, v in farming_context.crop_stages.items()},
                        'last_irrigation': farming_context.last_irrigation.isoformat() if farming_context.last_irrigation else None,
                        'irrigation_frequency': farming_context.irrigation_frequency_days,
                        'planting_dates': {k: v.isoformat() for k, v in farming_context.planting_dates.items()},
                        'harvest_dates': {k: v.isoformat() for k, v in farming_context.harvest_dates.items()}
                    }
            
            if 'irrigation_history' in context_needs:
                irrigation_history = contextual_memory_service.get_irrigation_history(user_id, days=30)
                context['irrigation_history'] = [
                    {
                        'crop': h.crop_name,
                        'date': h.irrigation_date.isoformat(),
                        'amount': h.water_amount_liters,
                        'effectiveness': h.effectiveness_rating,
                        'method': h.irrigation_method
                    }
                    for h in irrigation_history[-5:]  # Last 5 irrigations
                ]
            
            return context
            
        except Exception as e:
            print(f"User context collection error: {str(e)}")
            return context
    
    async def _collect_real_api_data(self, query_analysis, user_context: Dict) -> Dict[str, Any]:
        """Collect data from external APIs - real data only"""
        api_data = {}
        
        try:
            # Determine locations to query
            locations = query_analysis.extracted_info.locations
            if not locations and user_context.get('profile', {}).get('location'):
                locations = [user_context['profile']['location']]
            
            # Determine crops to query
            crops = query_analysis.extracted_info.crops
            if not crops and user_context.get('profile', {}).get('primary_crops'):
                crops = user_context['profile']['primary_crops']
            
            # Market data collection (real data only)
            if 'market_api' in query_analysis.requires_apis and crops:
                market_data = {}
                for location in locations or ['']:
                    try:
                        prices = real_market_api.get_consolidated_prices(crops, location)
                        trends = real_market_api.get_price_trends(crops, days=30)
                        
                        if prices or trends:  # Only add if we have real data
                            market_data[location or 'general'] = {}
                            if prices:
                                market_data[location or 'general']['current_prices'] = prices
                            if trends:
                                market_data[location or 'general']['price_trends'] = trends
                            market_data[location or 'general']['last_updated'] = datetime.now().isoformat()
                    except Exception as e:
                        print(f"Market data error for {location}: {str(e)}")
                
                if market_data:  # Only add if we have real data
                    api_data['market'] = market_data
            
            # Weather data collection (real data only)
            if 'weather_api' in query_analysis.requires_apis:
                weather_data = {}
                for location in locations or ['']:
                    try:
                        current_weather = weather_service.get_current_weather(location)
                        forecast = weather_service.get_weather_forecast(location, days=7)
                        
                        if current_weather or forecast:  # Only add if we have real data
                            weather_data[location or 'general'] = {}
                            if current_weather:
                                weather_data[location or 'general']['current'] = current_weather
                                alerts = weather_service.get_agricultural_alerts(location, current_weather)
                                if alerts:
                                    weather_data[location or 'general']['alerts'] = alerts
                            if forecast:
                                weather_data[location or 'general']['forecast'] = forecast
                    except Exception as e:
                        print(f"Weather data error for {location}: {str(e)}")
                
                if weather_data:  # Only add if we have real data
                    api_data['weather'] = weather_data
            
            # Irrigation engine data (real data only)
            if 'irrigation_engine' in query_analysis.requires_apis and user_context.get('profile'):
                irrigation_data = {}
                profile = user_context['profile']
                
                # Use default coordinates (in production, geocode the location)
                lat, lon = 28.6139, 77.2090
                
                for crop in crops or profile.get('primary_crops', []):
                    try:
                        decision = smart_irrigation_engine.make_irrigation_decision(
                            user_id=user_context.get('profile', {}).get('user_id', user_id),
                            crop_name=crop,
                            latitude=lat,
                            longitude=lon
                        )
                        
                        # Only add if we have a valid decision (not UNKNOWN)
                        if decision.recommendation != smart_irrigation_engine.IrrigationRecommendation.UNKNOWN:
                            irrigation_data[crop] = {
                                'recommendation': decision.recommendation.value,
                                'confidence': decision.confidence,
                                'water_amount': decision.water_amount_liters,
                                'timing': decision.timing,
                                'reasoning': decision.reasoning,
                                'next_check_hours': decision.next_check_hours,
                                'data_availability': decision.data_availability
                            }
                    except Exception as e:
                        print(f"Irrigation decision error for {crop}: {str(e)}")
                
                if irrigation_data:  # Only add if we have real decisions
                    api_data['irrigation'] = irrigation_data
            
            return api_data
            
        except Exception as e:
            print(f"API data collection error: {str(e)}")
            return api_data
    
    async def _process_real_insights(self, query_analysis, collected_data: Dict) -> Dict[str, Any]:
        """Process collected real data into actionable insights"""
        insights = {}
        
        try:
            intent = query_analysis.intent
            api_data = collected_data.get('api_data', {})
            user_context = collected_data.get('user_context', {})
            
            # Market insights (only if we have real market data)
            if intent in [QueryIntent.MARKET_PRICE, QueryIntent.SELLING_ADVICE, QueryIntent.BUYING_ADVICE]:
                market_data = api_data.get('market', {})
                if market_data:
                    insights['market'] = self._analyze_real_market_data(market_data, intent)
            
            # Irrigation insights (only if we have real irrigation data)
            if intent == QueryIntent.IRRIGATION_ADVICE:
                irrigation_data = api_data.get('irrigation', {})
                weather_data = api_data.get('weather', {})
                irrigation_history = user_context.get('irrigation_history', [])
                
                if irrigation_data or weather_data:
                    insights['irrigation'] = self._analyze_real_irrigation_data(
                        irrigation_data, weather_data, irrigation_history
                    )
            
            # Weather insights (only if we have real weather data)
            if intent == QueryIntent.WEATHER_INQUIRY:
                weather_data = api_data.get('weather', {})
                if weather_data:
                    insights['weather'] = self._analyze_real_weather_data(weather_data)
            
            # Profit optimization insights (only with real data)
            if api_data.get('market') or api_data.get('weather'):
                insights['profit_optimization'] = self._generate_real_profit_insights(
                    query_analysis, api_data, user_context
                )
            
            return insights
            
        except Exception as e:
            print(f"Insights processing error: {str(e)}")
            return insights
    
    def _analyze_real_market_data(self, market_data: Dict, intent: QueryIntent) -> Dict[str, Any]:
        """Analyze real market data for actionable insights"""
        insights = {
            'price_comparison': {},
            'trend_analysis': {},
            'recommendations': [],
            'profit_potential': {}
        }
        
        try:
            for location, data in market_data.items():
                prices = data.get('current_prices', [])
                trends = data.get('price_trends', [])
                
                # Price comparison across locations
                for price_info in prices:
                    crop = price_info['crop']
                    if crop not in insights['price_comparison']:
                        insights['price_comparison'][crop] = []
                    
                    insights['price_comparison'][crop].append({
                        'location': location,
                        'price': price_info['price'],
                        'unit': price_info['unit'],
                        'market': price_info['market']
                    })
                
                # Trend analysis
                for trend_info in trends:
                    crop = trend_info['crop']
                    insights['trend_analysis'][crop] = {
                        'direction': trend_info['trend'],
                        'change_percent': trend_info['change_percent'],
                        'confidence': trend_info['confidence'],
                        'recommendation': trend_info['recommendation']
                    }
                    
                    # Generate specific recommendations
                    if intent == QueryIntent.SELLING_ADVICE:
                        if trend_info['trend'] == 'increasing' and trend_info['change_percent'] > 5:
                            insights['recommendations'].append(
                                f"Good time to sell {crop} - prices rising by {trend_info['change_percent']:.1f}%"
                            )
                        elif trend_info['trend'] == 'decreasing':
                            insights['recommendations'].append(
                                f"Consider holding {crop} - prices falling by {abs(trend_info['change_percent']):.1f}%"
                            )
            
            return insights
            
        except Exception as e:
            print(f"Market analysis error: {str(e)}")
            return insights
    
    def _analyze_real_irrigation_data(self, irrigation_data: Dict, weather_data: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Analyze real irrigation data for insights"""
        insights = {
            'immediate_recommendations': [],
            'timing_advice': [],
            'water_optimization': [],
            'risk_factors': []
        }
        
        try:
            for crop, decision_data in irrigation_data.items():
                recommendation = decision_data['recommendation']
                confidence = decision_data['confidence']
                water_amount = decision_data['water_amount']
                timing = decision_data['timing']
                reasoning = decision_data.get('reasoning', [])
                
                if recommendation == 'urgent':
                    insights['immediate_recommendations'].append(
                        f"🚨 URGENT: {crop} needs immediate irrigation ({water_amount:.0f}L recommended)"
                    )
                elif recommendation == 'recommended':
                    insights['timing_advice'].append(
                        f"💧 {crop} should be irrigated {timing} ({water_amount:.0f}L)"
                    )
                elif recommendation == 'not_needed':
                    insights['water_optimization'].append(
                        f"✅ {crop} has adequate moisture - save water"
                    )
                elif recommendation == 'unknown':
                    insights['risk_factors'].append(
                        f"⚠️ Cannot determine irrigation needs for {crop} - insufficient data"
                    )
                
                # Add reasoning
                insights['timing_advice'].extend([f"• {reason}" for reason in reasoning])
            
            # Analyze weather impact if available
            for location, weather_info in weather_data.items():
                current = weather_info.get('current', {})
                forecast = weather_info.get('forecast', [])
                
                if forecast:
                    # Check for upcoming rain
                    upcoming_rain = sum(day.get('rainfall', 0) for day in forecast[:3])
                    if upcoming_rain > 10:
                        insights['water_optimization'].append(
                            f"🌧️ Rain expected ({upcoming_rain:.1f}mm in 3 days) - delay irrigation"
                        )
                    
                    # Check for extreme weather
                    max_temp = max((day.get('temperature', 25) for day in forecast[:3]), default=25)
                    if max_temp > 35:
                        insights['risk_factors'].append(
                            f"🌡️ High temperatures expected ({max_temp}°C) - increase irrigation frequency"
                        )
            
            return insights
            
        except Exception as e:
            print(f"Irrigation analysis error: {str(e)}")
            return insights
    
    def _analyze_real_weather_data(self, weather_data: Dict) -> Dict[str, Any]:
        """Analyze real weather data for farming insights"""
        insights = {
            'current_conditions': {},
            'forecast_summary': {},
            'agricultural_impact': [],
            'recommendations': []
        }
        
        try:
            for location, weather_info in weather_data.items():
                current = weather_info.get('current', {})
                forecast = weather_info.get('forecast', [])
                alerts = weather_info.get('alerts', [])
                
                # Current conditions
                if current:
                    insights['current_conditions'][location] = {
                        'temperature': current.get('temperature'),
                        'humidity': current.get('humidity'),
                        'rainfall': current.get('rainfall'),
                        'description': current.get('description')
                    }
                
                # Forecast summary
                if forecast:
                    avg_temp = sum(day.get('temperature', 25) for day in forecast[:7]) / min(7, len(forecast))
                    total_rain = sum(day.get('rainfall', 0) for day in forecast[:7])
                    
                    insights['forecast_summary'][location] = {
                        'avg_temperature_7days': round(avg_temp, 1),
                        'total_rainfall_7days': round(total_rain, 1),
                        'conditions': forecast[0].get('description', 'Unknown') if forecast else 'Unknown'
                    }
                
                # Agricultural impact
                for alert in alerts:
                    insights['agricultural_impact'].append({
                        'location': location,
                        'alert_type': alert['type'],
                        'message': alert['message'],
                        'recommendations': alert.get('recommendations', [])
                    })
            
            return insights
            
        except Exception as e:
            print(f"Weather analysis error: {str(e)}")
            return insights
    
    def _generate_real_profit_insights(self, query_analysis, api_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate profit optimization insights from real data only"""
        insights = {
            'immediate_actions': [],
            'short_term_strategy': [],
            'long_term_planning': [],
            'risk_mitigation': [],
            'profit_potential': {}
        }
        
        try:
            intent = query_analysis.intent
            market_data = api_data.get('market', {})
            weather_data = api_data.get('weather', {})
            
            # Selling advice insights (only with real market data)
            if intent == QueryIntent.SELLING_ADVICE and market_data:
                for location, data in market_data.items():
                    for price_info in data.get('current_prices', []):
                        crop = price_info['crop']
                        current_price = price_info['price']
                        
                        # Get trend for this crop
                        trend_data = next(
                            (t for t in data.get('price_trends', []) if t['crop'] == crop),
                            None
                        )
                        
                        if trend_data:
                            change_percent = trend_data['change_percent']
                            
                            if change_percent > 10:
                                insights['immediate_actions'].append(
                                    f"🚀 SELL NOW: {crop} prices up {change_percent:.1f}% at ₹{current_price}/{price_info['unit']} in {location}"
                                )
                            elif change_percent > 5:
                                insights['short_term_strategy'].append(
                                    f"📈 Monitor {crop} - prices rising slowly ({change_percent:.1f}%), may increase further"
                                )
                            elif change_percent < -5:
                                insights['risk_mitigation'].append(
                                    f"⚠️ Hold {crop} - prices falling ({change_percent:.1f}%), wait for recovery"
                                )
                            
                            # Calculate profit potential if we have farm size
                            if user_context.get('profile', {}).get('farm_size'):
                                farm_size_str = user_context['profile']['farm_size']
                                farm_size = 2 if 'small' in farm_size_str else 5 if 'medium' in farm_size_str else 10
                                estimated_yield = farm_size * 20  # Rough estimate: 20 quintals per acre
                                potential_revenue = estimated_yield * current_price
                                
                                insights['profit_potential'][crop] = {
                                    'estimated_yield_quintals': estimated_yield,
                                    'current_price_per_quintal': current_price,
                                    'potential_revenue': potential_revenue,
                                    'location': location
                                }
            
            # Weather-based profit insights (only with real weather data)
            if weather_data:
                for location, weather_info in weather_data.items():
                    forecast = weather_info.get('forecast', [])
                    if forecast:
                        # Check for favorable conditions
                        upcoming_rain = sum(day.get('rainfall', 0) for day in forecast[:3])
                        if upcoming_rain > 20:
                            insights['short_term_strategy'].append(
                                f"🌧️ Heavy rain expected in {location} - good for crop growth, delay harvest if near maturity"
                            )
                        
                        # Check for adverse conditions
                        max_temp = max((day.get('temperature', 25) for day in forecast[:3]), default=25)
                        if max_temp > 38:
                            insights['risk_mitigation'].append(
                                f"🌡️ Extreme heat in {location} - protect crops, increase irrigation, consider early harvest"
                            )
            
            return insights
            
        except Exception as e:
            print(f"Profit insights error: {str(e)}")
            return insights

# Global instance
intelligent_data_collector = IntelligentDataCollector()
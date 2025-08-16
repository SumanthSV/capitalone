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
        print(f"\n=== DATA COLLECTION START ===")
        print(f"User ID: {user_id}")
        print(f"Query intent: {query_analysis.intent.value}")
        print(f"Required APIs: {query_analysis.requires_apis}")
        
        collected_data = {
            'user_context': {},
            'api_data': {},
            'processed_insights': {}
        }
        
        try:
            # Collect user context
            print(f"[INFO] Collecting user context...")
            collected_data['user_context'] = await self._collect_user_context(user_id, query_analysis.context_needed)
            print(f"[INFO] User context collected: {list(collected_data['user_context'].keys())}")
            
            # Collect API data based on intent (real data only)
            print(f"[INFO] Collecting real API data...")
            collected_data['api_data'] = await self._collect_real_api_data(query_analysis, collected_data['user_context'])
            print(f"[INFO] API data collected: {list(collected_data['api_data'].keys())}")
            
            # Process insights from real data
            print(f"[INFO] Processing insights...")
            collected_data['processed_insights'] = await self._process_real_insights(query_analysis, collected_data)
            print(f"[INFO] Insights processed: {list(collected_data['processed_insights'].keys())}")
            
            print(f"[SUCCESS] Data collection completed")
            print(f"=== DATA COLLECTION END ===\n")
            
            return collected_data
            
        except Exception as e:
            print(f"[ERROR] Data collection failed: {str(e)}")
            print(f"=== DATA COLLECTION FAILED ===\n")
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
                        'farm_size': profile.farm_size.value if hasattr(profile.farm_size, 'value') else str(profile.farm_size),
                        'experience': profile.experience.value if hasattr(profile.experience, 'value') else str(profile.experience),
                        'soil_type': profile.soil_type,
                        'irrigation_type': profile.irrigation_type,
                        'preferred_language': profile.preferred_language
                    }
                else:
                    print(f"[WARNING] No user profile found for user {user_id}")
            
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
                else:
                    print(f"[WARNING] No farming context found for user {user_id}")
            
            if 'irrigation_history' in context_needs:
                irrigation_history = contextual_memory_service.get_irrigation_history(user_id, days=30)
                if irrigation_history:
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
                else:
                    print(f"[WARNING] No irrigation history found for user {user_id}")
            
            return context
            
        except Exception as e:
            print(f"[ERROR] User context collection error: {str(e)}")
            return context
    
    async def _collect_real_api_data(self, query_analysis, user_context: Dict) -> Dict[str, Any]:
        """Collect data from external APIs - real data only"""
        api_data = {}
        
        try:
            # Determine locations to query
            locations = query_analysis.extracted_info.locations or []
            if not locations and user_context.get('profile', {}).get('location'):
                locations = [user_context['profile']['location']]
            
            # Determine crops to query
            crops = query_analysis.extracted_info.crops or []
            if not crops and user_context.get('profile', {}).get('primary_crops'):
                crops = user_context['profile']['primary_crops']
            
            print(f"[INFO] Querying for crops: {crops}, locations: {locations}")
            
            # Market data collection (real data only)
            if 'market_api' in query_analysis.requires_apis and crops:
                market_data = {}
                for location in locations or ['']:
                    try:
                        print(f"[INFO] Fetching market data for {location}...")
                        prices = real_market_api.get_consolidated_prices(crops, location)
                        trends = real_market_api.get_price_trends(crops, days=30)
                        
                        # Only add if we have real data (not None or empty)
                        if prices and len(prices) > 0:
                            # Filter out error entries
                            valid_prices = [p for p in prices if p.get('source') != 'unavailable' and p.get('price', 0) > 0]
                            if valid_prices:
                            market_data[location or 'general'] = {}
                            if prices:
                                # Filter out error entries for API response
                                valid_prices = [p for p in prices if p.get('source') != 'unavailable']
                                if valid_prices:
                                market_data[location or 'general']['current_prices'] = valid_prices
                                print(f"[SUCCESS] Added {len(valid_prices)} valid prices for {location}")
                            else:
                                print(f"[WARNING] No valid price data for {location}")
                        
                        if trends and len(trends) > 0:
                            # Filter out low-confidence trends
                            valid_trends = [t for t in trends if t.get('confidence', 0) > 0.3]
                            if valid_trends:
                                if location or 'general' not in market_data:
                                    market_data[location or 'general'] = {}
                                market_data[location or 'general']['price_trends'] = valid_trends
                                print(f"[SUCCESS] Added {len(valid_trends)} valid trends for {location}")
                        
                        if market_data.get(location or 'general'):
                            market_data[location or 'general']['last_updated'] = datetime.now().isoformat()
                        else:
                            print(f"[WARNING] No market data available for {location}")
                    except Exception as e:
                        print(f"[ERROR] Market data error for {location}: {str(e)}")
                
                if market_data:  # Only add if we have real data
                    api_data['market'] = market_data
                    print(f"[SUCCESS] Market data collected for {len(market_data)} locations")
                else:
                    print(f"[WARNING] No market data collected from any source")
            
            # Weather data collection (real data only)
            if 'weather_api' in query_analysis.requires_apis:
                weather_data = {}
                for location in locations or ['']:
                    try:
                        print(f"[INFO] Fetching weather data for {location}...")
                        current_weather = weather_service.get_current_weather(location)
                        forecast = weather_service.get_weather_forecast(location, days=7)
                        
                        # Only add if we have valid data
                        if (current_weather and isinstance(current_weather, dict) and current_weather.get('temperature')) or \
                           (forecast and isinstance(forecast, list) and len(forecast) > 0):
                            weather_data[location or 'general'] = {}
                            if current_weather:
                                weather_data[location or 'general']['current'] = current_weather
                                alerts = weather_service.get_agricultural_alerts(location, current_weather)
                                if alerts:
                                    weather_data[location or 'general']['alerts'] = alerts
                            if forecast:
                                weather_data[location or 'general']['forecast'] = forecast
                            print(f"[SUCCESS] Weather data added for {location}")
                        else:
                            print(f"[WARNING] No weather data available for {location}")
                    except Exception as e:
                        print(f"[ERROR] Weather data error for {location}: {str(e)}")
                
                if weather_data:  # Only add if we have real data
                    api_data['weather'] = weather_data
                    print(f"[SUCCESS] Weather data collected for {len(weather_data)} locations")
                else:
                    print(f"[WARNING] No weather data collected from any source")
            
            # Irrigation engine data (real data only)
            if 'irrigation_engine' in query_analysis.requires_apis and user_context.get('profile'):
                irrigation_data = {}
                profile = user_context['profile']
                
                # Use default coordinates (in production, geocode the location)
                lat, lon = 28.6139, 77.2090
                
                for crop in crops or profile.get('primary_crops', []):
                    try:
                        print(f"[INFO] Getting irrigation decision for {crop}...")
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
                            print(f"[SUCCESS] Irrigation decision for {crop}: {decision.recommendation.value}")
                        else:
                            print(f"[WARNING] Insufficient data for irrigation decision on {crop}")
                    except Exception as e:
                        print(f"[ERROR] Irrigation decision error for {crop}: {str(e)}")
                
                if irrigation_data:  # Only add if we have real decisions
                    api_data['irrigation'] = irrigation_data
                    print(f"[SUCCESS] Irrigation data collected for {len(irrigation_data)} crops")
                else:
                    print(f"[WARNING] No irrigation data collected")
            
            return api_data
            
        except Exception as e:
            print(f"[ERROR] API data collection error: {str(e)}")
            return api_data
    
    async def _process_real_insights(self, query_analysis, collected_data: Dict) -> Dict[str, Any]:
        """Process collected real data into actionable insights"""
        insights = {}
        
        try:
            intent = query_analysis.intent
            api_data = collected_data.get('api_data', {}) or {}
            user_context = collected_data.get('user_context', {}) or {}
            
            # Market insights (only if we have real market data)
            if intent in [QueryIntent.MARKET_PRICE, QueryIntent.SELLING_ADVICE, QueryIntent.BUYING_ADVICE]:
                market_data = api_data.get('market', {})
                if market_data:
                    insights['market'] = self._analyze_real_market_data(market_data, intent)
                else:
                    print(f"[WARNING] No market data available for insights")
                    insights['market'] = {
                        'price_comparison': {},
                        'trend_analysis': {},
                        'recommendations': ["Market data not available - check API configuration"],
                        'profit_potential': {}
                    }
            
            # Irrigation insights (only if we have real irrigation data)
            if intent == QueryIntent.IRRIGATION_ADVICE:
                irrigation_data = api_data.get('irrigation', {})
                weather_data = api_data.get('weather', {})
                irrigation_history = user_context.get('irrigation_history', [])
                
                if irrigation_data or weather_data:
                    insights['irrigation'] = self._analyze_real_irrigation_data(
                        irrigation_data, weather_data, irrigation_history
                    )
                else:
                    print(f"[WARNING] No irrigation or weather data available for insights")
                    insights['irrigation'] = {
                        'immediate_recommendations': ["Irrigation data not available - check sensors and weather API"],
                        'timing_advice': [],
                        'water_optimization': [],
                        'risk_factors': ["Unable to assess irrigation needs without real-time data"]
                    }
            
            # Weather insights (only if we have real weather data)
            if intent == QueryIntent.WEATHER_INQUIRY:
                weather_data = api_data.get('weather', {})
                if weather_data:
                    insights['weather'] = self._analyze_real_weather_data(weather_data)
                else:
                    print(f"[WARNING] No weather data available for insights")
                    insights['weather'] = {
                        'current_conditions': {},
                        'forecast_summary': {},
                        'agricultural_impact': [],
                        'recommendations': ["Weather data not available - check API configuration"]
                    }
            
            # Profit optimization insights (only with real data)
            if api_data.get('market') or api_data.get('weather'):
                insights['profit_optimization'] = self._generate_real_profit_insights(
                    query_analysis, api_data, user_context
                )
            else:
                insights['profit_optimization'] = {
                    'immediate_actions': [],
                    'short_term_strategy': [],
                    'long_term_planning': [],
                    'risk_mitigation': ["Limited data available for profit optimization"],
                    'profit_potential': {}
                }
            
            return insights
            
        except Exception as e:
            print(f"[ERROR] Insights processing error: {str(e)}")
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
            if not market_data:
                return insights
                
            for location, data in market_data.items():
                prices = data.get('current_prices', []) or []
                trends = data.get('price_trends', []) or []
                
                # Price comparison across locations
                for price_info in prices:
                    if not price_info or not isinstance(price_info, dict):
                        continue
                        
                    crop = price_info.get('crop', 'Unknown')
                    if crop not in insights['price_comparison']:
                        insights['price_comparison'][crop] = []
                    
                    insights['price_comparison'][crop].append({
                        'location': location,
                        'price': price_info.get('price', 0),
                        'unit': price_info.get('unit', 'quintal'),
                        'market': price_info.get('market', 'Unknown')
                    })
                
                # Trend analysis
                for trend_info in trends:
                    if not trend_info or not isinstance(trend_info, dict):
                        continue
                        
                    crop = trend_info.get('crop', 'Unknown')
                    insights['trend_analysis'][crop] = {
                        'direction': trend_info.get('trend', 'stable'),
                        'change_percent': trend_info.get('change_percent', 0),
                        'confidence': trend_info.get('confidence', 0.5),
                        'recommendation': trend_info.get('recommendation', 'Monitor prices')
                    }
                    
                    # Generate specific recommendations
                    if intent == QueryIntent.SELLING_ADVICE:
                        change_percent = trend_info.get('change_percent', 0)
                        if trend_info.get('trend') == 'increasing' and change_percent > 5:
                            insights['recommendations'].append(
                                f"Good time to sell {crop} - prices rising by {change_percent:.1f}%"
                            )
                        elif trend_info.get('trend') == 'decreasing':
                            insights['recommendations'].append(
                                f"Consider holding {crop} - prices falling by {abs(change_percent):.1f}%"
                            )
            
            # Add fallback recommendations if none generated
            if not insights['recommendations']:
                if intent == QueryIntent.MARKET_PRICE:
                    insights['recommendations'].append("Check local mandi prices for most current rates")
                elif intent == QueryIntent.SELLING_ADVICE:
                    insights['recommendations'].append("Monitor price trends before making selling decisions")
                elif intent == QueryIntent.BUYING_ADVICE:
                    insights['recommendations'].append("Compare prices across different markets")
            
            return insights
            
        except Exception as e:
            print(f"[ERROR] Market analysis error: {str(e)}")
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
            # Process irrigation data
            for crop, decision_data in (irrigation_data or {}).items():
                if not decision_data or not isinstance(decision_data, dict):
                    continue
                    
                recommendation = decision_data.get('recommendation', 'unknown')
                confidence = decision_data.get('confidence', 0.5)
                water_amount = decision_data.get('water_amount', 0)
                timing = decision_data.get('timing', 'unknown')
                reasoning = decision_data.get('reasoning', []) or []
                
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
                for reason in reasoning:
                    if reason and isinstance(reason, str):
                        insights['timing_advice'].append(f"• {reason}")
            
            # Analyze weather impact if available
            for location, weather_info in (weather_data or {}).items():
                if not weather_info or not isinstance(weather_info, dict):
                    continue
                    
                current = weather_info.get('current', {}) or {}
                forecast = weather_info.get('forecast', []) or []
                
                if forecast:
                    # Check for upcoming rain
                    upcoming_rain = sum(day.get('rainfall', 0) for day in forecast[:3] if isinstance(day, dict))
                    if upcoming_rain > 10:
                        insights['water_optimization'].append(
                            f"🌧️ Rain expected ({upcoming_rain:.1f}mm in 3 days) - delay irrigation"
                        )
                    
                    # Check for extreme weather
                    max_temp = max((day.get('temperature', 25) for day in forecast[:3] if isinstance(day, dict)), default=25)
                    if max_temp > 35:
                        insights['risk_factors'].append(
                            f"🌡️ High temperatures expected ({max_temp}°C) - increase irrigation frequency"
                        )
            
            # Add fallback recommendations if none generated
            if not any([insights['immediate_recommendations'], insights['timing_advice'], 
                       insights['water_optimization']]):
                insights['timing_advice'].append("Check soil moisture manually and observe plant stress signs")
            
            return insights
            
        except Exception as e:
            print(f"[ERROR] Irrigation analysis error: {str(e)}")
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
            if not weather_data:
                return insights
                
            for location, weather_info in weather_data.items():
                if not weather_info or not isinstance(weather_info, dict):
                    continue
                    
                current = weather_info.get('current', {}) or {}
                forecast = weather_info.get('forecast', []) or []
                alerts = weather_info.get('alerts', []) or []
                
                # Current conditions
                if current:
                    insights['current_conditions'][location] = {
                        'temperature': current.get('temperature'),
                        'humidity': current.get('humidity'),
                        'rainfall': current.get('rainfall'),
                        'description': current.get('description')
                    }
                
                # Forecast summary
                if forecast and len(forecast) > 0:
                    valid_forecasts = [day for day in forecast if isinstance(day, dict) and day.get('temperature')]
                    if valid_forecasts:
                        avg_temp = sum(day.get('temperature', 25) for day in valid_forecasts[:7]) / min(7, len(valid_forecasts))
                        total_rain = sum(day.get('rainfall', 0) for day in valid_forecasts[:7])
                        
                        insights['forecast_summary'][location] = {
                            'avg_temperature_7days': round(avg_temp, 1),
                            'total_rainfall_7days': round(total_rain, 1),
                            'conditions': valid_forecasts[0].get('description', 'Unknown') if valid_forecasts else 'Unknown'
                        }
                
                # Agricultural impact
                for alert in alerts:
                    if alert and isinstance(alert, dict):
                        insights['agricultural_impact'].append({
                            'location': location,
                            'alert_type': alert.get('type', 'unknown'),
                            'message': alert.get('message', ''),
                            'recommendations': alert.get('recommendations', []) or []
                        })
            
            return insights
            
        except Exception as e:
            print(f"[ERROR] Weather analysis error: {str(e)}")
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
            market_data = api_data.get('market', {}) or {}
            weather_data = api_data.get('weather', {}) or {}
            
            # Selling advice insights (only with real market data)
            if intent == QueryIntent.SELLING_ADVICE and market_data:
                for location, data in market_data.items():
                    if not data or not isinstance(data, dict):
                        continue
                        
                    current_prices = data.get('current_prices', []) or []
                    price_trends = data.get('price_trends', []) or []
                    
                    for price_info in current_prices:
                        if not price_info or not isinstance(price_info, dict):
                            continue
                            
                        crop = price_info.get('crop', 'Unknown')
                        current_price = price_info.get('price', 0)
                        
                        # Get trend for this crop
                        trend_data = None
                        for trend in price_trends:
                            if isinstance(trend, dict) and trend.get('crop') == crop:
                                trend_data = trend
                                break
                        
                        if trend_data:
                            change_percent = trend_data.get('change_percent', 0)
                            
                            if change_percent > 10:
                                insights['immediate_actions'].append(
                                    f"🚀 SELL NOW: {crop} prices up {change_percent:.1f}% at ₹{current_price}/{price_info.get('unit', 'quintal')} in {location}"
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
                            profile = user_context.get('profile', {})
                            if profile and profile.get('farm_size'):
                                farm_size_str = str(profile.get('farm_size', 'medium'))
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
                    if not weather_info or not isinstance(weather_info, dict):
                        continue
                        
                    forecast = weather_info.get('forecast', []) or []
                    if forecast:
                        # Check for favorable conditions
                        valid_forecasts = [day for day in forecast if isinstance(day, dict)]
                        upcoming_rain = sum(day.get('rainfall', 0) for day in valid_forecasts[:3])
                        if upcoming_rain > 20:
                            insights['short_term_strategy'].append(
                                f"🌧️ Heavy rain expected in {location} - good for crop growth, delay harvest if near maturity"
                            )
                        
                        # Check for adverse conditions
                        max_temp = max((day.get('temperature', 25) for day in valid_forecasts[:3]), default=25)
                        if max_temp > 38:
                            insights['risk_mitigation'].append(
                                f"🌡️ Extreme heat in {location} - protect crops, increase irrigation, consider early harvest"
                            )
            
            return insights
            
        except Exception as e:
            print(f"[ERROR] Profit insights error: {str(e)}")
            return insights

# Global instance
intelligent_data_collector = IntelligentDataCollector()
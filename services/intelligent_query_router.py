# services/intelligent_query_router.py
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from services.enhanced_gemini import enhanced_gemini
from services.contextual_memory import contextual_memory_service
from services.real_market_api import real_market_api
from services.weather import weather_service
from services.smart_irrigation import smart_irrigation_engine
from services.user_profiles import user_profile_service
from services.translation import detect_language, translate_text
from services.offline_cache import offline_cache

class QueryIntent(Enum):
    MARKET_PRICE = "market_price"
    IRRIGATION_ADVICE = "irrigation_advice"
    WEATHER_INQUIRY = "weather_inquiry"
    DISEASE_DIAGNOSIS = "disease_diagnosis"
    CROP_RECOMMENDATION = "crop_recommendation"
    SELLING_ADVICE = "selling_advice"
    BUYING_ADVICE = "buying_advice"
    GENERAL_FARMING = "general_farming"
    FERTILIZER_ADVICE = "fertilizer_advice"
    HARVEST_TIMING = "harvest_timing"

@dataclass
class ExtractedInfo:
    crops: List[str]
    locations: List[str]
    time_references: List[str]
    quantities: List[str]
    actions: List[str]
    conditions: List[str]

@dataclass
class QueryAnalysis:
    intent: QueryIntent
    confidence: float
    extracted_info: ExtractedInfo
    requires_apis: List[str]
    context_needed: List[str]
    language: str
    original_query: str

class IntelligentQueryRouter:
    """Intelligent query router that understands farmer intent and routes to appropriate services"""
    
    def __init__(self):
        # Location patterns for Indian states and cities
        self.location_patterns = {
            'states': ['punjab', 'haryana', 'uttar pradesh', 'bihar', 'west bengal', 'maharashtra', 
                      'gujarat', 'rajasthan', 'madhya pradesh', 'karnataka', 'tamil nadu', 'andhra pradesh',
                      'telangana', 'kerala', 'odisha', 'jharkhand', 'chhattisgarh', 'assam'],
            'cities': ['delhi', 'mumbai', 'kolkata', 'chennai', 'bangalore', 'hyderabad', 'pune', 
                      'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'bhopal'],
            'markets': ['mandi', 'market', 'bazaar', 'apmc']
        }
        
        # Crop name variations and aliases
        self.crop_aliases = {
            'rice': ['rice', 'paddy', 'chawal', 'dhan'],
            'wheat': ['wheat', 'gehun', 'gahu'],
            'cotton': ['cotton', 'kapas', 'karpas'],
            'sugarcane': ['sugarcane', 'ganna', 'sugar cane'],
            'maize': ['maize', 'corn', 'makka', 'bhutta'],
            'tomato': ['tomato', 'tamatar'],
            'potato': ['potato', 'aloo', 'batata'],
            'onion': ['onion', 'pyaz', 'kanda'],
            'soybean': ['soybean', 'soya', 'soy']
        }
        
        # Intent patterns with keywords
        self.intent_patterns = {
            QueryIntent.MARKET_PRICE: [
                'price', 'rate', 'cost', 'mandi', 'market', 'bhav', 'kimat', 'daam',
                'how much', 'kitna', 'kitne mein', 'price list', 'current price'
            ],
            QueryIntent.SELLING_ADVICE: [
                'sell', 'bech', 'bechna', 'sale', 'when to sell', 'kab bechna',
                'profit', 'munafa', 'good time to sell', 'market timing'
            ],
            QueryIntent.BUYING_ADVICE: [
                'buy', 'kharid', 'kharidna', 'purchase', 'when to buy', 'kab kharidna',
                'seeds', 'beej', 'fertilizer', 'khad'
            ],
            QueryIntent.IRRIGATION_ADVICE: [
                'irrigate', 'irrigation', 'water', 'pani', 'sinchai', 'watering',
                'should i water', 'pani dena', 'when to water', 'kab pani'
            ],
            QueryIntent.WEATHER_INQUIRY: [
                'weather', 'mausam', 'rain', 'barish', 'temperature', 'tapman',
                'forecast', 'climate', 'humidity', 'wind'
            ],
            QueryIntent.DISEASE_DIAGNOSIS: [
                'disease', 'bimari', 'rog', 'pest', 'keet', 'infection', 'sankraman',
                'spots', 'yellowing', 'wilting', 'treatment', 'ilaj'
            ],
            QueryIntent.CROP_RECOMMENDATION: [
                'crop', 'fasal', 'plant', 'ugana', 'grow', 'cultivation', 'kheti',
                'what to grow', 'kya ugayen', 'which crop', 'kaun si fasal'
            ],
            QueryIntent.FERTILIZER_ADVICE: [
                'fertilizer', 'khad', 'manure', 'compost', 'nutrients', 'poshan',
                'npk', 'urea', 'when to apply', 'kab dalen'
            ],
            QueryIntent.HARVEST_TIMING: [
                'harvest', 'katai', 'cutting', 'ready', 'mature', 'pakna',
                'when to harvest', 'kab kate', 'harvest time'
            ]
        }
        
        # API mapping for each intent
        self.api_requirements = {
            QueryIntent.MARKET_PRICE: ['market_api'],
            QueryIntent.SELLING_ADVICE: ['market_api', 'weather_api'],
            QueryIntent.BUYING_ADVICE: ['market_api'],
            QueryIntent.IRRIGATION_ADVICE: ['weather_api', 'soil_moisture_api', 'irrigation_engine'],
            QueryIntent.WEATHER_INQUIRY: ['weather_api'],
            QueryIntent.DISEASE_DIAGNOSIS: ['disease_detection', 'weather_api'],
            QueryIntent.CROP_RECOMMENDATION: ['weather_api', 'soil_api', 'market_api'],
            QueryIntent.FERTILIZER_ADVICE: ['soil_api', 'crop_stage_api'],
            QueryIntent.HARVEST_TIMING: ['weather_api', 'market_api', 'crop_stage_api']
        }
    
    def analyze_query(self, query: str, user_id: str = None) -> QueryAnalysis:
        """Analyze user query to understand intent and extract information"""
        try:
            # Detect language
            detected_lang = detect_language(query)
            original_query = query
            
            # Translate to English for processing if needed
            if detected_lang != 'en':
                query_en = translate_text(query, detected_lang, 'en')
            else:
                query_en = query
            
            # Extract information
            extracted_info = self._extract_information(query_en)
            
            # Determine intent
            intent, confidence = self._determine_intent(query_en, extracted_info)
            
            # Determine required APIs and context
            required_apis = self.api_requirements.get(intent, [])
            context_needed = self._determine_context_needs(intent, extracted_info)
            
            return QueryAnalysis(
                intent=intent,
                confidence=confidence,
                extracted_info=extracted_info,
                requires_apis=required_apis,
                context_needed=context_needed,
                language=detected_lang,
                original_query=original_query
            )
            
        except Exception as e:
            print(f"Query analysis error: {str(e)}")
            return self._create_fallback_analysis(query)
    
    def _extract_information(self, query: str) -> ExtractedInfo:
        """Extract structured information from query"""
        query_lower = query.lower()
        
        # Extract crops
        crops = []
        for standard_crop, aliases in self.crop_aliases.items():
            for alias in aliases:
                if alias in query_lower:
                    crops.append(standard_crop)
                    break
        
        # Extract locations
        locations = []
        for location_type, location_list in self.location_patterns.items():
            for location in location_list:
                if location in query_lower:
                    locations.append(location.title())
        
        # Extract time references
        time_patterns = [
            r'\b(today|tomorrow|yesterday)\b',
            r'\b(this|next|last)\s+(week|month|year|season)\b',
            r'\b(\d+)\s+(days?|weeks?|months?)\b',
            r'\b(morning|evening|afternoon|night)\b',
            r'\b(now|currently|presently)\b'
        ]
        
        time_references = []
        for pattern in time_patterns:
            matches = re.findall(pattern, query_lower)
            time_references.extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        # Extract quantities
        quantity_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(kg|quintal|ton|acre|hectare|liter|ml)\b',
            r'\b(\d+(?:\.\d+)?)\s*(rupees?|rs\.?|₹)\b'
        ]
        
        quantities = []
        for pattern in quantity_patterns:
            matches = re.findall(pattern, query_lower)
            quantities.extend([f"{match[0]} {match[1]}" for match in matches])
        
        # Extract actions
        action_keywords = [
            'sell', 'buy', 'plant', 'harvest', 'irrigate', 'spray', 'fertilize',
            'treat', 'cure', 'prevent', 'apply', 'remove', 'cut', 'prune'
        ]
        
        actions = [action for action in action_keywords if action in query_lower]
        
        # Extract conditions
        condition_keywords = [
            'diseased', 'healthy', 'dry', 'wet', 'hot', 'cold', 'sunny', 'cloudy',
            'ready', 'mature', 'young', 'fresh', 'rotten', 'damaged'
        ]
        
        conditions = [condition for condition in condition_keywords if condition in query_lower]
        
        return ExtractedInfo(
            crops=crops,
            locations=locations,
            time_references=time_references,
            quantities=quantities,
            actions=actions,
            conditions=conditions
        )
    
    def _determine_intent(self, query: str, extracted_info: ExtractedInfo) -> Tuple[QueryIntent, float]:
        """Determine the primary intent of the query"""
        query_lower = query.lower()
        intent_scores = {}
        
        # Score each intent based on keyword matches
        for intent, keywords in self.intent_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Exact phrase match gets higher score
                    if keyword in query_lower.split():
                        score += 2
                    else:
                        score += 1
            
            # Boost score based on extracted information
            if intent == QueryIntent.MARKET_PRICE and extracted_info.locations:
                score += 3
            if intent == QueryIntent.SELLING_ADVICE and 'sell' in extracted_info.actions:
                score += 3
            if intent == QueryIntent.IRRIGATION_ADVICE and any(time in extracted_info.time_references for time in ['now', 'today']):
                score += 2
            
            if score > 0:
                intent_scores[intent] = score / len(keywords)  # Normalize
        
        if not intent_scores:
            return QueryIntent.GENERAL_FARMING, 0.5
        
        # Get highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(0.95, intent_scores[best_intent])
        
        return best_intent, confidence
    
    def _determine_context_needs(self, intent: QueryIntent, extracted_info: ExtractedInfo) -> List[str]:
        """Determine what context information is needed"""
        context_needs = []
        
        # Always need user profile for personalization
        context_needs.append('user_profile')
        
        if intent in [QueryIntent.IRRIGATION_ADVICE, QueryIntent.SELLING_ADVICE, QueryIntent.HARVEST_TIMING]:
            context_needs.extend(['farming_context', 'irrigation_history'])
        
        if intent in [QueryIntent.MARKET_PRICE, QueryIntent.SELLING_ADVICE, QueryIntent.BUYING_ADVICE]:
            context_needs.append('market_preferences')
        
        if intent == QueryIntent.DISEASE_DIAGNOSIS:
            context_needs.append('disease_history')
        
        # If no specific location mentioned, need user's location
        if not extracted_info.locations:
            context_needs.append('user_location')
        
        # If no specific crops mentioned, need user's crops
        if not extracted_info.crops:
            context_needs.append('user_crops')
        
        return context_needs
    
    def _create_fallback_analysis(self, query: str) -> QueryAnalysis:
        """Create fallback analysis when processing fails"""
        return QueryAnalysis(
            intent=QueryIntent.GENERAL_FARMING,
            confidence=0.3,
            extracted_info=ExtractedInfo([], [], [], [], [], []),
            requires_apis=['general'],
            context_needed=['user_profile'],
            language='en',
            original_query=query
        )

class IntelligentDataCollector:
    """Collects and processes data from multiple APIs based on query analysis"""
    
    def __init__(self):
        self.query_router = IntelligentQueryRouter()
    
    async def collect_data_for_query(self, query_analysis: QueryAnalysis, user_id: str) -> Dict[str, Any]:
        """Collect all necessary data for the query"""
        collected_data = {
            'user_context': {},
            'api_data': {},
            'processed_insights': {}
        }
        
        try:
            # Collect user context
            collected_data['user_context'] = await self._collect_user_context(user_id, query_analysis.context_needed)
            
            # Collect API data based on intent
            collected_data['api_data'] = await self._collect_api_data(query_analysis, collected_data['user_context'])
            
            # Process insights
            collected_data['processed_insights'] = await self._process_insights(query_analysis, collected_data)
            
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
                        'effectiveness': h.effectiveness_rating
                    }
                    for h in irrigation_history[-5:]  # Last 5 irrigations
                ]
            
            return context
            
        except Exception as e:
            print(f"User context collection error: {str(e)}")
            return context
    
    async def _collect_api_data(self, query_analysis: QueryAnalysis, user_context: Dict) -> Dict[str, Any]:
        """Collect data from external APIs"""
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
            
            # Market data collection
            if 'market_api' in query_analysis.requires_apis and crops:
                market_data = {}
                for location in locations or ['']:
                    try:
                        prices = real_market_api.get_consolidated_prices(crops, location)
                        trends = real_market_api.get_price_trends(crops, days=30)
                        
                        market_data[location or 'general'] = {
                            'current_prices': prices,
                            'price_trends': trends,
                            'last_updated': datetime.now().isoformat()
                        }
                    except Exception as e:
                        print(f"Market data error for {location}: {str(e)}")
                
                api_data['market'] = market_data
            
            # Weather data collection
            if 'weather_api' in query_analysis.requires_apis:
                weather_data = {}
                for location in locations or ['']:
                    try:
                        current_weather = weather_service.get_current_weather(location)
                        forecast = weather_service.get_weather_forecast(location, days=7)
                        alerts = weather_service.get_agricultural_alerts(location, current_weather)
                        
                        weather_data[location or 'general'] = {
                            'current': current_weather,
                            'forecast': forecast,
                            'alerts': alerts
                        }
                    except Exception as e:
                        print(f"Weather data error for {location}: {str(e)}")
                
                api_data['weather'] = weather_data
            
            # Irrigation engine data
            if 'irrigation_engine' in query_analysis.requires_apis and user_context.get('profile'):
                irrigation_data = {}
                profile = user_context['profile']
                
                # Use default coordinates (in production, geocode the location)
                lat, lon = 28.6139, 77.2090
                
                for crop in crops or profile.get('primary_crops', []):
                    try:
                        decision = smart_irrigation_engine.make_irrigation_decision(
                            user_id=user_context.get('profile', {}).get('user_id', 'anonymous'),
                            crop_name=crop,
                            latitude=lat,
                            longitude=lon
                        )
                        
                        irrigation_data[crop] = {
                            'recommendation': decision.recommendation.value,
                            'confidence': decision.confidence,
                            'water_amount': decision.water_amount_liters,
                            'timing': decision.timing,
                            'reasoning': decision.reasoning,
                            'next_check_hours': decision.next_check_hours
                        }
                    except Exception as e:
                        print(f"Irrigation decision error for {crop}: {str(e)}")
                
                api_data['irrigation'] = irrigation_data
            
            return api_data
            
        except Exception as e:
            print(f"API data collection error: {str(e)}")
            return api_data
    
    async def _process_insights(self, query_analysis: QueryAnalysis, collected_data: Dict) -> Dict[str, Any]:
        """Process collected data into actionable insights"""
        insights = {}
        
        try:
            intent = query_analysis.intent
            api_data = collected_data.get('api_data', {})
            user_context = collected_data.get('user_context', {})
            
            # Market insights
            if intent in [QueryIntent.MARKET_PRICE, QueryIntent.SELLING_ADVICE, QueryIntent.BUYING_ADVICE]:
                insights['market'] = self._analyze_market_data(api_data.get('market', {}), intent)
            
            # Irrigation insights
            if intent == QueryIntent.IRRIGATION_ADVICE:
                insights['irrigation'] = self._analyze_irrigation_data(
                    api_data.get('irrigation', {}),
                    api_data.get('weather', {}),
                    user_context.get('irrigation_history', [])
                )
            
            # Weather insights
            if intent == QueryIntent.WEATHER_INQUIRY:
                insights['weather'] = self._analyze_weather_data(api_data.get('weather', {}))
            
            # Profit optimization insights
            insights['profit_optimization'] = self._generate_profit_insights(
                query_analysis, api_data, user_context
            )
            
            return insights
            
        except Exception as e:
            print(f"Insights processing error: {str(e)}")
            return insights
    
    def _analyze_market_data(self, market_data: Dict, intent: QueryIntent) -> Dict[str, Any]:
        """Analyze market data for actionable insights"""
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
                    
                    elif intent == QueryIntent.BUYING_ADVICE:
                        if trend_info['trend'] == 'decreasing' and trend_info['change_percent'] < -5:
                            insights['recommendations'].append(
                                f"Good time to buy {crop} inputs - prices down by {abs(trend_info['change_percent']):.1f}%"
                            )
            
            # Find best prices across locations
            for crop, price_list in insights['price_comparison'].items():
                if len(price_list) > 1:
                    sorted_prices = sorted(price_list, key=lambda x: x['price'], reverse=True)
                    highest = sorted_prices[0]
                    lowest = sorted_prices[-1]
                    
                    if highest['price'] > lowest['price'] * 1.1:  # 10% difference
                        insights['recommendations'].append(
                            f"Price difference for {crop}: {highest['location']} (₹{highest['price']}) vs {lowest['location']} (₹{lowest['price']})"
                        )
            
            return insights
            
        except Exception as e:
            print(f"Market analysis error: {str(e)}")
            return insights
    
    def _analyze_irrigation_data(self, irrigation_data: Dict, weather_data: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Analyze irrigation data for insights"""
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
                
                # Add reasoning
                insights['timing_advice'].extend([f"• {reason}" for reason in reasoning])
            
            # Analyze weather impact
            for location, weather_info in weather_data.items():
                current = weather_info.get('current', {})
                forecast = weather_info.get('forecast', [])
                
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
    
    def _analyze_weather_data(self, weather_data: Dict) -> Dict[str, Any]:
        """Analyze weather data for farming insights"""
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
    
    def _generate_profit_insights(self, query_analysis: QueryAnalysis, api_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate profit optimization insights"""
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
            
            # Selling advice insights
            if intent == QueryIntent.SELLING_ADVICE:
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
                            
                            # Calculate profit potential
                            if user_context.get('profile', {}).get('farm_size'):
                                farm_size = float(user_context['profile']['farm_size'].replace('small', '2').replace('medium', '5').replace('large', '10'))
                                estimated_yield = farm_size * 20  # Rough estimate: 20 quintals per acre
                                potential_revenue = estimated_yield * current_price
                                
                                insights['profit_potential'][crop] = {
                                    'estimated_yield_quintals': estimated_yield,
                                    'current_price_per_quintal': current_price,
                                    'potential_revenue': potential_revenue,
                                    'location': location
                                }
            
            # Weather-based profit insights
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

# Global instances
intelligent_query_router = IntelligentQueryRouter()
intelligent_data_collector = IntelligentDataCollector()
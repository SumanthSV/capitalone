"""
Enhanced Data Service - Robust real-time data fetching with intelligent fallbacks
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from services.offline_cache import offline_cache
from services.enhanced_gemini import enhanced_gemini

class EnhancedDataService:
    """Enhanced data service with robust error handling and intelligent fallbacks"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.weather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.enam_api_key = os.getenv("ENAM_API_KEY")
        
        # Backup data sources
        self.backup_sources = {
            'market': [
                'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070',  # Alternative market API
                'https://agmarknet.gov.in'  # Direct AgMarkNet
            ],
            'weather': [
                'https://api.openweathermap.org/data/2.5',  # Primary
                'https://api.weatherapi.com/v1'  # Backup weather service
            ]
        }
        
        self.cache_duration = {
            'market': 2,  # 2 hours for market data
            'weather': 1,  # 1 hour for weather data
            'crop_info': 24  # 24 hours for crop information
        }
    
    async def get_comprehensive_data(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """Get comprehensive data for any agricultural query"""
        print(f"\n=== ENHANCED DATA SERVICE START ===")
        print(f"Query: {query}")
        print(f"User context available: {bool(user_context)}")
        
        try:
            # Analyze what data is needed
            data_needs = self._analyze_data_requirements(query, user_context)
            print(f"[INFO] Data needs identified: {data_needs}")
            
            # Collect all required data
            collected_data = {}
            
            # Market data
            if 'market' in data_needs:
                market_data = await self._get_robust_market_data(data_needs['market'])
                if market_data:
                    collected_data['market'] = market_data
                    print(f"[SUCCESS] Market data collected")
                else:
                    print(f"[WARNING] No market data available")
            
            # Weather data
            if 'weather' in data_needs:
                weather_data = await self._get_robust_weather_data(data_needs['weather'])
                if weather_data:
                    collected_data['weather'] = weather_data
                    print(f"[SUCCESS] Weather data collected")
                else:
                    print(f"[WARNING] No weather data available")
            
            # Crop information
            if 'crop_info' in data_needs:
                crop_data = await self._get_crop_information(data_needs['crop_info'])
                if crop_data:
                    collected_data['crop_info'] = crop_data
                    print(f"[SUCCESS] Crop information collected")
            
            # Generate intelligent response using available data
            response = await self._generate_intelligent_response(query, collected_data, user_context)
            
            print(f"[SUCCESS] Enhanced data service completed")
            print(f"=== ENHANCED DATA SERVICE END ===\n")
            
            return {
                'success': True,
                'response': response,
                'data_sources': list(collected_data.keys()),
                'data_availability': {k: bool(v) for k, v in collected_data.items()},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Enhanced data service failed: {str(e)}")
            print(f"=== ENHANCED DATA SERVICE FAILED ===\n")
            
            # Generate fallback response
            fallback_response = await self._generate_fallback_response(query, user_context)
            
            return {
                'success': False,
                'response': fallback_response,
                'error': str(e),
                'data_sources': [],
                'data_availability': {},
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_data_requirements(self, query: str, user_context: Dict = None) -> Dict[str, Any]:
        """Analyze what data is needed for the query"""
        query_lower = query.lower()
        data_needs = {}
        
        # Market data needs
        if any(keyword in query_lower for keyword in ['price', 'sell', 'profit', 'market', 'rate', 'cost']):
            crops = self._extract_crops_from_query(query)
            location = self._extract_location_from_query(query, user_context)
            data_needs['market'] = {
                'crops': crops or ['rice', 'wheat'],  # Default crops
                'location': location or 'india'
            }
        
        # Weather data needs
        if any(keyword in query_lower for keyword in ['weather', 'rain', 'irrigate', 'water', 'temperature']):
            location = self._extract_location_from_query(query, user_context)
            data_needs['weather'] = {
                'location': location or 'delhi',  # Default location
                'forecast_days': 7
            }
        
        # Crop information needs
        if any(keyword in query_lower for keyword in ['crop', 'grow', 'plant', 'cultivation', 'farming']):
            crops = self._extract_crops_from_query(query)
            data_needs['crop_info'] = {
                'crops': crops or ['rice', 'wheat']
            }
        
        return data_needs
    
    def _extract_crops_from_query(self, query: str) -> List[str]:
        """Extract crop names from query"""
        crop_keywords = {
            'rice': ['rice', 'paddy', 'chawal', 'dhan'],
            'wheat': ['wheat', 'gehun', 'gahu'],
            'cotton': ['cotton', 'kapas'],
            'sugarcane': ['sugarcane', 'ganna'],
            'maize': ['maize', 'corn', 'makka'],
            'tomato': ['tomato', 'tamatar'],
            'potato': ['potato', 'aloo'],
            'onion': ['onion', 'pyaz']
        }
        
        found_crops = []
        query_lower = query.lower()
        
        for crop, keywords in crop_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                found_crops.append(crop)
        
        return found_crops
    
    def _extract_location_from_query(self, query: str, user_context: Dict = None) -> Optional[str]:
        """Extract location from query or user context"""
        # Try to get from user context first
        if user_context and user_context.get('profile', {}).get('location'):
            return user_context['profile']['location']
        
        # Extract from query
        locations = ['punjab', 'haryana', 'karnataka', 'maharashtra', 'gujarat', 'rajasthan', 
                    'uttar pradesh', 'bihar', 'west bengal', 'tamil nadu', 'andhra pradesh']
        
        query_lower = query.lower()
        for location in locations:
            if location in query_lower:
                return location.title()
        
        return None
    
    async def _get_robust_market_data(self, market_needs: Dict) -> Optional[Dict[str, Any]]:
        """Get market data with multiple fallback strategies"""
        try:
            crops = market_needs.get('crops', [])
            location = market_needs.get('location', '')
            
            # Try cache first
            cache_key = f"robust_market_{'-'.join(crops)}_{location}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                print(f"[INFO] Using cached market data")
                return cached_data
            
            # Strategy 1: Use Gemini to get current market information
            if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
                market_data = await self._get_gemini_market_data(crops, location)
                if market_data:
                    offline_cache.set(cache_key, market_data, self.cache_duration['market'])
                    return market_data
            
            # Strategy 2: Use government data APIs
            gov_data = await self._get_government_market_data(crops, location)
            if gov_data:
                offline_cache.set(cache_key, gov_data, self.cache_duration['market'])
                return gov_data
            
            # Strategy 3: Use historical patterns and estimates
            estimated_data = await self._get_estimated_market_data(crops, location)
            if estimated_data:
                return estimated_data
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Robust market data error: {str(e)}")
            return None
    
    async def _get_gemini_market_data(self, crops: List[str], location: str) -> Optional[Dict[str, Any]]:
        """Use Gemini to get current market information"""
        try:
            prompt = f"""
You are an agricultural market data expert. Provide current market price information for the following:

Crops: {', '.join(crops)}
Location: {location}
Date: {datetime.now().strftime('%Y-%m-%d')}

Please provide realistic market prices in Indian Rupees per quintal for these crops in the specified location. 
Base your response on typical market patterns and seasonal variations.

Format your response as JSON:
{{
    "crops": [
        {{
            "name": "crop_name",
            "price_per_quintal": price_number,
            "price_trend": "increasing/decreasing/stable",
            "market_location": "location_name",
            "quality_grade": "standard/premium",
            "last_updated": "2025-08-16"
        }}
    ],
    "market_summary": "Brief market analysis",
    "data_source": "market_analysis",
    "confidence": 0.8
}}

Provide realistic prices based on current agricultural market conditions in India.
"""
            
            response = enhanced_gemini.get_text_response(prompt, temperature=0.3)
            
            # Try to parse JSON response
            try:
                # Clean the response
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1]
                
                market_data = json.loads(response.strip())
                
                # Validate the data structure
                if 'crops' in market_data and isinstance(market_data['crops'], list):
                    print(f"[SUCCESS] Gemini provided market data for {len(market_data['crops'])} crops")
                    return market_data
                
            except json.JSONDecodeError:
                print(f"[WARNING] Could not parse Gemini market response as JSON")
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Gemini market data error: {str(e)}")
            return None
    
    async def _get_government_market_data(self, crops: List[str], location: str) -> Optional[Dict[str, Any]]:
        """Try alternative government data sources"""
        try:
            # Try alternative data.gov.in endpoints
            alternative_endpoints = [
                "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
            ]
            
            for endpoint in alternative_endpoints:
                try:
                    params = {
                        "api-key": self.enam_api_key or "579b464db66ec23bdd000001fb43738564a441034e3dec2b2761e012",
                        "format": "json",
                        "limit": 50
                    }
                    
                    response = requests.get(endpoint, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('records'):
                            processed_data = self._process_government_data(data['records'], crops)
                            if processed_data:
                                return processed_data
                
                except Exception as e:
                    print(f"[WARNING] Government endpoint {endpoint} failed: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Government market data error: {str(e)}")
            return None
    
    async def _get_estimated_market_data(self, crops: List[str], location: str) -> Dict[str, Any]:
        """Generate estimated market data based on historical patterns"""
        try:
            # Base prices for common crops (realistic estimates)
            base_prices = {
                'rice': 2800,
                'wheat': 2200,
                'cotton': 6500,
                'sugarcane': 350,
                'maize': 1800,
                'tomato': 2500,
                'potato': 1200,
                'onion': 1800,
                'soybean': 4200
            }
            
            # Location multipliers
            location_multipliers = {
                'punjab': 1.1,
                'haryana': 1.05,
                'karnataka': 0.95,
                'maharashtra': 1.0,
                'gujarat': 1.02,
                'rajasthan': 0.98,
                'uttar pradesh': 0.92,
                'bihar': 0.88,
                'west bengal': 0.90
            }
            
            # Seasonal adjustments
            current_month = datetime.now().month
            seasonal_adjustments = {
                'rice': 1.1 if current_month in [10, 11, 12] else 0.95,  # Higher during harvest
                'wheat': 1.15 if current_month in [4, 5, 6] else 0.9,
                'cotton': 1.2 if current_month in [11, 12, 1] else 0.85
            }
            
            estimated_crops = []
            location_multiplier = location_multipliers.get(location.lower() if location else '', 1.0)
            
            for crop in crops:
                base_price = base_prices.get(crop.lower(), 2000)
                seasonal_adj = seasonal_adjustments.get(crop.lower(), 1.0)
                
                # Add some realistic variation
                import random
                variation = random.uniform(0.9, 1.1)
                
                final_price = base_price * location_multiplier * seasonal_adj * variation
                
                estimated_crops.append({
                    "name": crop,
                    "price_per_quintal": round(final_price, 0),
                    "price_trend": random.choice(["increasing", "stable", "decreasing"]),
                    "market_location": location or "General",
                    "quality_grade": "standard",
                    "last_updated": datetime.now().strftime('%Y-%m-%d'),
                    "data_type": "estimated"
                })
            
            return {
                "crops": estimated_crops,
                "market_summary": f"Estimated prices for {location or 'India'} based on seasonal patterns",
                "data_source": "historical_estimation",
                "confidence": 0.6,
                "note": "Estimated prices - check local mandi for accurate rates"
            }
            
        except Exception as e:
            print(f"[ERROR] Estimated market data error: {str(e)}")
            return None
    
    async def _get_robust_weather_data(self, weather_needs: Dict) -> Optional[Dict[str, Any]]:
        """Get weather data with fallback strategies"""
        try:
            location = weather_needs.get('location', 'delhi')
            
            # Try cache first
            cache_key = f"robust_weather_{location}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Strategy 1: OpenWeather API
            if self.weather_api_key and self.weather_api_key != "your_openweather_api_key_here":
                weather_data = await self._get_openweather_data(location)
                if weather_data:
                    offline_cache.set(cache_key, weather_data, self.cache_duration['weather'])
                    return weather_data
            
            # Strategy 2: Use Gemini for weather analysis
            if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
                weather_data = await self._get_gemini_weather_data(location)
                if weather_data:
                    return weather_data
            
            # Strategy 3: Generate seasonal weather estimates
            estimated_weather = await self._get_estimated_weather_data(location)
            return estimated_weather
            
        except Exception as e:
            print(f"[ERROR] Robust weather data error: {str(e)}")
            return None
    
    async def _get_openweather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Get data from OpenWeather API"""
        try:
            base_url = "http://api.openweathermap.org/data/2.5"
            
            # Current weather
            current_response = requests.get(
                f"{base_url}/weather",
                params={
                    "q": location,
                    "appid": self.weather_api_key,
                    "units": "metric"
                },
                timeout=10
            )
            
            if current_response.status_code == 200:
                current_data = current_response.json()
                
                # Forecast
                forecast_response = requests.get(
                    f"{base_url}/forecast",
                    params={
                        "q": location,
                        "appid": self.weather_api_key,
                        "units": "metric",
                        "cnt": 40
                    },
                    timeout=10
                )
                
                forecast_data = []
                if forecast_response.status_code == 200:
                    forecast_json = forecast_response.json()
                    for item in forecast_json.get('list', [])[:7]:  # Next 7 forecasts
                        forecast_data.append({
                            "date": datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d'),
                            "temperature": item['main']['temp'],
                            "humidity": item['main']['humidity'],
                            "rainfall": item.get('rain', {}).get('3h', 0),
                            "description": item['weather'][0]['description']
                        })
                
                return {
                    "current": {
                        "temperature": current_data['main']['temp'],
                        "humidity": current_data['main']['humidity'],
                        "description": current_data['weather'][0]['description'],
                        "wind_speed": current_data['wind']['speed']
                    },
                    "forecast": forecast_data,
                    "location": location,
                    "data_source": "openweather",
                    "timestamp": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] OpenWeather API error: {str(e)}")
            return None
    
    async def _get_gemini_weather_data(self, location: str) -> Optional[Dict[str, Any]]:
        """Use Gemini to provide weather analysis"""
        try:
            prompt = f"""
Provide current weather information and 7-day forecast for {location}, India.

Based on typical weather patterns for this location and season (August 2025), provide realistic weather data.

Format as JSON:
{{
    "current": {{
        "temperature": temperature_in_celsius,
        "humidity": humidity_percentage,
        "description": "weather_description",
        "wind_speed": wind_speed_mps
    }},
    "forecast": [
        {{
            "date": "2025-08-16",
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall_mm,
            "description": "weather_description"
        }}
    ],
    "agricultural_advice": "Brief advice for farmers based on weather",
    "data_source": "weather_analysis",
    "confidence": 0.7
}}

Provide realistic weather data for agricultural planning.
"""
            
            response = enhanced_gemini.get_text_response(prompt, temperature=0.3)
            
            # Parse JSON response
            try:
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                
                weather_data = json.loads(response.strip())
                
                if 'current' in weather_data and 'forecast' in weather_data:
                    print(f"[SUCCESS] Gemini provided weather data for {location}")
                    return weather_data
                
            except json.JSONDecodeError:
                print(f"[WARNING] Could not parse Gemini weather response")
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Gemini weather data error: {str(e)}")
            return None
    
    async def _get_estimated_weather_data(self, location: str) -> Dict[str, Any]:
        """Generate estimated weather data based on seasonal patterns"""
        try:
            # Seasonal weather patterns for India
            current_month = datetime.now().month
            
            # August weather patterns
            if current_month == 8:
                base_temp = 28
                base_humidity = 75
                base_rainfall = 15
                description = "Monsoon season"
            else:
                base_temp = 25
                base_humidity = 60
                base_rainfall = 5
                description = "Variable conditions"
            
            # Generate current weather
            import random
            current_weather = {
                "temperature": base_temp + random.uniform(-5, 5),
                "humidity": base_humidity + random.uniform(-15, 15),
                "description": description,
                "wind_speed": 3 + random.uniform(0, 7)
            }
            
            # Generate 7-day forecast
            forecast = []
            for i in range(7):
                date = datetime.now() + timedelta(days=i)
                forecast.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "temperature": base_temp + random.uniform(-8, 8),
                    "humidity": base_humidity + random.uniform(-20, 20),
                    "rainfall": base_rainfall + random.uniform(0, 25),
                    "description": random.choice([description, "Partly cloudy", "Clear sky"])
                })
            
            return {
                "current": current_weather,
                "forecast": forecast,
                "location": location,
                "data_source": "seasonal_estimation",
                "confidence": 0.5,
                "note": "Estimated weather based on seasonal patterns"
            }
            
        except Exception as e:
            print(f"[ERROR] Estimated weather data error: {str(e)}")
            return None
    
    async def _get_crop_information(self, crop_needs: Dict) -> Optional[Dict[str, Any]]:
        """Get comprehensive crop information"""
        try:
            crops = crop_needs.get('crops', [])
            
            # Use local database first
            from database.db import get_connection
            
            crop_info = {}
            conn = get_connection()
            
            for crop in crops:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM crops WHERE name LIKE ? LIMIT 1",
                    (f"%{crop}%",)
                )
                result = cursor.fetchone()
                
                if result:
                    crop_info[crop] = {
                        "name": result['name'],
                        "scientific_name": result['sci_name'],
                        "temperature_range": f"{result['temp_min']}-{result['temp_max']}°C",
                        "rainfall_range": f"{result['rainfall_min']}-{result['rainfall_max']}mm",
                        "soil_ph_range": f"{result['soil_ph_min']}-{result['soil_ph_max']}",
                        "season": result['season'],
                        "special_requirements": result['special_requirements']
                    }
            
            conn.close()
            
            if crop_info:
                return {
                    "crops": crop_info,
                    "data_source": "local_database",
                    "confidence": 0.9
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Crop information error: {str(e)}")
            return None
    
    async def _generate_intelligent_response(self, query: str, collected_data: Dict, user_context: Dict = None) -> str:
        """Generate intelligent response using available data"""
        try:
            # Build context for Gemini
            context_parts = [
                f"FARMER'S QUESTION: {query}",
                f"QUERY TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            # Add user context if available
            if user_context and user_context.get('profile'):
                profile = user_context['profile']
                context_parts.append(f"""
FARMER'S PROFILE:
- Location: {profile.get('location', 'Unknown')}
- Primary Crops: {', '.join(profile.get('primary_crops', []))}
- Farm Size: {profile.get('farm_size', 'Unknown')} acres
- Experience: {profile.get('experience', 'Unknown')}
- Soil Type: {profile.get('soil_type', 'Unknown')}
""")
            
            # Add available data
            if collected_data.get('market'):
                market_data = collected_data['market']
                context_parts.append(f"""
MARKET DATA AVAILABLE:
{json.dumps(market_data, indent=2)}
""")
            
            if collected_data.get('weather'):
                weather_data = collected_data['weather']
                context_parts.append(f"""
WEATHER DATA AVAILABLE:
{json.dumps(weather_data, indent=2)}
""")
            
            if collected_data.get('crop_info'):
                crop_data = collected_data['crop_info']
                context_parts.append(f"""
CROP INFORMATION AVAILABLE:
{json.dumps(crop_data, indent=2)}
""")
            
            # Add data availability transparency
            available_sources = list(collected_data.keys())
            unavailable_sources = []
            
            if 'market' not in available_sources:
                unavailable_sources.append("real-time market prices")
            if 'weather' not in available_sources:
                unavailable_sources.append("current weather data")
            
            if unavailable_sources:
                context_parts.append(f"""
DATA LIMITATIONS:
- Not available: {', '.join(unavailable_sources)}
- Please mention these limitations in your response
""")
            
            # Generate response
            full_prompt = "\n".join(context_parts) + f"""

INSTRUCTIONS:
1. Provide specific, actionable advice for this farmer
2. Use the available data to give concrete recommendations
3. If data is limited, clearly state what information is missing
4. Focus on profit optimization and practical steps
5. Be honest about data limitations
6. Provide alternative approaches when real-time data is unavailable
7. Give specific numbers and calculations where possible
8. Respond in a conversational, helpful tone

Generate a comprehensive response that helps the farmer make informed decisions.
"""
            
            response = enhanced_gemini.get_text_response(full_prompt, temperature=0.4)
            return response
            
        except Exception as e:
            print(f"[ERROR] Response generation error: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again or rephrase your question."
    
    async def _generate_fallback_response(self, query: str, user_context: Dict = None) -> str:
        """Generate fallback response when all data sources fail"""
        try:
            fallback_prompt = f"""
The farmer asked: "{query}"

You are an experienced agricultural advisor. Even without real-time data, provide helpful general guidance based on:
1. General agricultural knowledge
2. Seasonal farming patterns in India
3. Common best practices
4. Risk management strategies

Be honest that you don't have current market/weather data, but still provide valuable advice.
Focus on actionable steps the farmer can take.

Respond in a helpful, conversational tone.
"""
            
            response = enhanced_gemini.get_text_response(fallback_prompt, temperature=0.5)
            
            # Add disclaimer
            disclaimer = "\n\n⚠️ Note: I don't have access to current market and weather data right now. Please check local sources for the most up-to-date information."
            
            return response + disclaimer
            
        except Exception as e:
            print(f"[ERROR] Fallback response error: {str(e)}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again later or consult with a local agricultural expert."
    
    def _process_government_data(self, records: List[Dict], target_crops: List[str]) -> Optional[Dict[str, Any]]:
        """Process government API data"""
        try:
            processed_crops = []
            
            for record in records:
                commodity = record.get('Commodity', '').lower()
                modal_price = record.get('Modal_Price', '0')
                
                # Check if this record matches our target crops
                for crop in target_crops:
                    if crop.lower() in commodity or commodity in crop.lower():
                        try:
                            price = float(modal_price) if modal_price and modal_price != '-' else 0
                            if price > 0:
                                processed_crops.append({
                                    "name": crop,
                                    "price_per_quintal": price,
                                    "market_location": record.get('Market', 'Unknown'),
                                    "variety": record.get('Variety', 'Standard'),
                                    "date": record.get('Arrival_Date', datetime.now().strftime('%Y-%m-%d')),
                                    "data_source": "government_api"
                                })
                        except ValueError:
                            continue
            
            if processed_crops:
                return {
                    "crops": processed_crops,
                    "data_source": "government_api",
                    "confidence": 0.8
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Government data processing error: {str(e)}")
            return None

# Global enhanced data service
enhanced_data_service = EnhancedDataService()
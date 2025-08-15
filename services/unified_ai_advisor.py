# services/unified_ai_advisor.py
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.intelligent_query_router import intelligent_query_router, intelligent_data_collector, QueryIntent
from services.enhanced_gemini import enhanced_gemini
from services.translation import translate_text, detect_language
from services.contextual_memory import contextual_memory_service
from services.offline_cache import offline_cache

class UnifiedAIAdvisor:
    """Unified AI advisor that provides ChatGPT-like experience for agriculture"""
    
    def __init__(self):
        self.conversation_cache_hours = 24
        self.max_context_length = 4000
        self.active_queries = set()  # Track active queries to prevent concurrent processing
    
    async def process_unified_query(self, user_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process unified query with intelligent routing and human-like response"""
        try:
            # Check if user already has an active query
            if user_id in self.active_queries:
                return {
                    'success': False,
                    'error': 'Please wait for your previous query to complete before asking another question.'
                }
            
            # Mark user as having active query
            self.active_queries.add(user_id)
            
            try:
                # Extract primary text query
                text_query = inputs.get('text', '').strip()
                image_path = inputs.get('image_path')
                voice_data = inputs.get('voice_data')
                sensor_data = inputs.get('sensor_data')
                location_override = inputs.get('location')
                language_override = inputs.get('language')
                
                if not text_query and not image_path:
                    return {
                        'success': False,
                        'error': 'Please provide a text query or upload an image'
                    }
                
                # Detect language and translate if needed
                original_language = 'en'
                original_query = text_query
                
                if text_query:
                    original_language = detect_language(text_query)
                    if original_language != 'en':
                        text_query = translate_text(text_query, original_language, 'en')
                
                # Analyze the query to understand intent
                query_analysis = intelligent_query_router.analyze_query(text_query, user_id)
                
                # Override location if specified in query
                if location_override:
                    query_analysis.extracted_info.locations = [location_override]
                
                # Collect all necessary data (real data only)
                collected_data = await intelligent_data_collector.collect_data_for_query(query_analysis, user_id)
                
                # Process image if provided
                image_analysis = None
                if image_path:
                    image_analysis = await self._process_image_input(image_path)
                    collected_data['image_analysis'] = image_analysis
                
                # Generate personalized, human-like response
                response = await self._generate_personalized_response(
                    query_analysis, collected_data, user_id, original_query, original_language
                )
                
                # Store conversation memory for future context
                if user_id != 'anonymous':
                    await self._store_conversation_memory(user_id, query_analysis, collected_data, response, original_query)
                
                # Determine response language
                response_language = language_override or original_language
                
                # Translate response if needed
                if response_language != 'en' and response_language != original_language:
                    try:
                        response['main_response'] = translate_text(response['main_response'], 'en', response_language)
                        if response.get('recommendations'):
                            response['recommendations'] = [
                                translate_text(rec, 'en', response_language) for rec in response['recommendations']
                            ]
                    except Exception as e:
                        print(f"Translation error: {str(e)}")
                elif original_language != 'en':
                    # Translate back to original language
                    try:
                        response['main_response'] = translate_text(response['main_response'], 'en', original_language)
                        if response.get('recommendations'):
                            response['recommendations'] = [
                                translate_text(rec, 'en', original_language) for rec in response['recommendations']
                            ]
                    except Exception as e:
                        print(f"Translation error: {str(e)}")
                
                return {
                    'success': True,
                    'response': response['main_response'],
                    'recommendations': response.get('recommendations', []),
                    'data_sources': response.get('data_sources', []),
                    'confidence_score': response.get('confidence_score', 0.7),
                    'intent_detected': query_analysis.intent.value,
                    'apis_called': query_analysis.requires_apis,
                    'context_applied': bool(collected_data.get('user_context')),
                    'data_availability': response.get('data_availability', {}),
                    'follow_up_suggestions': response.get('follow_up_suggestions', [])
                }
                
            finally:
                # Always remove user from active queries
                self.active_queries.discard(user_id)
            
        except Exception as e:
            self.active_queries.discard(user_id)
            print(f"Unified query processing error: {str(e)}")
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}',
                'fallback_response': 'I apologize, but I encountered an error. Please try rephrasing your question or contact support.'
            }
    
    async def _process_image_input(self, image_path: str) -> Dict[str, Any]:
        """Process image input for disease detection"""
        try:
            # Use enhanced Gemini for image analysis
            analysis = enhanced_gemini.analyze_image(image_path)
            
            if analysis.get('error'):
                return {
                    'crop_detected': 'Unknown',
                    'disease_detected': 'Analysis failed',
                    'confidence': 'Low',
                    'treatment': 'Unable to analyze image. Please try with a clearer image.',
                    'error': analysis['error']
                }
            
            return {
                'crop_detected': analysis.get('crop', 'Unknown'),
                'disease_detected': analysis.get('disease', 'Unknown'),
                'confidence': analysis.get('confidence', 'Medium'),
                'treatment': analysis.get('organic_treatment', ''),
                'prevention': analysis.get('prevention', ''),
                'severity': analysis.get('severity', 'Unknown'),
                'symptoms': analysis.get('symptoms_observed', []),
                'recommended_actions': analysis.get('recommended_actions', [])
            }
            
        except Exception as e:
            print(f"Image processing error: {str(e)}")
            return {
                'crop_detected': 'Unknown',
                'disease_detected': 'Analysis failed',
                'confidence': 'Low',
                'treatment': 'Unable to analyze image. Please try with a clearer image.',
                'error': str(e)
            }
    
    async def _generate_personalized_response(self, query_analysis, collected_data: Dict, 
                                            user_id: str, original_query: str, original_language: str) -> Dict[str, Any]:
        """Generate deeply personalized response using collected data"""
        try:
            # Build comprehensive context for LLM
            context_prompt = self._build_personalized_context_prompt(
                query_analysis, collected_data, original_query, original_language
            )
            
            # Generate response using Gemini
            ai_response = enhanced_gemini.get_text_response(context_prompt, temperature=0.4)
            
            # Extract recommendations and data sources
            recommendations = self._extract_actionable_recommendations(collected_data)
            data_sources = self._extract_data_sources(collected_data)
            follow_up_suggestions = self._generate_contextual_follow_ups(query_analysis, collected_data)
            
            # Calculate confidence score
            confidence_score = self._calculate_response_confidence(query_analysis, collected_data)
            
            # Track data availability
            data_availability = self._track_data_availability(collected_data)
            
            return {
                'main_response': ai_response,
                'recommendations': recommendations,
                'data_sources': data_sources,
                'confidence_score': confidence_score,
                'data_availability': data_availability,
                'follow_up_suggestions': follow_up_suggestions
            }
            
        except Exception as e:
            print(f"Response generation error: {str(e)}")
            return {
                'main_response': 'I apologize, but I encountered an error generating your response. Please try again.',
                'recommendations': [],
                'data_sources': [],
                'confidence_score': 0.3,
                'data_availability': {},
                'follow_up_suggestions': []
            }
    
    def _build_personalized_context_prompt(self, query_analysis, collected_data: Dict, 
                                         original_query: str, original_language: str) -> str:
        """Build deeply personalized context prompt for LLM"""
        prompt_parts = []
        
        # Enhanced system instruction
        prompt_parts.append(f"""You are KrishiMitra, a highly personalized AI agricultural advisor. You are having a one-on-one conversation with a farmer who trusts you completely.

CRITICAL GUIDELINES:
1. Respond as if you know this farmer personally and understand their specific situation
2. Always provide specific, actionable advice with exact numbers, quantities, and timing
3. Focus on maximizing the farmer's profit and efficiency
4. Use conversational, warm tone like a trusted local expert
5. Reference the farmer's specific crops, location, and farming history when relevant
6. If you don't have real-time data, clearly state "I don't have current [data type] to give you accurate advice"
7. Never use generic advice - everything should be tailored to this specific farmer
8. Explain WHY you're recommending something, not just WHAT to do
9. Always consider the farmer's experience level and adjust complexity accordingly
10. Respond in the same language the farmer used: {original_language}""")
        
        # Farmer's personal context
        user_context = collected_data.get('user_context', {})
        if user_context.get('profile'):
            profile = user_context['profile']
            prompt_parts.append(f"""
YOUR FARMER'S PROFILE:
- Name: {profile.get('name', 'Farmer')} from {profile.get('location', 'Unknown location')}
- Primary Crops: {', '.join(profile.get('primary_crops', []))}
- Farm Size: {profile.get('farm_size', 'Unknown')} acres
- Experience Level: {profile.get('experience', 'Unknown')}
- Soil Type: {profile.get('soil_type', 'Unknown')}
- Irrigation Method: {profile.get('irrigation_type', 'Unknown')}
- Preferred Language: {profile.get('preferred_language', 'Unknown')}""")
        
        # Current farming status
        if user_context.get('farming'):
            farming = user_context['farming']
            prompt_parts.append(f"""
CURRENT FARMING STATUS:
- Last Irrigation: {farming.get('last_irrigation', 'Unknown')}
- Irrigation Frequency: Every {farming.get('irrigation_frequency', 'Unknown')} days
- Current Crop Stages: {json.dumps(farming.get('crop_stages', {}), indent=2)}
- Planting Dates: {json.dumps(farming.get('planting_dates', {}), indent=2)}""")
        
        # Recent conversation history for context
        if user_context.get('irrigation_history'):
            recent_irrigations = user_context['irrigation_history'][-3:]  # Last 3 irrigations
            prompt_parts.append(f"""
RECENT IRRIGATION HISTORY:
{json.dumps(recent_irrigations, indent=2)}""")
        
        # Original farmer's question
        prompt_parts.append(f"""
FARMER'S QUESTION: "{original_query}"
DETECTED INTENT: {query_analysis.intent.value}
LANGUAGE: {original_language}""")
        
        # Real-time data availability and content
        api_data = collected_data.get('api_data', {})
        data_available = []
        data_unavailable = []
        
        # Weather data
        if api_data.get('weather'):
            data_available.append("Real-time weather data")
            prompt_parts.append("\nREAL-TIME WEATHER DATA:")
            for location, weather_info in api_data['weather'].items():
                current = weather_info.get('current', {})
                forecast = weather_info.get('forecast', [])
                
                prompt_parts.append(f"\n{location.upper()} WEATHER:")
                prompt_parts.append(f"- Current: {current.get('temperature', 'N/A')}°C, {current.get('humidity', 'N/A')}% humidity")
                prompt_parts.append(f"- Conditions: {current.get('description', 'N/A')}")
                prompt_parts.append(f"- Wind: {current.get('wind_speed', 'N/A')} m/s")
                
                if forecast:
                    upcoming_rain = sum(day.get('rainfall', 0) for day in forecast[:3])
                    prompt_parts.append(f"- Next 3 days rainfall: {upcoming_rain:.1f}mm")
        else:
            data_unavailable.append("weather data")
        
        # Market data
        if api_data.get('market'):
            data_available.append("Real-time market prices")
            prompt_parts.append("\nREAL-TIME MARKET DATA:")
            for location, market_info in api_data['market'].items():
                prompt_parts.append(f"\n{location.upper()} MARKET:")
                for price in market_info.get('current_prices', []):
                    prompt_parts.append(f"- {price['crop']}: ₹{price['price']}/{price['unit']} at {price['market']}")
                
                for trend in market_info.get('price_trends', []):
                    direction = "📈" if trend['trend'] == 'increasing' else "📉" if trend['trend'] == 'decreasing' else "➡️"
                    prompt_parts.append(f"- {trend['crop']} trend: {direction} {trend['change_percent']:+.1f}% ({trend['recommendation']})")
        else:
            data_unavailable.append("market prices")
        
        # Irrigation analysis
        if api_data.get('irrigation'):
            data_available.append("Soil moisture and irrigation analysis")
            prompt_parts.append("\nIRRIGATION ANALYSIS:")
            for crop, irrigation_info in api_data['irrigation'].items():
                prompt_parts.append(f"- {crop}: {irrigation_info['recommendation']} ({irrigation_info['water_amount']:.0f}L recommended)")
                for reason in irrigation_info.get('reasoning', []):
                    prompt_parts.append(f"  • {reason}")
                
                # Data availability for irrigation
                data_avail = irrigation_info.get('data_availability', {})
                missing_irrigation_data = [k for k, v in data_avail.items() if not v]
                if missing_irrigation_data:
                    prompt_parts.append(f"  • Missing data: {', '.join(missing_irrigation_data)}")
        else:
            data_unavailable.append("soil moisture data")
        
        # Image analysis
        if collected_data.get('image_analysis'):
            img_analysis = collected_data['image_analysis']
            if not img_analysis.get('error'):
                data_available.append("Image analysis")
                prompt_parts.append(f"""
IMAGE ANALYSIS RESULTS:
- Crop Detected: {img_analysis['crop_detected']}
- Disease/Condition: {img_analysis['disease_detected']}
- Confidence: {img_analysis['confidence']}
- Treatment Needed: {img_analysis['treatment']}""")
            else:
                data_unavailable.append("image analysis")
        
        # Data availability summary
        if data_available:
            prompt_parts.append(f"\nDATA AVAILABLE: {', '.join(data_available)}")
        if data_unavailable:
            prompt_parts.append(f"\nDATA UNAVAILABLE: {', '.join(data_unavailable)}")
        
        # Enhanced response instructions
        prompt_parts.append(f"""
RESPONSE REQUIREMENTS:
1. Address the farmer by referencing their specific situation (crops, location, farm details)
2. If you have real-time data, provide specific actionable advice with numbers and timing
3. If data is unavailable, clearly state "I don't have current [data type] to give you accurate advice right now"
4. Focus on profit optimization - always consider financial impact of your advice
5. Use warm, conversational tone as if you're a trusted local agricultural expert
6. Reference their farming history and previous conversations when relevant
7. Provide step-by-step guidance they can follow immediately
8. Explain the reasoning behind your recommendations
9. Consider their experience level: {user_context.get('profile', {}).get('experience', 'unknown')}
10. Respond in {original_language} language

REMEMBER: You are their personal agricultural advisor who knows their farm intimately. Make them feel like this advice is crafted specifically for them.""")
        
        return "\n".join(prompt_parts)
    
    def _extract_actionable_recommendations(self, collected_data: Dict) -> List[str]:
        """Extract specific, actionable recommendations"""
        recommendations = []
        
        try:
            insights = collected_data.get('processed_insights', {})
            
            # Irrigation recommendations (most actionable)
            irrigation_insights = insights.get('irrigation', {})
            recommendations.extend(irrigation_insights.get('immediate_recommendations', []))
            recommendations.extend(irrigation_insights.get('timing_advice', []))
            
            # Market recommendations (profit-focused)
            market_insights = insights.get('market', {})
            recommendations.extend(market_insights.get('recommendations', []))
            
            # Profit optimization (highest priority)
            profit_insights = insights.get('profit_optimization', {})
            recommendations.extend(profit_insights.get('immediate_actions', []))
            
            # Weather-based recommendations
            weather_insights = insights.get('weather', {})
            for impact in weather_insights.get('agricultural_impact', []):
                recommendations.extend(impact.get('recommendations', []))
            
            return recommendations[:6]  # Limit to top 6 most actionable recommendations
            
        except Exception as e:
            print(f"Recommendation extraction error: {str(e)}")
            return []
    
    def _extract_data_sources(self, collected_data: Dict) -> List[str]:
        """Extract data sources used in the response"""
        sources = []
        
        api_data = collected_data.get('api_data', {})
        
        if api_data.get('market'):
            sources.append('Real-time Market Prices')
        if api_data.get('weather'):
            sources.append('Weather Forecast API')
        if api_data.get('irrigation'):
            sources.append('Soil Moisture & Irrigation Analysis')
        if collected_data.get('image_analysis') and not collected_data['image_analysis'].get('error'):
            sources.append('AI Image Analysis')
        if collected_data.get('user_context'):
            sources.append('Your Personal Farming Profile')
        
        return sources
    
    def _generate_contextual_follow_ups(self, query_analysis, collected_data: Dict) -> List[str]:
        """Generate intelligent follow-up suggestions based on context"""
        suggestions = []
        
        try:
            intent = query_analysis.intent
            user_context = collected_data.get('user_context', {})
            
            if intent == QueryIntent.IRRIGATION_ADVICE:
                suggestions.extend([
                    "Would you like me to set up irrigation reminders based on weather?",
                    "Should I track your irrigation effectiveness over time?",
                    "Do you want advice on optimizing your irrigation method?"
                ])
            
            elif intent == QueryIntent.MARKET_PRICE:
                suggestions.extend([
                    "Would you like me to notify you when prices reach your target?",
                    "Should I analyze the best time to sell based on trends?",
                    "Do you want to compare prices across different markets?"
                ])
            
            elif intent == QueryIntent.SELLING_ADVICE:
                suggestions.extend([
                    "Would you like a detailed profit analysis for your harvest?",
                    "Should I track market trends and alert you of opportunities?",
                    "Do you need advice on post-harvest handling to maximize value?"
                ])
            
            # Add context-specific suggestions
            if user_context.get('profile', {}).get('primary_crops'):
                crops = user_context['profile']['primary_crops']
                suggestions.append(f"Ask me about specific advice for your {', '.join(crops)} crops")
            
            return suggestions[:3]  # Limit to 3 suggestions
            
        except Exception as e:
            print(f"Follow-up generation error: {str(e)}")
            return []
    
    def _calculate_response_confidence(self, query_analysis, collected_data: Dict) -> float:
        """Calculate overall response confidence based on data availability"""
        try:
            base_confidence = query_analysis.confidence
            
            # Boost confidence based on available real data
            data_boost = 0
            api_data = collected_data.get('api_data', {})
            
            if api_data.get('market'):
                data_boost += 0.15
            if api_data.get('weather'):
                data_boost += 0.15
            if api_data.get('irrigation'):
                data_boost += 0.15
            if collected_data.get('user_context', {}).get('profile'):
                data_boost += 0.20  # Personal context is very valuable
            if collected_data.get('image_analysis') and not collected_data['image_analysis'].get('error'):
                data_boost += 0.10
            
            return min(0.95, base_confidence + data_boost)
            
        except Exception as e:
            print(f"Confidence calculation error: {str(e)}")
            return 0.5
    
    def _track_data_availability(self, collected_data: Dict) -> Dict[str, bool]:
        """Track what data was available for transparency"""
        api_data = collected_data.get('api_data', {})
        
        return {
            'weather_data': bool(api_data.get('weather')),
            'market_data': bool(api_data.get('market')),
            'soil_moisture': bool(api_data.get('irrigation')),
            'user_profile': bool(collected_data.get('user_context', {}).get('profile')),
            'farming_context': bool(collected_data.get('user_context', {}).get('farming')),
            'image_analysis': bool(collected_data.get('image_analysis') and not collected_data['image_analysis'].get('error')),
            'irrigation_history': bool(collected_data.get('user_context', {}).get('irrigation_history'))
        }
    
    async def _store_conversation_memory(self, user_id: str, query_analysis, collected_data: Dict, 
                                       response: Dict, original_query: str):
        """Store conversation in memory for future personalization"""
        try:
            # Determine topic
            topic = query_analysis.intent.value
            
            # Extract key information for future context
            context_data = {
                'intent': query_analysis.intent.value,
                'confidence': query_analysis.confidence,
                'extracted_info': {
                    'crops': query_analysis.extracted_info.crops,
                    'locations': query_analysis.extracted_info.locations,
                    'actions': query_analysis.extracted_info.actions,
                    'time_references': query_analysis.extracted_info.time_references
                },
                'apis_used': query_analysis.requires_apis,
                'data_sources': response.get('data_sources', []),
                'recommendations_given': response.get('recommendations', []),
                'data_availability': response.get('data_availability', {}),
                'response_confidence': response.get('confidence_score', 0.5)
            }
            
            # Create conversation memory
            contextual_memory_service.create_conversation_memory(
                user_id=user_id,
                topic=topic,
                query=original_query,
                response=response['main_response'],
                context_data=context_data
            )
            
        except Exception as e:
            print(f"Memory storage error: {str(e)}")

# Global unified AI advisor
unified_ai_advisor = UnifiedAIAdvisor()
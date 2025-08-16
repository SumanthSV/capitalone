# services/unified_ai_advisor.py
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from services.intelligent_query_router import intelligent_query_router, intelligent_data_collector, QueryIntent
from services.enhanced_gemini import enhanced_gemini
from services.translation import translate_text, detect_language
from services.contextual_memory import contextual_memory_service
from services.offline_cache import offline_cache
from services.enhanced_data_service import enhanced_data_service

class UnifiedAIAdvisor:
    """Unified AI advisor that provides ChatGPT-like experience for agriculture"""
    
    def __init__(self):
        self.conversation_cache_hours = 24
        self.max_context_length = 4000
        self.active_queries = set()  # Track active queries to prevent concurrent processing
    
    async def process_unified_query(self, user_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process unified query with intelligent routing and human-like response"""
        print(f"\n=== UNIFIED AI ADVISOR PROCESSING START ===")
        print(f"User ID: {user_id}")
        print(f"Inputs received: {list(inputs.keys())}")
        print(f"Text query: {inputs.get('text', 'None')}")
        print(f"Language requested: {inputs.get('language', 'None')}")
        
        try:
            # Check if user already has an active query
            if user_id in self.active_queries:
                print(f"[ERROR] User {user_id} already has active query")
                return {
                    'success': False,
                    'error': 'Please wait for your previous query to complete before asking another question.'
                }
            
            # Mark user as having active query
            self.active_queries.add(user_id)
            print(f"[INFO] Added user {user_id} to active queries")
            
            try:
                # Extract primary text query
                text_query = inputs.get('text', '').strip()
                image_path = inputs.get('image_path')
                voice_data = inputs.get('voice_data')
                sensor_data = inputs.get('sensor_data')
                location_override = inputs.get('location')
                language_override = inputs.get('language')
                
                print(f"[INFO] Extracted data:")
                print(f"  - Text query: {text_query}")
                print(f"  - Image path: {image_path}")
                print(f"  - Language override: {language_override}")
                print(f"  - Location override: {location_override}")
                
                if not text_query and not image_path:
                    print(f"[ERROR] No text query or image provided")
                    return {
                        'success': False,
                        'error': 'Please provide a text query or upload an image'
                    }
                
                # Detect language and translate if needed
                original_language = 'en'
                original_query = text_query
                
                if text_query:
                    print(f"[INFO] Detecting language for: {text_query}")
                    original_language = detect_language(text_query)
                    print(f"[INFO] Detected language: {original_language}")
                    
                    # Use language override if provided
                    if language_override and language_override != 'en':
                        original_language = language_override
                        print(f"[INFO] Using language override: {original_language}")
                    
                    if original_language != 'en':
                        print(f"[INFO] Translating from {original_language} to English")
                        text_query = translate_text(text_query, original_language, 'en')
                        print(f"[INFO] Translated query: {text_query}")
                
                # Analyze the query to understand intent
                print(f"[INFO] Analyzing query intent...")
                query_analysis = intelligent_query_router.analyze_query(text_query, user_id)
                print(f"[INFO] Query analysis complete:")
                print(f"  - Intent: {query_analysis.intent.value}")
                print(f"  - Confidence: {query_analysis.confidence}")
                print(f"  - Required APIs: {query_analysis.requires_apis}")
                
                # Override location if specified in query
                if location_override:
                    query_analysis.extracted_info.locations = [location_override]
                    print(f"[INFO] Location override applied: {location_override}")
                
                # Collect all necessary data (real data only)
                print(f"[INFO] Collecting data from APIs...")
                # Use enhanced data service instead of the problematic data collector
                user_context_data = {}
                if user_id != 'anonymous':
                    from services.user_profiles import user_profile_service
                    profile = user_profile_service.get_profile(user_id)
                    if profile:
                        user_context_data = {
                            'profile': {
                                'location': profile.location,
                                'primary_crops': profile.primary_crops,
                                'farm_size': profile.farm_size.value if hasattr(profile.farm_size, 'value') else str(profile.farm_size),
                                'experience': profile.experience.value if hasattr(profile.experience, 'value') else str(profile.experience),
                                'soil_type': profile.soil_type,
                                'irrigation_type': profile.irrigation_type,
                                'preferred_language': profile.preferred_language
                            }
                        }
                
                # Use enhanced data service for robust data collection
                enhanced_result = await enhanced_data_service.get_comprehensive_data(text_query, user_context_data)
                
                # Convert enhanced result to expected format
                collected_data = {
                    'user_context': user_context_data,
                    'api_data': {},
                    'processed_insights': {}
                }
                
                if enhanced_result.get('success'):
                    # The enhanced service provides a complete response
                    ai_response = enhanced_result.get('response', 'No response generated')
                    data_sources = enhanced_result.get('data_sources', [])
                    confidence_score = 0.8 if enhanced_result.get('data_sources') else 0.6
                else:
                    ai_response = enhanced_result.get('response', 'Unable to process your request')
                    data_sources = []
                    confidence_score = 0.3
                
                print(f"[INFO] Data collection complete:")
                print(f"  - Enhanced data service success: {enhanced_result.get('success')}")
                print(f"  - Data sources: {data_sources}")
                
                # Process image if provided
                image_analysis = None
                if image_path:
                    print(f"[INFO] Processing image: {image_path}")
                    image_analysis = await self._process_image_input(image_path)
                    collected_data['image_analysis'] = image_analysis
                    print(f"[INFO] Image analysis complete: {image_analysis.get('crop_detected', 'Unknown')}")
                
                # Generate personalized, human-like response
                print(f"[INFO] Generating personalized response...")
                # Use the response from enhanced data service
                response = {
                    'main_response': ai_response,
                    'recommendations': self._extract_recommendations_from_response(ai_response),
                    'data_sources': data_sources,
                    'confidence_score': confidence_score,
                    'data_availability': enhanced_result.get('data_availability', {}),
                    'follow_up_suggestions': self._generate_simple_follow_ups(query_analysis.intent)
                }
                print(f"[INFO] Response generated, length: {len(response.get('main_response', ''))}")
                
                # Store conversation memory for future context
                if user_id != 'anonymous':
                    print(f"[INFO] Storing conversation memory for user {user_id}")
                    await self._store_conversation_memory(user_id, query_analysis, collected_data, response, original_query)
                
                # Determine response language - prioritize user's request
                response_language = original_language
                if language_override and language_override != 'en':
                    response_language = language_override
                
                print(f"[INFO] Response language determined: {response_language}")
                
                # Translate response if needed
                if response_language != 'en':
                    print(f"[INFO] Translating response from English to {response_language}")
                    try:
                        response['main_response'] = translate_text(response['main_response'], 'en', response_language)
                        print(f"[INFO] Main response translated successfully")
                        if response.get('recommendations'):
                            response['recommendations'] = [
                                translate_text(rec, 'en', response_language) for rec in response['recommendations']
                            ]
                            print(f"[INFO] Recommendations translated successfully")
                    except Exception as e:
                        print(f"[ERROR] Translation failed: {str(e)}")
                        # Keep English response if translation fails
                
                print(f"[SUCCESS] Query processing completed successfully")
                print(f"=== UNIFIED AI ADVISOR PROCESSING END ===\n")
                
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
                    'follow_up_suggestions': response.get('follow_up_suggestions', []),
                    'language_used': response_language,
                    'original_language': original_language
                }
                
            finally:
                # Always remove user from active queries
                self.active_queries.discard(user_id)
                print(f"[INFO] Removed user {user_id} from active queries")
            
        except Exception as e:
            self.active_queries.discard(user_id)
            print(f"[ERROR] Unified query processing error: {str(e)}")
            print(f"=== UNIFIED AI ADVISOR PROCESSING FAILED ===\n")
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}',
                'fallback_response': 'I apologize, but I encountered an error. Please try rephrasing your question or contact support.'
            }
    
    def _extract_recommendations_from_response(self, response: str) -> List[str]:
        """Extract actionable recommendations from AI response"""
        try:
            recommendations = []
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                # Look for bullet points, numbered lists, or recommendation keywords
                if (line.startswith('•') or line.startswith('-') or line.startswith('*') or
                    any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider'])):
                    clean_line = line.lstrip('•-* ').strip()
                    if len(clean_line) > 10:  # Meaningful recommendation
                        recommendations.append(clean_line)
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            print(f"[ERROR] Recommendation extraction error: {str(e)}")
            return []
    
    def _generate_simple_follow_ups(self, intent: QueryIntent) -> List[str]:
        """Generate simple follow-up suggestions based on intent"""
        try:
            follow_ups = {
                QueryIntent.SELLING_ADVICE: [
                    "What's the best time to harvest my crops?",
                    "How can I get better prices for my produce?",
                    "Should I store my crops or sell immediately?"
                ],
                QueryIntent.MARKET_PRICE: [
                    "Which market gives the best price for my crops?",
                    "How do I negotiate better prices?",
                    "What are the price trends for next month?"
                ],
                QueryIntent.IRRIGATION_ADVICE: [
                    "How much water should I use for irrigation?",
                    "What's the best time of day to irrigate?",
                    "How can I make my irrigation more efficient?"
                ],
                QueryIntent.GENERAL_FARMING: [
                    "What government schemes am I eligible for?",
                    "How can I improve my crop yield?",
                    "What are the best farming practices for my area?"
                ]
            }
            
            return follow_ups.get(intent, [
                "Ask me about irrigation timing",
                "Get market price information",
                "Learn about government schemes"
            ])
            
        except Exception as e:
            print(f"[ERROR] Follow-up generation error: {str(e)}")
            return []
    
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
        print(f"\n=== BUILDING CONTEXT PROMPT ===")
        print(f"Original query: {original_query}")
        print(f"Original language: {original_language}")
        
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
10. IMPORTANT: Respond in English only. The response will be translated to {original_language} after generation.
11. PROFIT FOCUS: Every recommendation should consider financial impact and ROI
12. HUMAN-LIKE COMMUNICATION: Use phrases like "Based on your farm's history..." or "Given your wheat is in vegetative stage..."
13. ACTIONABLE STEPS: Provide step-by-step instructions with specific timing and quantities
14. NEVER respond in Hindi or any other language - always use English for generation""")
        
        # Farmer's personal context
        user_context = collected_data.get('user_context', {}) or {}
        if user_context.get('profile'):
            profile = user_context['profile']
            print(f"[INFO] Adding user profile to context")
            prompt_parts.append(f"""
YOUR FARMER'S PROFILE:
- Name: {profile.get('name', 'Farmer')} from {profile.get('location', 'Unknown location')}
- Primary Crops: {', '.join(profile.get('primary_crops', []))}
- Farm Size: {profile.get('farm_size', 'Unknown')} acres
- Experience Level: {profile.get('experience', 'Unknown')}
- Soil Type: {profile.get('soil_type', 'Unknown')}
- Irrigation Method: {profile.get('irrigation_type', 'Unknown')}
- Preferred Language: {profile.get('preferred_language', 'Unknown')}""")
        else:
            print(f"[WARNING] No user profile available")
            prompt_parts.append(f"""
YOUR FARMER'S PROFILE:
- Profile: Not available - please ask farmer to complete their profile for personalized advice
- This limits the personalization of recommendations""")
        
        # Current farming status
        if user_context.get('farming'):
            farming = user_context['farming']
            print(f"[INFO] Adding farming context to prompt")
            prompt_parts.append(f"""
CURRENT FARMING STATUS:
- Last Irrigation: {farming.get('last_irrigation', 'Unknown')}
- Irrigation Frequency: Every {farming.get('irrigation_frequency', 'Unknown')} days
- Current Crop Stages: {json.dumps(farming.get('crop_stages', {}), indent=2)}
- Planting Dates: {json.dumps(farming.get('planting_dates', {}), indent=2)}""")
        else:
            print(f"[WARNING] No farming context available")
        
        # Recent conversation history for context
        if user_context.get('irrigation_history'):
            recent_irrigations = user_context['irrigation_history'][-3:]  # Last 3 irrigations
            print(f"[INFO] Adding irrigation history to context")
            prompt_parts.append(f"""
RECENT IRRIGATION HISTORY:
{json.dumps(recent_irrigations, indent=2)}""")
        
        # Original farmer's question
        prompt_parts.append(f"""
FARMER'S QUESTION: "{original_query}"
DETECTED INTENT: {query_analysis.intent.value}
FARMER'S PREFERRED LANGUAGE: {original_language}

IMPORTANT: Generate your response in English only. Do not use Hindi, Bengali, or any other language in your response. The system will handle translation to the farmer's preferred language ({original_language}) after you generate the response.""")
        
        # Real-time data availability and content
        api_data = collected_data.get('api_data', {}) or {}
        data_available = []
        data_unavailable = []
        
        # Weather data
        if api_data.get('weather'):
            data_available.append("Real-time weather data")
            print(f"[INFO] Adding weather data to context")
            prompt_parts.append("\nREAL-TIME WEATHER DATA:")
            for location, weather_info in (api_data.get('weather', {}) or {}).items():
                if not weather_info or not isinstance(weather_info, dict):
                    continue
                current = weather_info.get('current', {})
                forecast = weather_info.get('forecast', [])
                
                prompt_parts.append(f"\n{location.upper()} WEATHER:")
                prompt_parts.append(f"- Current: {current.get('temperature', 'N/A')}°C, {current.get('humidity', 'N/A')}% humidity")
                prompt_parts.append(f"- Conditions: {current.get('description', 'N/A')}")
                prompt_parts.append(f"- Wind: {current.get('wind_speed', 'N/A')} m/s")
                
                if forecast:
                    upcoming_rain = sum(day.get('rainfall', 0) for day in forecast[:3] if isinstance(day, dict))
                    prompt_parts.append(f"- Next 3 days rainfall: {upcoming_rain:.1f}mm")
        else:
            data_unavailable.append("weather data")
            print(f"[WARNING] Weather data not available")
        
        # Market data
        if api_data.get('market'):
            data_available.append("Real-time market prices")
            print(f"[INFO] Adding market data to context")
            prompt_parts.append("\nREAL-TIME MARKET DATA:")
            for location, market_info in (api_data.get('market', {}) or {}).items():
                if not market_info or not isinstance(market_info, dict):
                    continue
                prompt_parts.append(f"\n{location.upper()} MARKET:")
                for price in (market_info.get('current_prices', []) or []):
                    if not price or not isinstance(price, dict):
                        continue
                    prompt_parts.append(f"- {price['crop']}: ₹{price['price']}/{price['unit']} at {price['market']}")
                
                for trend in (market_info.get('price_trends', []) or []):
                    if not trend or not isinstance(trend, dict):
                        continue
                    direction = "📈" if trend['trend'] == 'increasing' else "📉" if trend['trend'] == 'decreasing' else "➡️"
                    prompt_parts.append(f"- {trend['crop']} trend: {direction} {trend['change_percent']:+.1f}% ({trend['recommendation']})")
        else:
            data_unavailable.append("market prices")
            print(f"[WARNING] Market data not available")
        
        # Irrigation analysis
        if api_data.get('irrigation'):
            data_available.append("Soil moisture and irrigation analysis")
            print(f"[INFO] Adding irrigation data to context")
            prompt_parts.append("\nIRRIGATION ANALYSIS:")
            for crop, irrigation_info in (api_data.get('irrigation', {}) or {}).items():
                if not irrigation_info or not isinstance(irrigation_info, dict):
                    continue
                prompt_parts.append(f"- {crop}: {irrigation_info['recommendation']} ({irrigation_info['water_amount']:.0f}L recommended)")
                for reason in (irrigation_info.get('reasoning', []) or []):
                    if reason and isinstance(reason, str):
                    prompt_parts.append(f"  • {reason}")
                
                # Data availability for irrigation
                data_avail = irrigation_info.get('data_availability', {})
                missing_irrigation_data = [k for k, v in (data_avail or {}).items() if not v]
                if missing_irrigation_data:
                    prompt_parts.append(f"  • Missing data: {', '.join(missing_irrigation_data)}")
        else:
            data_unavailable.append("soil moisture data")
            print(f"[WARNING] Irrigation data not available")
        
        # Image analysis
        image_analysis = collected_data.get('image_analysis')
        if image_analysis and isinstance(image_analysis, dict):
            if not img_analysis.get('error'):
                data_available.append("Image analysis")
                print(f"[INFO] Adding image analysis to context")
                prompt_parts.append(f"""
IMAGE ANALYSIS RESULTS:
- Crop Detected: {image_analysis.get('crop_detected', 'Unknown')}
- Disease/Condition: {image_analysis.get('disease_detected', 'Unknown')}
- Confidence: {image_analysis.get('confidence', 'Low')}
- Treatment Needed: {image_analysis.get('treatment', 'Not available')}""")
            else:
                data_unavailable.append("image analysis")
                print(f"[WARNING] Image analysis failed")
        
        # Data availability summary
        if data_available:
            prompt_parts.append(f"\nDATA AVAILABLE: {', '.join(data_available)}")
            print(f"[INFO] Data available: {data_available}")
        if data_unavailable:
            prompt_parts.append(f"\nDATA UNAVAILABLE: {', '.join(data_unavailable)}")
            print(f"[WARNING] Data unavailable: {data_unavailable}")
        
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
10. CRITICAL: Respond in English only. Do not use Hindi, Bengali, or any other language.
11. The farmer's preferred language is {original_language}, but you must respond in English for proper translation.

REMEMBER: You are their personal agricultural advisor who knows their farm intimately. Make them feel like this advice is crafted specifically for them.

LANGUAGE INSTRUCTION: Generate your entire response in English. Do not include any Hindi, Bengali, or other language text. The translation to {original_language} will be handled separately.""")
        
        final_prompt = "\n".join(prompt_parts)
        print(f"[INFO] Context prompt built, total length: {len(final_prompt)}")
        print(f"=== CONTEXT PROMPT BUILDING END ===\n")
        
        return final_prompt
    
    def _extract_actionable_recommendations(self, collected_data: Dict) -> List[str]:
        """Extract specific, actionable recommendations"""
        recommendations = []
        
        try:
            insights = collected_data.get('processed_insights', {}) or {}
            
            # Irrigation recommendations (most actionable)
            irrigation_insights = insights.get('irrigation', {}) or {}
            recommendations.extend(irrigation_insights.get('immediate_recommendations', []))
            recommendations.extend(irrigation_insights.get('timing_advice', []))
            
            # Market recommendations (profit-focused)
            market_insights = insights.get('market', {}) or {}
            recommendations.extend(market_insights.get('recommendations', []))
            
            # Profit optimization (highest priority)
            profit_insights = insights.get('profit_optimization', {}) or {}
            recommendations.extend(profit_insights.get('immediate_actions', []))
            recommendations.extend(profit_insights.get('short_term_strategy', []))
            
            # Weather-based recommendations
            weather_insights = insights.get('weather', {}) or {}
            for impact in (weather_insights.get('agricultural_impact', []) or []):
                if not impact or not isinstance(impact, dict):
                    continue
                recommendations.extend(impact.get('recommendations', []))
            
            # Filter out None or empty recommendations
            recommendations = [rec for rec in recommendations if rec and isinstance(rec, str)]
            
            return recommendations[:8]  # Limit to top 8 most actionable recommendations
            
        except Exception as e:
            print(f"Recommendation extraction error: {str(e)}")
            return []
    
    def _extract_data_sources(self, collected_data: Dict) -> List[str]:
        """Extract data sources used in the response"""
        sources = []
        
        try:
            api_data = collected_data.get('api_data', {}) or {}
            
            if api_data.get('market'):
                sources.append('Real-time Market Prices')
            if api_data.get('weather'):
                sources.append('Weather Forecast API')
            if api_data.get('irrigation'):
                sources.append('Soil Moisture & Irrigation Analysis')
            
            image_analysis = collected_data.get('image_analysis')
            if image_analysis and isinstance(image_analysis, dict) and not image_analysis.get('error'):
                sources.append('AI Image Analysis')
            
            if collected_data.get('user_context'):
                sources.append('Your Personal Farming Profile')
            
            # Add fallback if no sources
            if not sources:
                sources.append('General Agricultural Knowledge')
        
        except Exception as e:
            print(f"[ERROR] Data sources extraction error: {str(e)}")
            sources = ['General Agricultural Knowledge']
        
        return sources
    
    def _generate_contextual_follow_ups(self, query_analysis, collected_data: Dict) -> List[str]:
        """Generate intelligent follow-up suggestions based on context"""
        suggestions = []
        
        try:
            intent = query_analysis.intent
            user_context = collected_data.get('user_context', {}) or {}
            
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
            profile = user_context.get('profile', {}) or {}
            if profile.get('primary_crops'):
                crops = user_context['profile']['primary_crops']
                if isinstance(crops, list) and crops:
                    suggestions.append(f"Ask me about specific advice for your {', '.join(crops)} crops")
            
            # Add general suggestions if none generated
            if not suggestions:
                suggestions.extend([
                    "Ask me about irrigation timing for your crops",
                    "Get current market prices for your area",
                    "Learn about government schemes you're eligible for"
                ])
            
            return suggestions[:3]  # Limit to 3 suggestions
            
        except Exception as e:
            print(f"Follow-up generation error: {str(e)}")
            return ["Ask me anything about farming!", "Check market prices", "Get irrigation advice"]
    
    def _calculate_response_confidence(self, query_analysis, collected_data: Dict) -> float:
        """Calculate overall response confidence based on data availability"""
        try:
            base_confidence = query_analysis.confidence
            
            # Boost confidence based on available real data
            data_boost = 0
            api_data = collected_data.get('api_data', {}) or {}
            
            if api_data.get('market'):
                data_boost += 0.15
            if api_data.get('weather'):
                data_boost += 0.15
            if api_data.get('irrigation'):
                data_boost += 0.15
            
            user_context = collected_data.get('user_context', {}) or {}
            if user_context.get('profile'):
                data_boost += 0.20  # Personal context is very valuable
            
            image_analysis = collected_data.get('image_analysis')
            if image_analysis and isinstance(image_analysis, dict) and not image_analysis.get('error'):
                data_boost += 0.10
            
            return min(0.95, base_confidence + data_boost)
            
        except Exception as e:
            print(f"Confidence calculation error: {str(e)}")
            return 0.5
    
    def _track_data_availability(self, collected_data: Dict) -> Dict[str, bool]:
        """Track what data was available for transparency"""
        try:
            api_data = collected_data.get('api_data', {}) or {}
            user_context = collected_data.get('user_context', {}) or {}
            image_analysis = collected_data.get('image_analysis')
            
            return {
                'weather_data': bool(api_data.get('weather')),
                'market_data': bool(api_data.get('market')),
                'soil_moisture': bool(api_data.get('irrigation')),
                'user_profile': bool(user_context.get('profile')),
                'farming_context': bool(user_context.get('farming')),
                'image_analysis': bool(image_analysis and isinstance(image_analysis, dict) and not image_analysis.get('error')),
                'irrigation_history': bool(user_context.get('irrigation_history'))
            }
        
        except Exception as e:
            print(f"[ERROR] Data availability tracking error: {str(e)}")
            return {
                'weather_data': False,
                'market_data': False,
                'soil_moisture': False,
                'user_profile': False,
                'farming_context': False,
                'image_analysis': False,
                'irrigation_history': False
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
                response=response.get('main_response', 'Response not available'),
                context_data=context_data
            )
            
        except Exception as e:
            print(f"Memory storage error: {str(e)}")

# Global unified AI advisor
unified_ai_advisor = UnifiedAIAdvisor()
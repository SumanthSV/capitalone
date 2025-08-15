# services/hybrid_query_processor.py
import json
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from services.translation import detect_language, translate_text
from services.enhanced_gemini import enhanced_gemini

class HybridQueryProcessor:
    """Processes multi-modal queries (text, voice, image, sensor data) before unified AI processing"""
    
    def __init__(self):
        self.supported_languages = ['hi', 'en', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa']
    
    async def process_hybrid_input(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize multi-modal inputs"""
        try:
            processed_data = {
                'text_query': None,
                'image_analysis': None,
                'voice_transcript': None,
                'sensor_readings': None,
                'language': 'en',
                'original_language': 'en',
                'input_types': [],
                'processing_metadata': {}
            }
            
            # Process text input
            if inputs.get('text'):
                text_result = await self._process_text_input(inputs['text'])
                processed_data.update(text_result)
                processed_data['input_types'].append('text')
            
            # Process image input
            if inputs.get('image_path'):
                image_result = await self._process_image_input(inputs['image_path'])
                processed_data['image_analysis'] = image_result
                processed_data['input_types'].append('image')
            
            # Process voice input
            if inputs.get('voice_data'):
                voice_result = await self._process_voice_input(inputs['voice_data'])
                processed_data['voice_transcript'] = voice_result
                processed_data['input_types'].append('voice')
            
            # Process sensor data
            if inputs.get('sensor_data'):
                sensor_result = await self._process_sensor_input(inputs['sensor_data'])
                processed_data['sensor_readings'] = sensor_result
                processed_data['input_types'].append('sensor')
            
            # Combine and prioritize inputs
            combined_query = self._combine_inputs(processed_data)
            processed_data['combined_query'] = combined_query
            
            # Add processing metadata
            processed_data['processing_metadata'] = {
                'processed_at': datetime.now().isoformat(),
                'input_count': len(processed_data['input_types']),
                'primary_input': processed_data['input_types'][0] if processed_data['input_types'] else None,
                'language_detected': processed_data['language'],
                'translation_applied': processed_data['language'] != processed_data['original_language']
            }
            
            return {
                'success': True,
                'processed_data': processed_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processed_data': None
            }
    
    async def _process_text_input(self, text: str) -> Dict[str, Any]:
        """Process text input with language detection and translation"""
        try:
            # Detect language
            detected_lang = detect_language(text)
            original_text = text
            
            # Translate to English if needed
            if detected_lang != 'en':
                translated_text = translate_text(text, detected_lang, 'en')
            else:
                translated_text = text
            
            return {
                'text_query': translated_text,
                'original_text': original_text,
                'language': detected_lang,
                'original_language': detected_lang,
                'translation_confidence': 0.9 if detected_lang in self.supported_languages else 0.7
            }
            
        except Exception as e:
            return {
                'text_query': text,
                'original_text': text,
                'language': 'en',
                'original_language': 'en',
                'translation_error': str(e)
            }
    
    async def _process_image_input(self, image_path: str) -> Dict[str, Any]:
        """Process image input for agricultural analysis"""
        try:
            # Use enhanced Gemini for image analysis
            analysis = enhanced_gemini.analyze_image(image_path)
            
            # Extract key information
            return {
                'crop_detected': analysis.get('crop', 'Unknown'),
                'disease_detected': analysis.get('disease', 'None'),
                'confidence': analysis.get('confidence', 'Medium'),
                'symptoms': analysis.get('symptoms_observed', []),
                'treatment_needed': analysis.get('organic_treatment', ''),
                'severity': analysis.get('severity', 'Unknown'),
                'analysis_source': 'gemini_vision',
                'raw_analysis': analysis
            }
            
        except Exception as e:
            return {
                'crop_detected': 'Unknown',
                'disease_detected': 'Analysis Failed',
                'confidence': 'Low',
                'error': str(e),
                'analysis_source': 'error'
            }
    
    async def _process_voice_input(self, voice_data: str) -> Dict[str, Any]:
        """Process voice input (transcript or audio data)"""
        try:
            # If voice_data is already a transcript
            if isinstance(voice_data, str) and len(voice_data) > 10:
                # Process as text
                text_result = await self._process_text_input(voice_data)
                return {
                    'transcript': text_result['text_query'],
                    'original_transcript': text_result['original_text'],
                    'language': text_result['language'],
                    'source': 'voice_transcript',
                    'confidence': 0.8
                }
            
            # If it's audio data (base64 encoded), would need speech-to-text
            # For now, return placeholder
            return {
                'transcript': '',
                'original_transcript': '',
                'language': 'en',
                'source': 'voice_audio',
                'confidence': 0.0,
                'note': 'Voice processing not implemented'
            }
            
        except Exception as e:
            return {
                'transcript': '',
                'error': str(e),
                'source': 'voice_error'
            }
    
    async def _process_sensor_input(self, sensor_data: Union[str, Dict]) -> Dict[str, Any]:
        """Process sensor data input"""
        try:
            # Parse sensor data if it's a string
            if isinstance(sensor_data, str):
                sensor_data = json.loads(sensor_data)
            
            # Validate and normalize sensor readings
            normalized_data = {
                'soil_moisture': self._normalize_sensor_value(sensor_data.get('soil_moisture'), 0, 100),
                'temperature': self._normalize_sensor_value(sensor_data.get('temperature'), -10, 50),
                'ph_level': self._normalize_sensor_value(sensor_data.get('ph'), 0, 14),
                'humidity': self._normalize_sensor_value(sensor_data.get('humidity'), 0, 100),
                'light_intensity': self._normalize_sensor_value(sensor_data.get('light_intensity'), 0, 100000),
                'timestamp': sensor_data.get('timestamp', datetime.now().isoformat())
            }
            
            # Generate sensor-based insights
            insights = self._generate_sensor_insights(normalized_data)
            
            return {
                'readings': normalized_data,
                'insights': insights,
                'data_quality': self._assess_sensor_data_quality(normalized_data),
                'source': 'iot_sensors'
            }
            
        except Exception as e:
            return {
                'readings': {},
                'error': str(e),
                'source': 'sensor_error'
            }
    
    def _normalize_sensor_value(self, value: Any, min_val: float, max_val: float) -> Optional[float]:
        """Normalize and validate sensor values"""
        try:
            if value is None:
                return None
            
            float_val = float(value)
            
            # Check if value is within reasonable range
            if min_val <= float_val <= max_val:
                return round(float_val, 2)
            else:
                return None  # Invalid reading
                
        except (ValueError, TypeError):
            return None
    
    def _generate_sensor_insights(self, sensor_data: Dict[str, Any]) -> List[str]:
        """Generate insights from sensor readings"""
        insights = []
        
        # Soil moisture insights
        soil_moisture = sensor_data.get('soil_moisture')
        if soil_moisture is not None:
            if soil_moisture < 30:
                insights.append("Soil moisture is low - irrigation may be needed")
            elif soil_moisture > 80:
                insights.append("Soil moisture is high - avoid overwatering")
            else:
                insights.append("Soil moisture levels are adequate")
        
        # Temperature insights
        temperature = sensor_data.get('temperature')
        if temperature is not None:
            if temperature > 35:
                insights.append("High temperature detected - consider shade protection")
            elif temperature < 10:
                insights.append("Low temperature - protect crops from cold stress")
        
        # pH insights
        ph_level = sensor_data.get('ph_level')
        if ph_level is not None:
            if ph_level < 6.0:
                insights.append("Soil is acidic - consider lime application")
            elif ph_level > 8.0:
                insights.append("Soil is alkaline - consider sulfur application")
        
        return insights
    
    def _assess_sensor_data_quality(self, sensor_data: Dict[str, Any]) -> str:
        """Assess the quality of sensor data"""
        valid_readings = sum(1 for value in sensor_data.values() if value is not None and isinstance(value, (int, float)))
        total_readings = len([k for k in sensor_data.keys() if k != 'timestamp'])
        
        if valid_readings == 0:
            return "poor"
        elif valid_readings < total_readings * 0.5:
            return "fair"
        elif valid_readings < total_readings * 0.8:
            return "good"
        else:
            return "excellent"
    
    def _combine_inputs(self, processed_data: Dict[str, Any]) -> str:
        """Combine multiple inputs into a unified query"""
        query_parts = []
        
        # Add text query
        if processed_data.get('text_query'):
            query_parts.append(processed_data['text_query'])
        
        # Add voice transcript
        if processed_data.get('voice_transcript', {}).get('transcript'):
            voice_text = processed_data['voice_transcript']['transcript']
            if voice_text and voice_text != processed_data.get('text_query'):
                query_parts.append(f"Voice input: {voice_text}")
        
        # Add image analysis
        if processed_data.get('image_analysis'):
            img_analysis = processed_data['image_analysis']
            if img_analysis.get('crop_detected') != 'Unknown':
                query_parts.append(f"Image shows: {img_analysis['crop_detected']}")
                if img_analysis.get('disease_detected') and img_analysis['disease_detected'] != 'None':
                    query_parts.append(f"Possible disease: {img_analysis['disease_detected']}")
        
        # Add sensor insights
        if processed_data.get('sensor_readings', {}).get('insights'):
            sensor_insights = processed_data['sensor_readings']['insights']
            if sensor_insights:
                query_parts.append(f"Sensor data indicates: {'; '.join(sensor_insights)}")
        
        # Combine all parts
        if query_parts:
            return ". ".join(query_parts)
        else:
            return "General agricultural inquiry"

# Global hybrid query processor
hybrid_query_processor = HybridQueryProcessor()
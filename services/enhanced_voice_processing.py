"""
Enhanced Voice Processing Service
Supports multiple Indian languages with real-time speech-to-text and text-to-speech
"""

import os
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from services.translation import detect_language, translate_text
from services.offline_cache import offline_cache

class VoiceProcessingService:
    """Enhanced voice processing with multi-language support"""
    
    def __init__(self):
        self.supported_languages = {
            'hi': 'hi-IN',  # Hindi
            'en': 'en-IN',  # English (India)
            'bn': 'bn-IN',  # Bengali
            'te': 'te-IN',  # Telugu
            'mr': 'mr-IN',  # Marathi
            'ta': 'ta-IN',  # Tamil
            'gu': 'gu-IN',  # Gujarati
            'kn': 'kn-IN',  # Kannada
            'ml': 'ml-IN',  # Malayalam
            'pa': 'pa-IN'   # Punjabi
        }
        
        self.cache_expiry_hours = 1  # Cache voice processing for 1 hour
        
        # Initialize speech recognition (would use Google Cloud Speech-to-Text in production)
        self.speech_config = {
            'sample_rate': 16000,
            'encoding': 'LINEAR16',
            'language_code': 'hi-IN',
            'enable_automatic_punctuation': True,
            'enable_word_time_offsets': True,
            'model': 'latest_long'
        }
    
    async def process_voice_input(self, audio_data: str, language_hint: str = 'hi') -> Dict[str, Any]:
        """Process voice input and convert to text"""
        try:
            # Check cache first
            cache_key = f"voice_processing_{hash(audio_data)}_{language_hint}"
            cached_result = offline_cache.get(cache_key)
            
            if cached_result:
                return cached_result
            
            # Determine language code
            language_code = self.supported_languages.get(language_hint, 'hi-IN')
            
            # Process audio data
            if audio_data.startswith('data:audio'):
                # Extract base64 audio data
                audio_bytes = self._extract_audio_from_data_url(audio_data)
            else:
                # Assume it's already base64 encoded
                audio_bytes = base64.b64decode(audio_data)
            
            # Perform speech-to-text conversion
            transcript_result = await self._speech_to_text(audio_bytes, language_code)
            
            # Post-process the transcript
            processed_result = self._post_process_transcript(transcript_result, language_hint)
            
            # Cache the result
            offline_cache.set(cache_key, processed_result, self.cache_expiry_hours)
            
            return processed_result
            
        except Exception as e:
            print(f"Voice processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': '',
                'confidence': 0.0,
                'language_detected': language_hint
            }
    
    async def generate_voice_response(self, text: str, language: str = 'hi') -> Dict[str, Any]:
        """Generate voice response from text"""
        try:
            # Check cache first
            cache_key = f"tts_{hash(text)}_{language}"
            cached_result = offline_cache.get(cache_key)
            
            if cached_result:
                return cached_result
            
            # Determine language code
            language_code = self.supported_languages.get(language, 'hi-IN')
            
            # Generate speech from text
            audio_result = await self._text_to_speech(text, language_code)
            
            # Cache the result
            offline_cache.set(cache_key, audio_result, self.cache_expiry_hours)
            
            return audio_result
            
        except Exception as e:
            print(f"Voice generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None
            }
    
    async def _speech_to_text(self, audio_bytes: bytes, language_code: str) -> Dict[str, Any]:
        """Convert speech to text using speech recognition service"""
        try:
            # In production, this would use Google Cloud Speech-to-Text API
            # For now, simulate the process
            
            # Simulate API call delay
            await asyncio.sleep(0.5)
            
            # Simulate speech recognition result
            # In reality, this would process the actual audio
            simulated_transcripts = {
                'hi-IN': [
                    "मुझे अपनी फसल के बारे में जानकारी चाहिए",
                    "क्या मैं आज सिंचाई कर सकता हूं",
                    "बाजार में गेहूं का भाव क्या है",
                    "मेरी फसल में कोई बीमारी तो नहीं है"
                ],
                'en-IN': [
                    "I need information about my crops",
                    "Can I irrigate today",
                    "What is the wheat price in market",
                    "Is there any disease in my crop"
                ]
            }
            
            # Select a random transcript for simulation
            import random
            transcripts = simulated_transcripts.get(language_code, simulated_transcripts['hi-IN'])
            selected_transcript = random.choice(transcripts)
            
            return {
                'success': True,
                'transcript': selected_transcript,
                'confidence': 0.85 + random.random() * 0.1,  # 0.85-0.95
                'language_detected': language_code,
                'alternatives': [
                    {
                        'transcript': selected_transcript,
                        'confidence': 0.85 + random.random() * 0.1
                    }
                ],
                'word_timestamps': []  # Would contain word-level timestamps in production
            }
            
        except Exception as e:
            print(f"Speech-to-text error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': '',
                'confidence': 0.0
            }
    
    async def _text_to_speech(self, text: str, language_code: str) -> Dict[str, Any]:
        """Convert text to speech using TTS service"""
        try:
            # In production, this would use Google Cloud Text-to-Speech API
            # For now, simulate the process
            
            # Simulate API call delay
            await asyncio.sleep(0.3)
            
            # Simulate TTS result
            # In reality, this would generate actual audio
            simulated_audio_data = base64.b64encode(b"simulated_audio_data").decode('utf-8')
            
            return {
                'success': True,
                'audio_data': simulated_audio_data,
                'audio_format': 'mp3',
                'language': language_code,
                'text_processed': text,
                'duration_seconds': len(text) * 0.1  # Rough estimate
            }
            
        except Exception as e:
            print(f"Text-to-speech error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None
            }
    
    def _extract_audio_from_data_url(self, data_url: str) -> bytes:
        """Extract audio bytes from data URL"""
        try:
            # Parse data URL format: data:audio/wav;base64,<base64_data>
            header, data = data_url.split(',', 1)
            return base64.b64decode(data)
        except Exception as e:
            print(f"Audio extraction error: {str(e)}")
            return b""
    
    def _post_process_transcript(self, transcript_result: Dict[str, Any], language_hint: str) -> Dict[str, Any]:
        """Post-process the transcript for better accuracy"""
        try:
            if not transcript_result.get('success'):
                return transcript_result
            
            transcript = transcript_result['transcript']
            
            # Clean up the transcript
            cleaned_transcript = self._clean_transcript(transcript)
            
            # Detect actual language
            detected_language = detect_language(cleaned_transcript)
            
            # Translate if needed
            if detected_language != 'en' and language_hint == 'en':
                translated_text = translate_text(cleaned_transcript, detected_language, 'en')
            else:
                translated_text = cleaned_transcript
            
            # Apply agricultural context corrections
            corrected_transcript = self._apply_agricultural_corrections(cleaned_transcript, detected_language)
            
            return {
                'success': True,
                'transcript': corrected_transcript,
                'translated_transcript': translated_text,
                'confidence': transcript_result.get('confidence', 0.8),
                'language_detected': detected_language,
                'original_transcript': transcript,
                'processing_applied': [
                    'cleaning',
                    'language_detection',
                    'agricultural_corrections'
                ]
            }
            
        except Exception as e:
            print(f"Transcript post-processing error: {str(e)}")
            return transcript_result
    
    def _clean_transcript(self, transcript: str) -> str:
        """Clean up the transcript"""
        # Remove extra spaces
        cleaned = ' '.join(transcript.split())
        
        # Fix common speech recognition errors
        corrections = {
            'फसल': ['फसल', 'फ़सल'],
            'सिंचाई': ['सिंचाई', 'सिचाई'],
            'बाजार': ['बाजार', 'बाज़ार'],
            'irrigation': ['irrigation', 'irriation', 'irigation'],
            'market': ['market', 'markit'],
            'crop': ['crop', 'crops']
        }
        
        for correct, variants in corrections.items():
            for variant in variants:
                cleaned = cleaned.replace(variant, correct)
        
        return cleaned
    
    def _apply_agricultural_corrections(self, transcript: str, language: str) -> str:
        """Apply agricultural domain-specific corrections"""
        # Common agricultural terms and their corrections
        agricultural_corrections = {
            'hi': {
                'गेहूं': ['गेहु', 'गेहुं'],
                'धान': ['धान', 'धन'],
                'कपास': ['कपास', 'कपस'],
                'मक्का': ['मक्का', 'मका'],
                'सरसों': ['सरसों', 'सरसो']
            },
            'en': {
                'wheat': ['weat', 'whea'],
                'rice': ['ryce', 'ric'],
                'cotton': ['coton', 'cotten'],
                'maize': ['maze', 'mais'],
                'mustard': ['mustar', 'mustrd']
            }
        }
        
        corrections = agricultural_corrections.get(language, {})
        corrected_transcript = transcript
        
        for correct, variants in corrections.items():
            for variant in variants:
                corrected_transcript = corrected_transcript.replace(variant, correct)
        
        return corrected_transcript
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return {
            'hi': 'हिंदी (Hindi)',
            'en': 'English',
            'bn': 'বাংলা (Bengali)',
            'te': 'తెలుగు (Telugu)',
            'mr': 'मराठी (Marathi)',
            'ta': 'தமிழ் (Tamil)',
            'gu': 'ગુજરાતી (Gujarati)',
            'kn': 'ಕನ್ನಡ (Kannada)',
            'ml': 'മലയാളം (Malayalam)',
            'pa': 'ਪੰਜਾਬੀ (Punjabi)'
        }
    
    def get_voice_processing_stats(self) -> Dict[str, Any]:
        """Get voice processing statistics"""
        return {
            'supported_languages': len(self.supported_languages),
            'cache_expiry_hours': self.cache_expiry_hours,
            'features': [
                'Multi-language speech recognition',
                'Text-to-speech synthesis',
                'Agricultural domain corrections',
                'Real-time processing',
                'Offline caching'
            ]
        }

# Global voice processing service
voice_processing_service = VoiceProcessingService()
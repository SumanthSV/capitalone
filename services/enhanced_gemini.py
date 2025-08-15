# services/enhanced_gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import json
from typing import Dict, Any, Optional
try:
    from services.error_handler import error_handler, APIError
except ImportError:
    # Fallback error handling if error_handler not available
    class APIError(Exception):
        def __init__(self, message, error_code="UNKNOWN"):
            self.message = message
            self.error_code = error_code
            super().__init__(message)
    
    class ErrorHandler:
        @staticmethod
        def handle_error(error, context=""):
            return {"user_message": str(error)}
    
    error_handler = ErrorHandler()

# Load environment variables
load_dotenv()

class EnhancedGeminiService:
    def __init__(self):
        """Initialize Enhanced Gemini Service with error handling"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise APIError(
                "Gemini API key not found", 
                error_code="GEMINI_API_KEY_MISSING"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        try:
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
            self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Safety settings to allow agricultural content
            self.safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
        except Exception as e:
            raise APIError(f"Failed to initialize Gemini models: {str(e)}")
    
    def get_text_response(self, prompt: str, temperature: float = 0.3) -> str:
        """Get text response from Gemini with enhanced error handling"""
        try:
            response = self.text_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                ),
                safety_settings=self.safety_settings
            )
            
            if response.candidates and response.candidates[0].content:
                return response.candidates[0].content.parts[0].text
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            error_info = error_handler.handle_error(e, "gemini_text_generation")
            return f"Error: {error_info['user_message']}"
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze agricultural image with enhanced prompting"""
        try:
            # Load and validate image
            image = Image.open(image_path)
            
            # Enhanced agricultural analysis prompt
            prompt = """
            You are an expert agricultural pathologist. Analyze this image and provide detailed information in JSON format.

            Please identify:
            1. The crop/plant type
            2. Any diseases, pests, or health issues visible
            3. Confidence level (High/Medium/Low)
            4. Organic treatment recommendations
            5. Prevention methods
            6. Severity assessment

            Return ONLY valid JSON in this exact format:
            {
                "crop": "crop name",
                "disease": "disease name or 'Healthy' if no issues",
                "confidence": "High/Medium/Low",
                "severity": "Mild/Moderate/Severe/None",
                "organic_treatment": "detailed organic treatment steps",
                "prevention": "prevention methods",
                "symptoms_observed": ["list", "of", "symptoms"],
                "recommended_actions": ["immediate", "actions", "to", "take"]
            }
            """
            
            response = self.vision_model.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                ),
                safety_settings=self.safety_settings
            )
            
            if response.candidates and response.candidates[0].content:
                response_text = response.candidates[0].content.parts[0].text
                
                # Try to parse JSON response
                try:
                    # Clean the response text
                    response_text = response_text.strip()
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]
                    
                    analysis = json.loads(response_text)
                    
                    # Validate required fields
                    required_fields = ['crop', 'disease', 'confidence']
                    for field in required_fields:
                        if field not in analysis:
                            analysis[field] = 'Unknown'
                    
                    return analysis
                    
                except json.JSONDecodeError:
                    # Fallback to structured text parsing
                    return self._parse_text_response(response_text)
            
            return {
                "crop": "Unknown",
                "disease": "Unable to analyze image",
                "confidence": "Low",
                "organic_treatment": "Please consult a local agricultural expert",
                "error": "No valid response from vision model"
            }
            
        except Exception as e:
            error_info = error_handler.handle_error(e, "gemini_image_analysis")
            return {
                "crop": "Unknown",
                "disease": "Analysis failed",
                "confidence": "Low",
                "organic_treatment": "Please consult a local agricultural expert",
                "error": error_info['user_message']
            }
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Fallback text parsing when JSON parsing fails"""
        analysis = {
            "crop": "Unknown",
            "disease": "Unknown", 
            "confidence": "Medium",
            "organic_treatment": "",
            "prevention": "",
            "symptoms_observed": [],
            "recommended_actions": []
        }
        
        # Simple keyword extraction
        text_lower = text.lower()
        
        # Common crop keywords
        crops = ['tomato', 'potato', 'corn', 'wheat', 'rice', 'cotton', 'soybean']
        for crop in crops:
            if crop in text_lower:
                analysis['crop'] = crop.title()
                break
        
        # Common disease keywords
        diseases = ['blight', 'rust', 'mildew', 'spot', 'rot', 'wilt', 'mosaic']
        for disease in diseases:
            if disease in text_lower:
                analysis['disease'] = disease.title()
                break
        
        # Extract treatment information
        if 'treatment' in text_lower or 'spray' in text_lower:
            lines = text.split('\n')
            treatment_lines = [line for line in lines if 'treatment' in line.lower() or 'spray' in line.lower()]
            analysis['organic_treatment'] = ' '.join(treatment_lines)
        
        return analysis

# Global instance
enhanced_gemini = EnhancedGeminiService()
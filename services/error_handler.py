"""
Centralized error handling and user-friendly error messages
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('krishimitra.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class KrishiMitraError(Exception):
    """Base exception for KrishiMitra application"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

class APIError(KrishiMitraError):
    """API-related errors"""
    pass

class DatabaseError(KrishiMitraError):
    """Database-related errors"""
    pass

class ImageProcessingError(KrishiMitraError):
    """Image processing errors"""
    pass

class ErrorHandler:
    """Centralized error handling with user-friendly messages"""
    
    ERROR_MESSAGES = {
        "GEMINI_API_KEY_MISSING": {
            "user_message": "AI service is not configured. Please check your API keys.",
            "technical_message": "GEMINI_API_KEY environment variable is missing"
        },
        "WEATHER_API_ERROR": {
            "user_message": "Weather information is temporarily unavailable. Using cached data if available.",
            "technical_message": "OpenWeather API request failed"
        },
        "WEATHER_API_KEY_MISSING": {
            "user_message": "Weather service is not configured. Using general weather guidance.",
            "technical_message": "OpenWeather API key is missing"
        },
        "IMAGE_PROCESSING_ERROR": {
            "user_message": "Unable to analyze the uploaded image. Please try with a clearer image.",
            "technical_message": "Image processing pipeline failed"
        },
        "DATABASE_ERROR": {
            "user_message": "Unable to access crop database. Some recommendations may be limited.",
            "technical_message": "SQLite database query failed"
        },
        "TRANSLATION_ERROR": {
            "user_message": "Translation service is unavailable. Responding in English.",
            "technical_message": "Google Translate API failed"
        },
        "NETWORK_ERROR": {
            "user_message": "Network connection issue. Using offline capabilities where possible.",
            "technical_message": "Network request failed"
        }
    }
    
    @classmethod
    def handle_error(cls, error: Exception, context: str = "", user_language: str = "en") -> Dict[str, Any]:
        """Handle errors and return user-friendly messages"""
        
        # Log the error
        logger.error(f"Error in {context}: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Determine error type and get appropriate message
        if isinstance(error, KrishiMitraError):
            error_code = error.error_code
            user_message = cls.ERROR_MESSAGES.get(error_code, {}).get("user_message", str(error))
        else:
            # Map common exceptions to error codes
            error_code = cls._map_exception_to_code(error)
            user_message = cls.ERROR_MESSAGES.get(error_code, {}).get("user_message", 
                                                                     "An unexpected error occurred. Please try again.")
        
        return {
            "success": False,
            "error_code": error_code,
            "user_message": user_message,
            "technical_details": str(error) if logger.level <= logging.DEBUG else None,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "fallback_available": cls._has_fallback(error_code)
        }
    
    @classmethod
    def _map_exception_to_code(cls, error: Exception) -> str:
        """Map common exceptions to error codes"""
        error_type = type(error).__name__
        
        mapping = {
            "ConnectionError": "NETWORK_ERROR",
            "TimeoutError": "NETWORK_ERROR",
            "HTTPError": "NETWORK_ERROR",
            "FileNotFoundError": "IMAGE_PROCESSING_ERROR",
            "PermissionError": "IMAGE_PROCESSING_ERROR",
            "sqlite3.Error": "DATABASE_ERROR",
            "json.JSONDecodeError": "API_RESPONSE_ERROR",
            "KeyError": "DATA_MISSING_ERROR",
            "ValueError": "INPUT_VALIDATION_ERROR"
        }
        
        return mapping.get(error_type, "UNKNOWN_ERROR")
    
    @classmethod
    def _has_fallback(cls, error_code: str) -> bool:
        """Check if fallback mechanisms are available for this error type"""
        fallback_available = {
            "WEATHER_API_ERROR": True,  # Can use cached weather data
            "GEMINI_API_KEY_MISSING": False,  # No fallback for missing API key
            "IMAGE_PROCESSING_ERROR": True,  # Can try color-based matching
            "DATABASE_ERROR": False,  # No fallback for database issues
            "TRANSLATION_ERROR": True,  # Can respond in English
            "NETWORK_ERROR": True  # Can use offline capabilities
        }
        
        return fallback_available.get(error_code, False)
    
    @classmethod
    def create_fallback_response(cls, error_code: str, context: Dict = None) -> Dict[str, Any]:
        """Create fallback responses when primary services fail"""
        context = context or {}
        
        fallback_responses = {
            "WEATHER_API_ERROR": {
                "current_weather": {
                    "temperature": "N/A",
                    "humidity": "N/A",
                    "description": "Weather data unavailable",
                    "source": "fallback"
                }
            },
            "IMAGE_PROCESSING_ERROR": {
                "disease_info": {
                    "crop": "Unknown",
                    "disease": "Unable to analyze image",
                    "confidence": "Low",
                    "organic_treatment": "Please consult a local agricultural expert",
                    "source": "fallback"
                }
            },
            "TRANSLATION_ERROR": {
                "language": "en",
                "translation_note": "Responding in English due to translation service unavailability"
            }
        }
        
        return fallback_responses.get(error_code, {})

# Global error handler instance
error_handler = ErrorHandler()
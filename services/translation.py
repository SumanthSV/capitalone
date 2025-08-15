# services/translation.py
from deep_translator import GoogleTranslator
import langdetect

def detect_language(text: str) -> str:
    """Detect language of input text"""
    try:
        return langdetect.detect(text)
    except:
        return "en"  # Default to English

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text between languages"""
    try:
        if source_lang == target_lang:
            return text
        
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails

def get_supported_languages() -> dict:
    """Get supported languages"""
    return {
        'hi': 'Hindi',
        'en': 'English',
        'bn': 'Bengali',
        'te': 'Telugu',
        'mr': 'Marathi',
        'ta': 'Tamil',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'pa': 'Punjabi'
    }

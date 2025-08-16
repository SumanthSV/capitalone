# services/translation.py
from deep_translator import GoogleTranslator
import langdetect

def detect_language(text: str) -> str:
    """Detect language of input text"""
    print(f"\n=== LANGUAGE DETECTION START ===")
    print(f"Text to detect: {text}")
    
    try:
        detected = langdetect.detect(text)
        print(f"[SUCCESS] Language detected: {detected}")
        print(f"=== LANGUAGE DETECTION END ===\n")
        return detected
    except Exception as e:
        print(f"[ERROR] Language detection failed: {str(e)}")
        print(f"[INFO] Defaulting to English")
        print(f"=== LANGUAGE DETECTION END ===\n")
        return "en"  # Default to English

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text between languages"""
    print(f"\n=== TRANSLATION START ===")
    print(f"Source language: {source_lang}")
    print(f"Target language: {target_lang}")
    print(f"Text to translate: {text[:100]}...")
    
    try:
        if source_lang == target_lang:
            print(f"[INFO] Source and target languages are same, no translation needed")
            print(f"=== TRANSLATION END ===\n")
            return text
        
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        print(f"[SUCCESS] Translation completed")
        print(f"[INFO] Translated text: {translated[:100]}...")
        print(f"=== TRANSLATION END ===\n")
        return translated
    except Exception as e:
        print(f"[ERROR] Translation failed: {str(e)}")
        print(f"[INFO] Returning original text")
        print(f"=== TRANSLATION END ===\n")
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

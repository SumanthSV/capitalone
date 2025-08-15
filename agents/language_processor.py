# agents/language_processor.py
from services.translation import detect_language, translate_text
from agents.orchestrator import AgentState

def process_language(state: AgentState) -> AgentState:
    """Detect and translate user input if needed"""
    try:
        user_query = state.get('user_query', '')
        
        if not user_query:
            return state
        
        # Detect language
        detected_lang = detect_language(user_query)
        
        # Translate to English for processing if needed
        if detected_lang != 'en':
            translated_query = translate_text(user_query, detected_lang, 'en')
            return {
                **state,
                "original_language": detected_lang,
                "original_query": user_query,
                "user_query": translated_query,
                "language": detected_lang
            }
        
        return {
            **state,
            "original_language": "en",
            "language": "en"
        }
    except Exception as e:
        print(f"Language processing error: {str(e)}")
        return state
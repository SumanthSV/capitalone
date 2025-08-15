# agents/rag_agent.py
from services.vector_db import vector_db
from agents.orchestrator import AgentState
from services.offline_cache import offline_cache

def enhance_with_rag(state: AgentState) -> AgentState:
    """Enhance responses with offline RAG knowledge"""
    try:
        user_query = state.get('user_query', '')
        if not user_query:
            return state
        
        # Check cache first
        cache_key = f"rag_{hash(user_query)}"
        cached_results = offline_cache.get(cache_key)
        
        if cached_results:
            return {
                **state,
                "rag_results": cached_results,
                "rag_source": "cache"
            }
        
        # Search relevant knowledge
        crop_results = vector_db.search_crop_knowledge(user_query, n_results=2)
        disease_results = vector_db.search_disease_knowledge(user_query, n_results=2)
        practice_results = vector_db.search_farming_practices(user_query, n_results=2)
        
        rag_results = {
            "crop_knowledge": crop_results,
            "disease_knowledge": disease_results,
            "farming_practices": practice_results,
            "total_results": len(crop_results) + len(disease_results) + len(practice_results)
        }
        
        # Cache results
        offline_cache.set(cache_key, rag_results, expiry_hours=24)
        
        return {
            **state,
            "rag_results": rag_results,
            "rag_source": "vector_db"
        }
    
    except Exception as e:
        print(f"RAG enhancement error: {str(e)}")
        return state
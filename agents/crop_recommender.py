# agents/crop_recommender.py
from database.queries import get_crop_recommendations
from agents.orchestrator import AgentState

def recommend_crops(state: AgentState) -> AgentState:
    """Retrieve crops matching parameters from database"""
    params = {
        'soil_ph': state['soil_ph'],
        'rainfall': state['rainfall'],
        'temperature': state['temperature'],
        'soil_type': state['soil_type'],
        'season': state['season'],
        'location': state['location']
    }
    
    recommendations, query = get_crop_recommendations(params)
    
    return {
        **state,
        "sql_query": query,
        "crop_recommendations": recommendations
    }
# agents/validation_trust.py
from agents.orchestrator import AgentState
import json

def validate_and_score(state: AgentState) -> AgentState:
    """Add confidence scoring and source citations"""
    try:
        confidence_score = calculate_confidence(state)
        source_citations = generate_citations(state)
        
        return {
            **state,
            "confidence_score": confidence_score,
            "source_citations": source_citations,
            "reliability_check": confidence_score > 0.7
        }
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return state

def calculate_confidence(state: AgentState) -> float:
    """Calculate overall confidence score"""
    scores = []
    
    # Crop recommendation confidence
    if state.get("crop_recommendations"):
        scores.append(0.9)  # High confidence for database matches
    
    # Disease detection confidence
    if state.get("disease_info"):
        disease_conf = state["disease_info"].get("confidence", "Medium")
        conf_map = {"High": 0.9, "Medium": 0.7, "Low": 0.5}
        scores.append(conf_map.get(disease_conf, 0.5))
    
    # Weather data confidence
    if state.get("current_weather"):
        scores.append(0.8)  # Weather APIs are generally reliable
    
    # Market data confidence
    if state.get("market_prices"):
        scores.append(0.8)
    
    return sum(scores) / len(scores) if scores else 0.5

def generate_citations(state: AgentState) -> list:
    """Generate source citations for transparency"""
    citations = []
    
    if state.get("crop_recommendations"):
        citations.append({
            "source": "Local Crop Database",
            "type": "database",
            "reliability": "High"
        })
    
    if state.get("disease_info"):
        source = state["disease_info"].get("source", "unknown")
        citations.append({
            "source": f"Disease Detection ({source})",
            "type": "ai_analysis" if source == "gemini" else "database",
            "reliability": "Medium" if source == "gemini" else "High"
        })
    
    if state.get("current_weather"):
        citations.append({
            "source": "Weather API",
            "type": "api",
            "reliability": "High"
        })
    
    return citations
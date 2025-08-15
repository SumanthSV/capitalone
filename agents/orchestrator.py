# agents/orchestrator.py
from typing import TypedDict, List, Dict, Optional, Union

class AgentState(TypedDict):
    # User inputs
    user_query: Optional[str]
    original_query: Optional[str]  # Original query before translation
    original_language: Optional[str]  # Detected language
    location: Optional[str]
    language: Optional[str]
    image_path: Optional[str]  # New field for image uploads
    timestamp: str
    
    # Extracted parameters
    soil_ph: Optional[float]
    rainfall: Optional[float]
    temperature: Optional[float]
    soil_type: Optional[str]
    altitude: Optional[float]
    season: Optional[str]
    
    # Agent outputs
    sql_query: str
    crop_recommendations: List[Dict]
    disease_info: Optional[Dict]  # New field for disease results
    
    # New agent outputs
    current_weather: Optional[Dict]
    weather_forecast: Optional[List[Dict]]
    agricultural_alerts: Optional[List[Dict]]
    credit_options: Optional[List[Dict]]
    government_schemes: Optional[List[Dict]]
    market_prices: Optional[List[Dict]]
    price_trends: Optional[List[Dict]]
    
    # Trust and validation
    confidence_score: Optional[float]
    source_citations: Optional[List[Dict]]
    reliability_check: Optional[bool]
    
    llm_response: str
# agents/weather_agent.py
from services.weather import get_current_weather, get_weather_forecast, get_agricultural_alerts
from agents.orchestrator import AgentState

def get_weather_insights(state: AgentState) -> AgentState:
    """Get weather information for agricultural planning"""
    try:
        location = state.get('location', '')
        
        if not location:
            return state
        
        # Get current weather
        current_weather = get_current_weather(location)
        
        # Get 7-day forecast
        weather_forecast = get_weather_forecast(location, days=7)
        
        # Get agricultural alerts
        agricultural_alerts = get_agricultural_alerts(location, current_weather) if current_weather else []
        
        return {
            **state,
            "current_weather": current_weather,
            "weather_forecast": weather_forecast,
            "agricultural_alerts": agricultural_alerts
        }
    except Exception as e:
        print(f"Weather insights error: {str(e)}")
        return state
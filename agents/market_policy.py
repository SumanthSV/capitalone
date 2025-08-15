# agents/market_policy.py
from services.real_market_api import real_market_api
from agents.orchestrator import AgentState

def get_market_insights(state: AgentState) -> AgentState:
    """Get market prices and policy information"""
    try:
        location = state.get('location', '')
        crops = [crop['name'] for crop in state.get('crop_recommendations', [])]
        
        # Get current market prices
        market_prices = real_market_api.get_consolidated_prices(crops, location)
        
        # Get price trends
        price_trends = real_market_api.get_price_trends(crops, days=30)
        
        return {
            **state,
            "market_prices": market_prices,
            "price_trends": price_trends
        }
    except Exception as e:
        print(f"Market insights error: {str(e)}")
        return {
            **state,
            "market_prices": [],
            "price_trends": []
        }
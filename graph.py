# graph.py
from langgraph.graph import StateGraph, END
from agents.orchestrator import AgentState
from services.unified_ai_advisor import unified_ai_advisor

def create_workflow():
    """Simplified workflow that routes everything to unified AI advisor"""
    workflow = StateGraph(AgentState)
    
    # Single node for unified processing
    workflow.add_node("unified_processor", process_unified_query)
    
    # Set entry point
    workflow.set_entry_point("unified_processor")
    
    # Direct to end
    workflow.add_edge("unified_processor", END)
    
    return workflow.compile()

async def process_unified_query(state: AgentState) -> AgentState:
    """Process query using unified AI advisor"""
    try:
        # Prepare inputs for unified advisor
        inputs = {
            'text': state.get('user_query'),
            'image_path': state.get('image_path'),
            'voice_data': state.get('voice_data'),
            'sensor_data': state.get('sensor_data'),
            'location': state.get('location'),
            'language': state.get('language', 'hindi')
        }
        
        # Process with unified advisor
        result = await unified_ai_advisor.process_unified_query(
            user_id=state.get('user_id', 'anonymous'),
            inputs=inputs
        )
        
        if result['success']:
            return {
                **state,
                "llm_response": result['response'],
                "confidence_score": result.get('confidence_score', 0.7),
                "data_sources": result.get('data_sources', []),
                "intent_detected": result.get('intent_detected', 'general'),
                "apis_called": result.get('apis_called', []),
                "context_applied": result.get('context_applied', False),
                "data_availability": result.get('data_availability', {}),
                "follow_up_suggestions": result.get('follow_up_suggestions', [])
            }
        else:
            return {
                **state,
                "llm_response": result.get('fallback_response', 'I apologize, but I encountered an error processing your request.'),
                "error": result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        print(f"Unified query processing error: {str(e)}")
        return {
            **state,
            "llm_response": "I apologize, but I encountered an error. Please try again or contact support.",
            "error": str(e)
        }

# Compile workflow
workflow = create_workflow()
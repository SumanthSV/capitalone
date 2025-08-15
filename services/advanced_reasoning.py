"""
Advanced Reasoning Engine for KrishiMitra
Implements multi-step reasoning and complex decision-making for agricultural scenarios
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from services.enhanced_gemini import enhanced_gemini

class ReasoningType(Enum):
    TRADE_OFF_ANALYSIS = "trade_off_analysis"
    MULTI_STEP_PLANNING = "multi_step_planning"
    RISK_ASSESSMENT = "risk_assessment"
    PROFIT_OPTIMIZATION = "profit_optimization"
    SEASONAL_PLANNING = "seasonal_planning"

@dataclass
class ReasoningStep:
    step_number: int
    description: str
    data_required: List[str]
    analysis: str
    confidence: float
    alternatives: List[str]

@dataclass
class ReasoningResult:
    reasoning_type: ReasoningType
    primary_recommendation: str
    confidence_score: float
    reasoning_steps: List[ReasoningStep]
    trade_offs: Dict[str, Any]
    risk_factors: List[str]
    expected_outcomes: Dict[str, Any]
    alternative_strategies: List[str]
    implementation_timeline: List[Dict[str, Any]]

class AdvancedReasoningEngine:
    """Advanced reasoning engine for complex agricultural decision-making"""
    
    def __init__(self):
        self.reasoning_templates = {
            ReasoningType.TRADE_OFF_ANALYSIS: self._trade_off_template,
            ReasoningType.MULTI_STEP_PLANNING: self._multi_step_template,
            ReasoningType.RISK_ASSESSMENT: self._risk_assessment_template,
            ReasoningType.PROFIT_OPTIMIZATION: self._profit_optimization_template,
            ReasoningType.SEASONAL_PLANNING: self._seasonal_planning_template
        }
    
    async def analyze_complex_scenario(self, query: str, context_data: Dict[str, Any], 
                                     reasoning_type: ReasoningType) -> ReasoningResult:
        """Perform advanced reasoning for complex agricultural scenarios"""
        try:
            # Get appropriate reasoning template
            template_func = self.reasoning_templates.get(reasoning_type)
            if not template_func:
                raise ValueError(f"Unsupported reasoning type: {reasoning_type}")
            
            # Generate reasoning prompt
            reasoning_prompt = template_func(query, context_data)
            
            # Get AI analysis
            ai_response = enhanced_gemini.get_text_response(reasoning_prompt, temperature=0.2)
            
            # Parse and structure the response
            reasoning_result = self._parse_reasoning_response(ai_response, reasoning_type)
            
            return reasoning_result
            
        except Exception as e:
            print(f"Advanced reasoning error: {str(e)}")
            return self._create_fallback_reasoning(query, reasoning_type)
    
    def _trade_off_template(self, query: str, context_data: Dict[str, Any]) -> str:
        """Template for trade-off analysis scenarios"""
        user_context = context_data.get('user_context', {})
        api_data = context_data.get('api_data', {})
        
        return f"""
ADVANCED AGRICULTURAL TRADE-OFF ANALYSIS

FARMER'S SITUATION:
{json.dumps(user_context, indent=2)}

REAL-TIME DATA:
{json.dumps(api_data, indent=2)}

FARMER'S QUESTION: "{query}"

INSTRUCTIONS: Perform a comprehensive trade-off analysis following these steps:

STEP 1: IDENTIFY KEY TRADE-OFFS
- List all major trade-offs involved in this decision
- Quantify each trade-off with specific numbers where possible
- Consider short-term vs long-term implications

STEP 2: ANALYZE EACH OPTION
For each possible action:
- Calculate potential profit/loss
- Assess risk level (1-10 scale)
- Estimate probability of success
- Consider resource requirements

STEP 3: MARKET TIMING ANALYSIS
- Current market conditions
- Price trend predictions
- Optimal timing windows
- Seasonal factors

STEP 4: RISK MITIGATION
- Identify major risks for each option
- Suggest risk mitigation strategies
- Calculate risk-adjusted returns

STEP 5: FINAL RECOMMENDATION
- Recommend the best option with clear reasoning
- Provide implementation timeline
- Suggest monitoring checkpoints

FORMAT YOUR RESPONSE AS:
TRADE-OFF ANALYSIS:
[Detailed analysis]

RECOMMENDATION:
[Clear, actionable recommendation]

IMPLEMENTATION PLAN:
[Step-by-step timeline]

RISK FACTORS:
[Key risks and mitigation strategies]

EXPECTED OUTCOMES:
[Quantified expected results]
"""
    
    def _multi_step_template(self, query: str, context_data: Dict[str, Any]) -> str:
        """Template for multi-step planning scenarios"""
        return f"""
MULTI-STEP AGRICULTURAL PLANNING

CONTEXT: {json.dumps(context_data, indent=2)}
QUERY: "{query}"

INSTRUCTIONS: Create a comprehensive multi-step plan following this structure:

STEP 1: SITUATION ANALYSIS
- Current farm status
- Available resources
- Constraints and limitations

STEP 2: GOAL DEFINITION
- Primary objectives
- Success metrics
- Timeline expectations

STEP 3: STRATEGY DEVELOPMENT
- Break down into actionable steps
- Sequence steps logically
- Identify dependencies

STEP 4: RESOURCE PLANNING
- Required inputs for each step
- Cost estimates
- Labor requirements

STEP 5: TIMELINE CREATION
- Optimal timing for each step
- Weather dependencies
- Market timing considerations

STEP 6: CONTINGENCY PLANNING
- Alternative approaches
- Risk mitigation steps
- Backup plans

Provide a detailed, implementable plan with specific dates, quantities, and actions.
"""
    
    def _risk_assessment_template(self, query: str, context_data: Dict[str, Any]) -> str:
        """Template for comprehensive risk assessment"""
        return f"""
COMPREHENSIVE AGRICULTURAL RISK ASSESSMENT

CONTEXT: {json.dumps(context_data, indent=2)}
SCENARIO: "{query}"

INSTRUCTIONS: Conduct a thorough risk assessment:

RISK IDENTIFICATION:
1. Weather-related risks
2. Market price risks
3. Pest/disease risks
4. Financial risks
5. Operational risks

RISK QUANTIFICATION:
For each risk:
- Probability of occurrence (%)
- Potential impact (₹ amount)
- Risk score (probability × impact)
- Mitigation cost

RISK PRIORITIZATION:
- Rank risks by severity
- Identify critical risks requiring immediate attention
- Assess cumulative risk exposure

MITIGATION STRATEGIES:
- Preventive measures
- Risk transfer options (insurance, contracts)
- Diversification strategies
- Emergency response plans

MONITORING FRAMEWORK:
- Key risk indicators
- Monitoring frequency
- Alert thresholds
- Response protocols

Provide specific, actionable risk management recommendations.
"""
    
    def _profit_optimization_template(self, query: str, context_data: Dict[str, Any]) -> str:
        """Template for profit optimization analysis"""
        return f"""
PROFIT OPTIMIZATION ANALYSIS

CONTEXT: {json.dumps(context_data, indent=2)}
OPTIMIZATION GOAL: "{query}"

INSTRUCTIONS: Perform comprehensive profit optimization:

REVENUE OPTIMIZATION:
- Current revenue streams
- Market price analysis
- Timing optimization
- Quality premiums
- Value-added opportunities

COST OPTIMIZATION:
- Input cost analysis
- Efficiency improvements
- Bulk purchasing opportunities
- Labor optimization
- Technology adoption benefits

YIELD OPTIMIZATION:
- Current vs potential yields
- Limiting factors
- Improvement strategies
- Investment requirements
- ROI calculations

MARKET STRATEGY:
- Best selling channels
- Optimal timing
- Price negotiation strategies
- Contract farming opportunities

FINANCIAL PROJECTIONS:
- Current profit margins
- Optimized profit projections
- Investment requirements
- Payback periods
- Break-even analysis

Provide specific recommendations with quantified profit improvements.
"""
    
    def _seasonal_planning_template(self, query: str, context_data: Dict[str, Any]) -> str:
        """Template for seasonal planning scenarios"""
        return f"""
COMPREHENSIVE SEASONAL PLANNING

CONTEXT: {json.dumps(context_data, indent=2)}
PLANNING REQUEST: "{query}"

INSTRUCTIONS: Create a detailed seasonal plan:

SEASONAL ANALYSIS:
- Current season status
- Upcoming seasonal transitions
- Historical patterns
- Climate predictions

CROP PLANNING:
- Optimal crop selection
- Planting schedules
- Harvest timing
- Rotation strategies

RESOURCE PLANNING:
- Seasonal resource requirements
- Labor scheduling
- Equipment needs
- Input procurement timing

MARKET TIMING:
- Seasonal price patterns
- Optimal selling windows
- Storage strategies
- Market demand cycles

RISK MANAGEMENT:
- Seasonal risks
- Weather contingencies
- Market volatility management
- Insurance considerations

IMPLEMENTATION CALENDAR:
- Month-by-month action plan
- Critical decision points
- Monitoring milestones
- Adjustment opportunities

Provide a comprehensive seasonal strategy with specific timelines and actions.
"""
    
    def _parse_reasoning_response(self, ai_response: str, reasoning_type: ReasoningType) -> ReasoningResult:
        """Parse AI response into structured reasoning result"""
        try:
            # Extract key sections from the response
            sections = self._extract_response_sections(ai_response)
            
            # Create reasoning steps
            reasoning_steps = self._extract_reasoning_steps(sections)
            
            # Extract trade-offs
            trade_offs = self._extract_trade_offs(sections)
            
            # Extract risk factors
            risk_factors = self._extract_risk_factors(sections)
            
            # Extract expected outcomes
            expected_outcomes = self._extract_expected_outcomes(sections)
            
            # Extract alternatives
            alternatives = self._extract_alternatives(sections)
            
            # Extract implementation timeline
            timeline = self._extract_timeline(sections)
            
            # Determine primary recommendation and confidence
            primary_recommendation = sections.get('recommendation', ai_response[:500])
            confidence_score = self._calculate_confidence_score(sections)
            
            return ReasoningResult(
                reasoning_type=reasoning_type,
                primary_recommendation=primary_recommendation,
                confidence_score=confidence_score,
                reasoning_steps=reasoning_steps,
                trade_offs=trade_offs,
                risk_factors=risk_factors,
                expected_outcomes=expected_outcomes,
                alternative_strategies=alternatives,
                implementation_timeline=timeline
            )
            
        except Exception as e:
            print(f"Response parsing error: {str(e)}")
            return self._create_fallback_reasoning(ai_response, reasoning_type)
    
    def _extract_response_sections(self, response: str) -> Dict[str, str]:
        """Extract different sections from AI response"""
        sections = {}
        
        # Common section headers
        section_headers = [
            'TRADE-OFF ANALYSIS:', 'RECOMMENDATION:', 'IMPLEMENTATION PLAN:',
            'RISK FACTORS:', 'EXPECTED OUTCOMES:', 'ALTERNATIVES:',
            'TIMELINE:', 'ANALYSIS:', 'STRATEGY:', 'CONCLUSION:'
        ]
        
        current_section = 'main'
        current_content = []
        
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a section header
            header_found = None
            for header in section_headers:
                if line.upper().startswith(header):
                    header_found = header.lower().replace(':', '').replace(' ', '_')
                    break
            
            if header_found:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = header_found
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_reasoning_steps(self, sections: Dict[str, str]) -> List[ReasoningStep]:
        """Extract reasoning steps from response sections"""
        steps = []
        
        # Look for numbered steps in various sections
        for section_name, content in sections.items():
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if line.strip().startswith(('STEP', 'Step', '1.', '2.', '3.', '4.', '5.')):
                    step_number = len(steps) + 1
                    description = line.strip()
                    
                    # Get analysis content (next few lines)
                    analysis_lines = []
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip() and not lines[j].strip().startswith(('STEP', 'Step')):
                            analysis_lines.append(lines[j].strip())
                        else:
                            break
                    
                    analysis = ' '.join(analysis_lines)
                    
                    steps.append(ReasoningStep(
                        step_number=step_number,
                        description=description,
                        data_required=[],
                        analysis=analysis,
                        confidence=0.8,
                        alternatives=[]
                    ))
        
        return steps[:5]  # Limit to 5 steps
    
    def _extract_trade_offs(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract trade-off information"""
        trade_offs = {}
        
        trade_off_section = sections.get('trade_off_analysis', sections.get('analysis', ''))
        
        if trade_off_section:
            # Look for trade-off patterns
            lines = trade_off_section.split('\n')
            for line in lines:
                if 'vs' in line.lower() or 'versus' in line.lower():
                    trade_offs[f"trade_off_{len(trade_offs) + 1}"] = line.strip()
        
        return trade_offs
    
    def _extract_risk_factors(self, sections: Dict[str, str]) -> List[str]:
        """Extract risk factors from response"""
        risks = []
        
        risk_section = sections.get('risk_factors', sections.get('risks', ''))
        
        if risk_section:
            lines = risk_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 'risk' in line.lower()):
                    risks.append(line.lstrip('- •'))
        
        return risks[:10]  # Limit to 10 risks
    
    def _extract_expected_outcomes(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract expected outcomes"""
        outcomes = {}
        
        outcomes_section = sections.get('expected_outcomes', sections.get('outcomes', ''))
        
        if outcomes_section:
            # Look for quantified outcomes
            lines = outcomes_section.split('\n')
            for line in lines:
                if '₹' in line or '%' in line or 'increase' in line.lower() or 'decrease' in line.lower():
                    outcomes[f"outcome_{len(outcomes) + 1}"] = line.strip()
        
        return outcomes
    
    def _extract_alternatives(self, sections: Dict[str, str]) -> List[str]:
        """Extract alternative strategies"""
        alternatives = []
        
        alt_section = sections.get('alternatives', sections.get('alternative_strategies', ''))
        
        if alt_section:
            lines = alt_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 'alternative' in line.lower()):
                    alternatives.append(line.lstrip('- •'))
        
        return alternatives[:5]  # Limit to 5 alternatives
    
    def _extract_timeline(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract implementation timeline"""
        timeline = []
        
        timeline_section = sections.get('implementation_plan', sections.get('timeline', ''))
        
        if timeline_section:
            lines = timeline_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and ('day' in line.lower() or 'week' in line.lower() or 'month' in line.lower()):
                    timeline.append({
                        'action': line,
                        'timing': 'TBD',
                        'priority': 'medium'
                    })
        
        return timeline[:10]  # Limit to 10 timeline items
    
    def _calculate_confidence_score(self, sections: Dict[str, str]) -> float:
        """Calculate overall confidence score"""
        # Base confidence
        confidence = 0.7
        
        # Boost confidence based on available sections
        if sections.get('analysis'):
            confidence += 0.1
        if sections.get('recommendation'):
            confidence += 0.1
        if sections.get('risk_factors'):
            confidence += 0.05
        if sections.get('expected_outcomes'):
            confidence += 0.05
        
        return min(0.95, confidence)
    
    def _create_fallback_reasoning(self, query: str, reasoning_type: ReasoningType) -> ReasoningResult:
        """Create fallback reasoning result when parsing fails"""
        return ReasoningResult(
            reasoning_type=reasoning_type,
            primary_recommendation=f"Unable to perform advanced reasoning for: {query}",
            confidence_score=0.3,
            reasoning_steps=[],
            trade_offs={},
            risk_factors=["Insufficient data for comprehensive analysis"],
            expected_outcomes={},
            alternative_strategies=["Consult local agricultural expert"],
            implementation_timeline=[]
        )

# Global advanced reasoning engine
advanced_reasoning_engine = AdvancedReasoningEngine()
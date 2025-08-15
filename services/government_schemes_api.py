"""
Government Schemes and Policies API Integration
Fetches real-time information about agricultural schemes, subsidies, and loan programs
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from services.offline_cache import offline_cache

class SchemeType(Enum):
    SUBSIDY = "subsidy"
    LOAN = "loan"
    INSURANCE = "insurance"
    TRAINING = "training"
    EQUIPMENT = "equipment"
    SEED = "seed"
    FERTILIZER = "fertilizer"
    IRRIGATION = "irrigation"

class EligibilityStatus(Enum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PARTIALLY_ELIGIBLE = "partially_eligible"
    UNKNOWN = "unknown"

@dataclass
class GovernmentScheme:
    scheme_id: str
    name: str
    description: str
    scheme_type: SchemeType
    implementing_agency: str
    eligibility_criteria: List[str]
    benefits: List[str]
    application_process: List[str]
    required_documents: List[str]
    application_deadline: Optional[datetime]
    budget_allocation: Optional[float]
    beneficiaries_target: Optional[int]
    states_covered: List[str]
    crops_covered: List[str]
    contact_info: Dict[str, str]
    website_url: Optional[str]
    last_updated: datetime

@dataclass
class EligibilityAssessment:
    scheme: GovernmentScheme
    status: EligibilityStatus
    eligibility_score: float
    matching_criteria: List[str]
    missing_criteria: List[str]
    recommendations: List[str]
    estimated_benefit: Optional[float]

class GovernmentSchemesAPI:
    """API service for government agricultural schemes and policies"""
    
    def __init__(self):
        # Government API endpoints (these would be real endpoints in production)
        self.api_endpoints = {
            'central_schemes': 'https://api.india.gov.in/agriculture/schemes',
            'state_schemes': 'https://api.india.gov.in/states/{state}/agriculture/schemes',
            'loan_schemes': 'https://api.nabard.org/schemes',
            'insurance_schemes': 'https://api.aic.co.in/schemes',
            'subsidy_schemes': 'https://api.agricoop.nic.in/subsidies'
        }
        
        self.cache_expiry_hours = 24  # Cache schemes for 24 hours
        
        # Predefined schemes database (fallback when APIs are unavailable)
        self.fallback_schemes = self._load_fallback_schemes()
    
    def get_applicable_schemes(self, user_profile: Dict[str, Any], 
                             location: str, crops: List[str]) -> List[EligibilityAssessment]:
        """Get schemes applicable to the user's profile and location"""
        try:
            cache_key = f"schemes_{location}_{'-'.join(crops)}_{user_profile.get('farm_size', 'unknown')}"
            cached_schemes = offline_cache.get(cache_key)
            
            if cached_schemes:
                return [self._dict_to_eligibility_assessment(scheme) for scheme in cached_schemes]
            
            # Fetch schemes from multiple sources
            all_schemes = []
            
            # Central government schemes
            central_schemes = self._fetch_central_schemes()
            all_schemes.extend(central_schemes)
            
            # State-specific schemes
            state = self._extract_state_from_location(location)
            if state:
                state_schemes = self._fetch_state_schemes(state)
                all_schemes.extend(state_schemes)
            
            # Loan schemes
            loan_schemes = self._fetch_loan_schemes()
            all_schemes.extend(loan_schemes)
            
            # Insurance schemes
            insurance_schemes = self._fetch_insurance_schemes()
            all_schemes.extend(insurance_schemes)
            
            # Assess eligibility for each scheme
            eligible_schemes = []
            for scheme in all_schemes:
                assessment = self._assess_eligibility(scheme, user_profile, location, crops)
                if assessment.status in [EligibilityStatus.ELIGIBLE, EligibilityStatus.PARTIALLY_ELIGIBLE]:
                    eligible_schemes.append(assessment)
            
            # Sort by eligibility score
            eligible_schemes.sort(key=lambda x: x.eligibility_score, reverse=True)
            
            # Cache results
            cache_data = [self._eligibility_assessment_to_dict(scheme) for scheme in eligible_schemes]
            offline_cache.set(cache_key, cache_data, self.cache_expiry_hours)
            
            return eligible_schemes[:10]  # Return top 10 schemes
            
        except Exception as e:
            print(f"Government schemes API error: {str(e)}")
            return self._get_fallback_schemes(user_profile, location, crops)
    
    def get_scheme_details(self, scheme_id: str) -> Optional[GovernmentScheme]:
        """Get detailed information about a specific scheme"""
        try:
            cache_key = f"scheme_details_{scheme_id}"
            cached_scheme = offline_cache.get(cache_key)
            
            if cached_scheme:
                return self._dict_to_scheme(cached_scheme)
            
            # Try to fetch from various APIs
            scheme = None
            
            # Try central schemes API
            scheme = self._fetch_scheme_from_central_api(scheme_id)
            
            if not scheme:
                # Try other APIs
                scheme = self._fetch_scheme_from_other_apis(scheme_id)
            
            if not scheme:
                # Fallback to predefined schemes
                scheme = self._get_fallback_scheme(scheme_id)
            
            if scheme:
                # Cache the scheme
                offline_cache.set(cache_key, self._scheme_to_dict(scheme), self.cache_expiry_hours)
            
            return scheme
            
        except Exception as e:
            print(f"Scheme details error: {str(e)}")
            return self._get_fallback_scheme(scheme_id)
    
    def get_loan_recommendations(self, user_profile: Dict[str, Any], 
                               loan_amount: float, purpose: str) -> List[Dict[str, Any]]:
        """Get personalized loan recommendations"""
        try:
            recommendations = []
            
            # Assess user's loan eligibility profile
            eligibility_profile = self._assess_loan_eligibility_profile(user_profile)
            
            # Get applicable loan schemes
            loan_schemes = self._fetch_loan_schemes()
            
            for scheme in loan_schemes:
                if scheme.scheme_type == SchemeType.LOAN:
                    # Calculate loan terms
                    loan_terms = self._calculate_loan_terms(scheme, user_profile, loan_amount)
                    
                    if loan_terms['eligible']:
                        recommendations.append({
                            'scheme': scheme,
                            'loan_terms': loan_terms,
                            'eligibility_score': loan_terms['eligibility_score'],
                            'estimated_approval_time': loan_terms['approval_time'],
                            'required_documents': scheme.required_documents,
                            'application_process': scheme.application_process
                        })
            
            # Sort by eligibility score and interest rate
            recommendations.sort(key=lambda x: (x['eligibility_score'], -x['loan_terms']['interest_rate']), reverse=True)
            
            return recommendations[:5]  # Top 5 recommendations
            
        except Exception as e:
            print(f"Loan recommendations error: {str(e)}")
            return self._get_fallback_loan_recommendations(user_profile, loan_amount)
    
    def _fetch_central_schemes(self) -> List[GovernmentScheme]:
        """Fetch central government schemes"""
        try:
            # In production, this would call the actual API
            # For now, return fallback schemes
            return [scheme for scheme in self.fallback_schemes if 'central' in scheme.implementing_agency.lower()]
            
        except Exception as e:
            print(f"Central schemes fetch error: {str(e)}")
            return []
    
    def _fetch_state_schemes(self, state: str) -> List[GovernmentScheme]:
        """Fetch state-specific schemes"""
        try:
            # Filter fallback schemes by state
            return [scheme for scheme in self.fallback_schemes 
                   if state.lower() in [s.lower() for s in scheme.states_covered]]
            
        except Exception as e:
            print(f"State schemes fetch error: {str(e)}")
            return []
    
    def _fetch_loan_schemes(self) -> List[GovernmentScheme]:
        """Fetch loan schemes"""
        try:
            return [scheme for scheme in self.fallback_schemes if scheme.scheme_type == SchemeType.LOAN]
            
        except Exception as e:
            print(f"Loan schemes fetch error: {str(e)}")
            return []
    
    def _fetch_insurance_schemes(self) -> List[GovernmentScheme]:
        """Fetch insurance schemes"""
        try:
            return [scheme for scheme in self.fallback_schemes if scheme.scheme_type == SchemeType.INSURANCE]
            
        except Exception as e:
            print(f"Insurance schemes fetch error: {str(e)}")
            return []
    
    def _assess_eligibility(self, scheme: GovernmentScheme, user_profile: Dict[str, Any], 
                          location: str, crops: List[str]) -> EligibilityAssessment:
        """Assess user's eligibility for a scheme"""
        try:
            matching_criteria = []
            missing_criteria = []
            eligibility_score = 0.0
            
            # Check location eligibility
            state = self._extract_state_from_location(location)
            if not scheme.states_covered or state.lower() in [s.lower() for s in scheme.states_covered]:
                matching_criteria.append("Location eligible")
                eligibility_score += 0.2
            else:
                missing_criteria.append("Not available in your state")
            
            # Check crop eligibility
            if not scheme.crops_covered or any(crop.lower() in [c.lower() for c in scheme.crops_covered] for crop in crops):
                matching_criteria.append("Crops covered")
                eligibility_score += 0.2
            else:
                missing_criteria.append("Your crops not covered")
            
            # Check farm size eligibility
            farm_size = user_profile.get('farm_size_acres', 0)
            if self._check_farm_size_eligibility(scheme, farm_size):
                matching_criteria.append("Farm size eligible")
                eligibility_score += 0.2
            else:
                missing_criteria.append("Farm size not in eligible range")
            
            # Check experience eligibility
            experience = user_profile.get('farming_experience', 'beginner')
            if self._check_experience_eligibility(scheme, experience):
                matching_criteria.append("Experience level suitable")
                eligibility_score += 0.2
            
            # Check additional criteria
            additional_score = self._check_additional_criteria(scheme, user_profile)
            eligibility_score += additional_score
            
            # Determine eligibility status
            if eligibility_score >= 0.8:
                status = EligibilityStatus.ELIGIBLE
            elif eligibility_score >= 0.5:
                status = EligibilityStatus.PARTIALLY_ELIGIBLE
            elif eligibility_score >= 0.2:
                status = EligibilityStatus.NOT_ELIGIBLE
            else:
                status = EligibilityStatus.UNKNOWN
            
            # Generate recommendations
            recommendations = self._generate_eligibility_recommendations(scheme, missing_criteria, user_profile)
            
            # Estimate benefit
            estimated_benefit = self._estimate_scheme_benefit(scheme, user_profile)
            
            return EligibilityAssessment(
                scheme=scheme,
                status=status,
                eligibility_score=eligibility_score,
                matching_criteria=matching_criteria,
                missing_criteria=missing_criteria,
                recommendations=recommendations,
                estimated_benefit=estimated_benefit
            )
            
        except Exception as e:
            print(f"Eligibility assessment error: {str(e)}")
            return EligibilityAssessment(
                scheme=scheme,
                status=EligibilityStatus.UNKNOWN,
                eligibility_score=0.0,
                matching_criteria=[],
                missing_criteria=["Unable to assess eligibility"],
                recommendations=["Contact scheme administrator for details"],
                estimated_benefit=None
            )
    
    def _load_fallback_schemes(self) -> List[GovernmentScheme]:
        """Load predefined government schemes as fallback"""
        schemes = []
        
        # PM-KISAN Scheme
        schemes.append(GovernmentScheme(
            scheme_id="PM_KISAN_2024",
            name="PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            description="Direct income support to farmers with cultivable land",
            scheme_type=SchemeType.SUBSIDY,
            implementing_agency="Ministry of Agriculture & Farmers Welfare",
            eligibility_criteria=[
                "Farmer families with cultivable land",
                "Land records in farmer's name",
                "Valid Aadhaar card",
                "Bank account linked to Aadhaar"
            ],
            benefits=[
                "₹6,000 per year in three installments",
                "Direct bank transfer",
                "No upper limit on farm size"
            ],
            application_process=[
                "Visit PM-KISAN portal or CSC",
                "Fill application form",
                "Upload required documents",
                "Submit for verification"
            ],
            required_documents=[
                "Aadhaar card",
                "Bank account details",
                "Land ownership documents",
                "Mobile number"
            ],
            application_deadline=None,
            budget_allocation=75000.0,  # 75,000 crores
            beneficiaries_target=120000000,  # 12 crore farmers
            states_covered=["All States", "All UTs"],
            crops_covered=["All Crops"],
            contact_info={
                "helpline": "155261",
                "email": "pmkisan-ict@gov.in",
                "website": "pmkisan.gov.in"
            },
            website_url="https://pmkisan.gov.in",
            last_updated=datetime.now()
        ))
        
        # Kisan Credit Card
        schemes.append(GovernmentScheme(
            scheme_id="KCC_2024",
            name="Kisan Credit Card (KCC)",
            description="Credit facility for farmers to meet crop production needs",
            scheme_type=SchemeType.LOAN,
            implementing_agency="NABARD, Commercial Banks, RRBs, Cooperative Banks",
            eligibility_criteria=[
                "Farmers with cultivable land",
                "Tenant farmers with valid documents",
                "Self Help Group members",
                "Good credit history"
            ],
            benefits=[
                "Credit limit based on cropping pattern",
                "Flexible repayment",
                "Interest subvention available",
                "Insurance coverage"
            ],
            application_process=[
                "Visit nearest bank branch",
                "Fill KCC application form",
                "Submit required documents",
                "Bank verification and approval"
            ],
            required_documents=[
                "Identity proof",
                "Address proof",
                "Land documents",
                "Income proof",
                "Passport size photographs"
            ],
            application_deadline=None,
            budget_allocation=None,
            beneficiaries_target=None,
            states_covered=["All States"],
            crops_covered=["All Crops"],
            contact_info={
                "helpline": "1800-180-1551",
                "website": "nabard.org"
            },
            website_url="https://www.nabard.org/content1.aspx?id=523",
            last_updated=datetime.now()
        ))
        
        # Pradhan Mantri Fasal Bima Yojana
        schemes.append(GovernmentScheme(
            scheme_id="PMFBY_2024",
            name="Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            description="Crop insurance scheme providing financial support to farmers",
            scheme_type=SchemeType.INSURANCE,
            implementing_agency="Ministry of Agriculture & Farmers Welfare",
            eligibility_criteria=[
                "All farmers including sharecroppers and tenant farmers",
                "Farmers growing notified crops in notified areas",
                "Compulsory for loanee farmers",
                "Voluntary for non-loanee farmers"
            ],
            benefits=[
                "Comprehensive risk insurance",
                "Low premium rates",
                "Quick settlement of claims",
                "Coverage for all stages of crop cycle"
            ],
            application_process=[
                "Apply through banks, CSCs, or insurance companies",
                "Fill application form",
                "Pay premium amount",
                "Get policy document"
            ],
            required_documents=[
                "Identity proof",
                "Bank account details",
                "Land records",
                "Sowing certificate",
                "Premium payment receipt"
            ],
            application_deadline=None,
            budget_allocation=15695.0,  # 15,695 crores
            beneficiaries_target=55000000,  # 5.5 crore farmers
            states_covered=["All States"],
            crops_covered=["Food crops", "Oilseeds", "Annual commercial/horticultural crops"],
            contact_info={
                "helpline": "1800-180-1551",
                "email": "pmfby@gov.in"
            },
            website_url="https://pmfby.gov.in",
            last_updated=datetime.now()
        ))
        
        return schemes
    
    def _extract_state_from_location(self, location: str) -> str:
        """Extract state name from location string"""
        # Simple state extraction logic
        states = [
            'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
            'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
            'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
            'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu',
            'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal'
        ]
        
        location_lower = location.lower()
        for state in states:
            if state in location_lower:
                return state.title()
        
        return "Unknown"
    
    def _check_farm_size_eligibility(self, scheme: GovernmentScheme, farm_size: float) -> bool:
        """Check if farm size meets scheme eligibility"""
        # Most schemes don't have farm size restrictions
        # This is a simplified check
        return True
    
    def _check_experience_eligibility(self, scheme: GovernmentScheme, experience: str) -> bool:
        """Check if farming experience meets scheme eligibility"""
        # Most schemes don't have experience restrictions
        return True
    
    def _check_additional_criteria(self, scheme: GovernmentScheme, user_profile: Dict[str, Any]) -> float:
        """Check additional eligibility criteria"""
        additional_score = 0.0
        
        # Add score based on scheme type and user profile
        if scheme.scheme_type == SchemeType.LOAN:
            # For loans, consider financial stability indicators
            additional_score += 0.1
        
        if scheme.scheme_type == SchemeType.SUBSIDY:
            # For subsidies, most farmers are eligible
            additional_score += 0.2
        
        return additional_score
    
    def _generate_eligibility_recommendations(self, scheme: GovernmentScheme, 
                                           missing_criteria: List[str], 
                                           user_profile: Dict[str, Any]) -> List[str]:
        """Generate recommendations to improve eligibility"""
        recommendations = []
        
        if missing_criteria:
            recommendations.append("Address the missing criteria to become eligible")
            
            for criteria in missing_criteria:
                if "state" in criteria.lower():
                    recommendations.append("This scheme is not available in your state")
                elif "crop" in criteria.lower():
                    recommendations.append("Consider growing crops covered under this scheme")
                elif "size" in criteria.lower():
                    recommendations.append("Check if you can meet the farm size requirements")
        else:
            recommendations.append("You appear to be eligible for this scheme")
            recommendations.append("Proceed with the application process")
        
        return recommendations
    
    def _estimate_scheme_benefit(self, scheme: GovernmentScheme, user_profile: Dict[str, Any]) -> Optional[float]:
        """Estimate potential benefit from the scheme"""
        try:
            if scheme.scheme_type == SchemeType.SUBSIDY:
                if "PM-KISAN" in scheme.name:
                    return 6000.0  # ₹6,000 per year
                else:
                    # Estimate based on farm size
                    farm_size = user_profile.get('farm_size_acres', 1.0)
                    return farm_size * 2000  # ₹2,000 per acre estimate
            
            elif scheme.scheme_type == SchemeType.LOAN:
                # Estimate loan amount based on farm size
                farm_size = user_profile.get('farm_size_acres', 1.0)
                return farm_size * 50000  # ₹50,000 per acre estimate
            
            elif scheme.scheme_type == SchemeType.INSURANCE:
                # Estimate insurance coverage
                farm_size = user_profile.get('farm_size_acres', 1.0)
                return farm_size * 30000  # ₹30,000 per acre coverage estimate
            
            return None
            
        except Exception as e:
            print(f"Benefit estimation error: {str(e)}")
            return None
    
    def _get_fallback_schemes(self, user_profile: Dict[str, Any], 
                            location: str, crops: List[str]) -> List[EligibilityAssessment]:
        """Get fallback schemes when API is unavailable"""
        fallback_assessments = []
        
        for scheme in self.fallback_schemes[:5]:  # Top 5 schemes
            assessment = self._assess_eligibility(scheme, user_profile, location, crops)
            fallback_assessments.append(assessment)
        
        return fallback_assessments
    
    def _scheme_to_dict(self, scheme: GovernmentScheme) -> Dict[str, Any]:
        """Convert scheme to dictionary for caching"""
        return {
            'scheme_id': scheme.scheme_id,
            'name': scheme.name,
            'description': scheme.description,
            'scheme_type': scheme.scheme_type.value,
            'implementing_agency': scheme.implementing_agency,
            'eligibility_criteria': scheme.eligibility_criteria,
            'benefits': scheme.benefits,
            'application_process': scheme.application_process,
            'required_documents': scheme.required_documents,
            'application_deadline': scheme.application_deadline.isoformat() if scheme.application_deadline else None,
            'budget_allocation': scheme.budget_allocation,
            'beneficiaries_target': scheme.beneficiaries_target,
            'states_covered': scheme.states_covered,
            'crops_covered': scheme.crops_covered,
            'contact_info': scheme.contact_info,
            'website_url': scheme.website_url,
            'last_updated': scheme.last_updated.isoformat()
        }
    
    def _dict_to_scheme(self, data: Dict[str, Any]) -> GovernmentScheme:
        """Convert dictionary to scheme object"""
        return GovernmentScheme(
            scheme_id=data['scheme_id'],
            name=data['name'],
            description=data['description'],
            scheme_type=SchemeType(data['scheme_type']),
            implementing_agency=data['implementing_agency'],
            eligibility_criteria=data['eligibility_criteria'],
            benefits=data['benefits'],
            application_process=data['application_process'],
            required_documents=data['required_documents'],
            application_deadline=datetime.fromisoformat(data['application_deadline']) if data['application_deadline'] else None,
            budget_allocation=data['budget_allocation'],
            beneficiaries_target=data['beneficiaries_target'],
            states_covered=data['states_covered'],
            crops_covered=data['crops_covered'],
            contact_info=data['contact_info'],
            website_url=data['website_url'],
            last_updated=datetime.fromisoformat(data['last_updated'])
        )

# Global government schemes API
government_schemes_api = GovernmentSchemesAPI()
# web_app/main.py
from fastapi import FastAPI, File, UploadFile, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
import os
import uuid
from datetime import datetime
import json
import asyncio
import mimetypes

# Import your existing system
import sys
sys.path.append('..')
# from graph import workflow
# from agents.orchestrator import AgentState
from services.notification_service import notification_service
from services.user_profiles import user_profile_service, UserInteraction
from services.community_features import community_service
from services.real_market_api import real_market_api
from services.auth import auth_service, get_current_user, get_current_active_user, get_current_user_optional, User
from services.task_queue import task_queue
from services.phone_auth import phone_auth_service
from services.contextual_memory import contextual_memory_service
from services.smart_irrigation import smart_irrigation_engine
from services.hybrid_query_processor import hybrid_query_processor
from services.proactive_advisory import proactive_advisory_service


# Import unified AI advisor
from services.unified_ai_advisor import unified_ai_advisor
from services.advanced_reasoning import advanced_reasoning_engine, ReasoningType
from services.government_schemes_api import government_schemes_api
from services.enhanced_voice_processing import voice_processing_service
from services.enhanced_sensor_integration import enhanced_sensor_integration

from typing import Optional, Dict


from typing import Optional


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class PhoneAuthRequest(BaseModel):
    phone_number: str
    country_code: str = "+91"

class OTPVerifyRequest(BaseModel):
    session_id: str
    otp_code: str

class HybridQueryRequest(BaseModel):
    text: Optional[str] = None
    voice_data: Optional[str] = None
    sensor_data: Optional[Dict] = None
    location: Optional[str] = None
    language: str = "hindi"

class UnifiedQueryRequest(BaseModel):
    text: Optional[str] = None
    voice_data: Optional[str] = None
    sensor_data: Optional[Dict] = None
    location: Optional[str] = None
    language: Optional[str] = None

app = FastAPI(title="KrishiMitra", description="AI-Powered Agricultural Advisory")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("web_app/static", exist_ok=True)
os.makedirs("web_app/templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Ensure proper MIME types for CSS
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

# Get base directory for web_app
try:
    web_app_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(web_app_dir, "static")
    template_dir = os.path.join(web_app_dir, "templates")
    
    # Ensure directories exist
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)
    
except Exception as e:
    print(f"Directory setup error: {e}")
    # Fallback to relative paths
    static_dir = "static"
    template_dir = "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

# Mount static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Templates
templates = Jinja2Templates(directory=template_dir)

# Background task for notifications
@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    # Start task queue for background operations
    await task_queue.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks"""
    await task_queue.stop()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main PWA interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/static/styles.css")
async def get_styles():
    """Serve CSS with correct MIME type"""
    try:
        css_path = os.path.join(static_dir, "styles.css")
        if os.path.exists(css_path):
            return FileResponse(
                path=css_path,
                media_type="text/css",
                headers={"Cache-Control": "public, max-age=3600"}
            )
        else:
            return HTMLResponse("/* CSS file not found */", media_type="text/css")
    except Exception as e:
        return HTMLResponse(f"/* CSS error: {e} */", media_type="text/css")

@app.get("/static/app.js")
async def get_app_js():
    """Serve JavaScript with correct MIME type and error handling"""
    try:
        js_path = os.path.join(static_dir, "app.js")
        if os.path.exists(js_path):
            return FileResponse(
                path=js_path,
                media_type="application/javascript",
                headers={"Cache-Control": "public, max-age=3600"}
            )
        else:
            return HTMLResponse(
                "/* JavaScript file not found */", 
                media_type="application/javascript"
            )
    except Exception as e:
        return HTMLResponse(
            f"/* JavaScript error: {e} */", 
            media_type="application/javascript"
        )

# Authentication endpoints
@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = auth_service.create_user(user_data.email, user_data.name, user_data.password)
        access_token = auth_service.create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    user = auth_service.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name
    }

# Phone Authentication Endpoints
@app.post("/api/auth/send-otp")
async def send_otp(request: PhoneAuthRequest):
    """Send OTP to phone number"""
    try:
        result = phone_auth_service.send_otp(request.phone_number, request.country_code)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": "Failed to send OTP"
        }, status_code=500)

@app.post("/api/auth/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP and create/login user"""
    try:
        result = phone_auth_service.verify_otp(request.session_id, request.otp_code)
        
        if result["success"]:
            phone_number = result["phone_number"]
            country_code = result["country_code"]
            
            # Check if user exists with this phone
            user_id = phone_auth_service.get_user_by_phone(phone_number, country_code)
            
            if user_id:
                # Existing user - login
                user = auth_service.get_user_by_id(user_id)
                if user:
                    access_token = auth_service.create_access_token(data={"sub": user.id})
                    return JSONResponse({
                        "success": True,
                        "access_token": access_token,
                        "token_type": "bearer",
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "name": user.name,
                            "phone": phone_number
                        }
                    })
            else:
                # New user - create account
                # For phone auth, use phone as email temporarily
                email = f"{phone_number}@phone.krishimitra.com"
                name = f"Farmer {phone_number[-4:]}"
                
                try:
                    user = auth_service.create_user(email, name, phone_number)  # Use phone as password
                    
                    # Link phone to user
                    phone_auth_service.link_phone_to_user(user.id, phone_number, country_code)
                    
                    access_token = auth_service.create_access_token(data={"sub": user.id})
                    
                    return JSONResponse({
                        "success": True,
                        "access_token": access_token,
                        "token_type": "bearer",
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "name": user.name,
                            "phone": phone_number,
                            "new_user": True
                        }
                    })
                except Exception as e:
                    return JSONResponse({
                        "success": False,
                        "error": "Failed to create user account"
                    }, status_code=500)
        
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": "OTP verification failed"
        }, status_code=500)

# Main Unified Query Processing Endpoint
@app.post("/api/unified-query")
async def process_unified_query(
    text: str = Form(None),
    voice_data: str = Form(None),
    sensor_data: str = Form(None),
    location: str = Form(None),
    language: str = Form("hindi"),
    image: UploadFile = File(None),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Main endpoint for all agricultural queries - ChatGPT-like interface"""
    try:
        user_id = current_user.id if current_user else "anonymous"
        
        # Process voice input if provided
        if voice_data and not text:
            voice_result = await voice_processing_service.process_voice_input(voice_data, language)
            if voice_result.get('success'):
                text = voice_result.get('transcript', '')
        
        # Handle image upload
        image_path = None
        if image and image.filename:
            file_extension = os.path.splitext(image.filename)[1]
            filename = f"{uuid.uuid4()}{file_extension}"
            image_path = os.path.join("uploads", filename)
            
            with open(image_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)
        
        # Parse sensor data if provided
        parsed_sensor_data = None
        if sensor_data:
            try:
                parsed_sensor_data = json.loads(sensor_data)
            except:
                parsed_sensor_data = None
        
        # Prepare inputs for unified processor
        inputs = {
            "text": text,
            "image_path": image_path,
            "voice_data": voice_data,
            "sensor_data": parsed_sensor_data,
            "location": location,
            "language": language
        }
        
        # Check if any input is provided
        if not any([text, image_path, voice_data]):
            return JSONResponse({
                "success": False,
                "error": "Please provide a text query, upload an image, or use voice input"
            }, status_code=400)
        
        # Process unified query
        result = await unified_ai_advisor.process_unified_query(user_id, inputs)
        
        # Clean up uploaded image
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Advanced Reasoning Endpoint
@app.post("/api/advanced-reasoning")
async def process_advanced_reasoning(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Process complex agricultural scenarios with advanced reasoning"""
    try:
        data = await request.json()
        query = data.get('query', '')
        reasoning_type = data.get('reasoning_type', 'trade_off_analysis')
        
        user_id = current_user.id if current_user else "anonymous"
        
        # Get user context
        user_context = {}
        if current_user:
            profile = user_profile_service.get_profile(current_user.id)
            if profile:
                user_context['profile'] = profile.to_dict()
            
            farming_context = contextual_memory_service.get_farming_context(current_user.id)
            if farming_context:
                user_context['farming'] = {
                    'location': farming_context.location,
                    'primary_crops': farming_context.primary_crops,
                    'farm_size_acres': farming_context.farm_size_acres,
                    'soil_type': farming_context.soil_type,
                    'irrigation_method': farming_context.irrigation_method
                }
        
        # Collect relevant data
        context_data = {'user_context': user_context}
        
        # Perform advanced reasoning
        reasoning_result = await advanced_reasoning_engine.analyze_complex_scenario(
            query, context_data, ReasoningType(reasoning_type)
        )
        
        return JSONResponse({
            'success': True,
            'reasoning_type': reasoning_result.reasoning_type.value,
            'primary_recommendation': reasoning_result.primary_recommendation,
            'confidence_score': reasoning_result.confidence_score,
            'reasoning_steps': [
                {
                    'step_number': step.step_number,
                    'description': step.description,
                    'analysis': step.analysis,
                    'confidence': step.confidence
                }
                for step in reasoning_result.reasoning_steps
            ],
            'trade_offs': reasoning_result.trade_offs,
            'risk_factors': reasoning_result.risk_factors,
            'expected_outcomes': reasoning_result.expected_outcomes,
            'alternative_strategies': reasoning_result.alternative_strategies,
            'implementation_timeline': reasoning_result.implementation_timeline
        })
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)

# Government Schemes Endpoint
@app.get("/api/government-schemes")
async def get_government_schemes(
    current_user: User = Depends(get_current_active_user)
):
    """Get applicable government schemes for the user"""
    try:
        # Get user profile
        profile = user_profile_service.get_profile(current_user.id)
        if not profile:
            return JSONResponse({
                'success': False,
                'error': 'Please complete your profile first'
            }, status_code=400)
        
        # Get farming context
        farming_context = contextual_memory_service.get_farming_context(current_user.id)
        
        user_profile_dict = {
            'farm_size_acres': profile.farm_size.value if hasattr(profile.farm_size, 'value') else str(profile.farm_size),
            'farming_experience': profile.experience.value if hasattr(profile.experience, 'value') else str(profile.experience),
            'soil_type': profile.soil_type,
            'irrigation_type': profile.irrigation_type
        }
        
        location = farming_context.location if farming_context else profile.location
        crops = farming_context.primary_crops if farming_context else profile.primary_crops
        
        # Get applicable schemes
        schemes = government_schemes_api.get_applicable_schemes(
            user_profile_dict, location, crops
        )
        
        return JSONResponse({
            'success': True,
            'schemes': [
                {
                    'scheme_id': scheme.scheme.scheme_id,
                    'name': scheme.scheme.name,
                    'description': scheme.scheme.description,
                    'scheme_type': scheme.scheme.scheme_type.value,
                    'implementing_agency': scheme.scheme.implementing_agency,
                    'eligibility_status': scheme.status.value,
                    'eligibility_score': scheme.eligibility_score,
                    'matching_criteria': scheme.matching_criteria,
                    'missing_criteria': scheme.missing_criteria,
                    'recommendations': scheme.recommendations,
                    'estimated_benefit': scheme.estimated_benefit,
                    'benefits': scheme.scheme.benefits,
                    'application_process': scheme.scheme.application_process,
                    'required_documents': scheme.scheme.required_documents,
                    'contact_info': scheme.scheme.contact_info,
                    'website_url': scheme.scheme.website_url
                }
                for scheme in schemes
            ]
        })
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)

# Voice Processing Endpoint
@app.post("/api/voice/process")
async def process_voice_input(
    audio_data: str = Form(...),
    language: str = Form("hi"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Process voice input and convert to text"""
    try:
        result = await voice_processing_service.process_voice_input(audio_data, language)
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)

# Enhanced Sensor Data Endpoint
@app.get("/api/sensors/{farm_id}")
async def get_sensor_data(
    farm_id: str,
    sensor_types: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get real-time sensor data for a farm"""
    try:
        # Parse sensor types if provided
        requested_sensor_types = None
        if sensor_types:
            from services.enhanced_sensor_integration import SensorType
            requested_sensor_types = [SensorType(s.strip()) for s in sensor_types.split(',')]
        
        # Get sensor data
        sensor_data = await enhanced_sensor_integration.get_real_sensor_data(
            farm_id, requested_sensor_types
        )
        
        return JSONResponse(sensor_data)
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)

# Contextual Memory Endpoints
@app.post("/api/context/farming")
async def create_farming_context(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Create or update farming context"""
    try:
        data = await request.json()
        
        # Check if context exists
        existing_context = contextual_memory_service.get_farming_context(current_user.id)
        
        if existing_context:
            # Update existing context
            success = contextual_memory_service.update_farming_context(current_user.id, data)
            return JSONResponse({"success": success})
        else:
            # Create new context
            context = contextual_memory_service.create_farming_context(current_user.id, data)
            return JSONResponse({
                "success": True,
                "context_id": context.user_id
            })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/context/farming")
async def get_farming_context(current_user: User = Depends(get_current_active_user)):
    """Get farming context"""
    try:
        context = contextual_memory_service.get_farming_context(current_user.id)
        
        if context:
            return JSONResponse({
                "success": True,
                "context": {
                    "location": context.location,
                    "primary_crops": context.primary_crops,
                    "secondary_crops": context.secondary_crops,
                    "farm_size_acres": context.farm_size_acres,
                    "soil_type": context.soil_type,
                    "irrigation_method": context.irrigation_method,
                    "last_irrigation": context.last_irrigation.isoformat() if context.last_irrigation else None,
                    "irrigation_frequency_days": context.irrigation_frequency_days,
                    "crop_stages": {k: v.value for k, v in context.crop_stages.items()},
                    "farming_experience": context.farming_experience,
                    "preferred_language": context.preferred_language
                }
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "No farming context found"
            }, status_code=404)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# User Profile Endpoints
@app.post("/api/profile")
async def create_profile(request: Request, current_user: User = Depends(get_current_active_user)):
    """Create user profile"""
    try:
        data = await request.json()
        data['user_id'] = current_user.id  # Use authenticated user ID
        profile = user_profile_service.create_profile(data)
        return JSONResponse({"success": True, "profile": profile.to_dict()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get user profile"""
    try:
        profile = user_profile_service.get_profile(current_user.id)
        if profile:
            return JSONResponse({"success": True, "profile": profile.to_dict()})
        else:
            return JSONResponse({"success": False, "error": "Profile not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    """Get user dashboard data"""
    try:
        dashboard_data = user_profile_service.get_user_dashboard_data(current_user.id)
        return JSONResponse({"success": True, "data": dashboard_data})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# Community Endpoints
@app.get("/api/community/posts")
async def get_community_posts(
    post_type: str = None,
    location: str = None,
    limit: int = 20,
    offset: int = 0
):
    """Get community posts"""
    try:
        filters = {}
        if post_type:
            filters['post_type'] = post_type
        if location:
            filters['location'] = location
        
        posts = community_service.get_posts(filters, limit, offset)
        return JSONResponse({"success": True, "posts": posts})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/community/posts")
async def create_post(request: Request, current_user: User = Depends(get_current_active_user)):
    """Create a community post"""
    try:
        data = await request.json()
        user_id = current_user.id
        post = community_service.create_post(user_id, data)
        return JSONResponse({"success": True, "post": post.to_dict()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/community/posts/{post_id}")
async def get_post_details(post_id: str, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get detailed post information"""
    try:
        user_id = current_user.id if current_user else None
        post = community_service.get_post_details(post_id, user_id)
        if post:
            return JSONResponse({"success": True, "post": post})
        else:
            return JSONResponse({"success": False, "error": "Post not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/community/posts/{post_id}/comments")
async def add_comment(post_id: str, request: Request, current_user: User = Depends(get_current_active_user)):
    """Add comment to a post"""
    try:
        data = await request.json()
        user_id = current_user.id
        content = data.get('content', '')
        
        comment = community_service.add_comment(user_id, post_id, content)
        return JSONResponse({"success": True, "comment": comment.to_dict()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/community/posts/{post_id}/like")
async def like_post(post_id: str, request: Request, current_user: User = Depends(get_current_active_user)):
    """Like or unlike a post"""
    try:
        data = await request.json()
        user_id = current_user.id
        
        liked = community_service.like_post(user_id, post_id)
        return JSONResponse({"success": True, "liked": liked})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/community/trending")
async def get_trending_posts(days: int = 7, limit: int = 10):
    """Get trending posts"""
    try:
        posts = community_service.get_trending_posts(days, limit)
        return JSONResponse({"success": True, "posts": posts})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# Market Data Endpoints
@app.get("/api/market/prices")
async def get_market_prices(crops: str = "", location: str = ""):
    """Get current market prices - real data only"""
    try:
        crop_list = [c.strip() for c in crops.split(",")] if crops else ["Rice", "Wheat"]
        prices = real_market_api.get_consolidated_prices(crop_list, location)
        
        if prices:
            return JSONResponse({"success": True, "prices": prices})
        else:
            return JSONResponse({
                "success": False, 
                "error": "Market data not available. Please check your API configuration or try again later."
            })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/market/trends")
async def get_price_trends(crops: str = "", days: int = 30):
    """Get price trends - real data only"""
    try:
        crop_list = [c.strip() for c in crops.split(",")] if crops else ["Rice", "Wheat"]
        trends = real_market_api.get_price_trends(crop_list, days)
        
        if trends:
            return JSONResponse({"success": True, "trends": trends})
        else:
            return JSONResponse({
                "success": False,
                "error": "Price trend data not available. Insufficient historical data."
            })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# Notification Endpoints
@app.get("/api/notifications")
async def get_notifications(current_user: User = Depends(get_current_active_user), limit: int = 20):
    """Get user notifications"""
    try:
        notifications = notification_service.get_user_notifications(current_user.id, limit)
        return JSONResponse({"success": True, "notifications": notifications})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_active_user)):
    """Mark notification as read"""
    try:
        success = notification_service.mark_notification_read(current_user.id, notification_id)
        return JSONResponse({"success": success})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/manifest.json")
async def manifest():
    """PWA manifest"""
    with open("web_app/static/manifest.json", "r") as f:
        import json
        return json.load(f)

@app.get("/api/status")
async def system_status():
    """System status endpoint - real data availability"""
    try:
        # Check database connection
        from database.db import get_connection
        conn = get_connection()
        conn.close()
        db_status = "healthy"
    except Exception:
        db_status = "error"
    
    # Check API keys
    import os
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    weather_configured = bool(os.getenv("OPENWEATHER_API_KEY"))
    enam_configured = bool(os.getenv("ENAM_API_KEY"))
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "gemini_api": "configured" if gemini_configured else "missing",
            "weather_api": "configured" if weather_configured else "missing",
            "market_api": "configured" if enam_configured else "missing",
            "phone_auth": "available",
            "contextual_memory": "available",
            "smart_irrigation": "available"
        },
        "version": "4.0.0",
        "features": {
            "unified_ai_chat": True,
            "personalized_responses": True,
            "real_time_data_only": True,
            "contextual_memory": True,
            "user_profiles": True,
            "community": True,
            "notifications": True,
            "real_market_data": enam_configured,
            "offline_support": True,
            "phone_authentication": True,
            "smart_irrigation": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
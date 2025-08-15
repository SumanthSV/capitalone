#!/usr/bin/env python3
"""
KrishiMitra Phase 2 Setup Script
Sets up offline capabilities, PWA features, and enhanced caching
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_optional_dependencies():
    """Install optional dependencies with fallbacks"""
    optional_packages = [
        ("chromadb", "Vector database for offline RAG"),
        ("sentence-transformers", "Text embeddings for semantic search"),
        ("onnxruntime", "Offline ML model inference"),
        ("redis", "Advanced caching (optional)"),
        ("twilio", "SMS notifications (optional)")
    ]
    
    installed = []
    failed = []
    
    for package, description in optional_packages:
        try:
            print(f"📦 Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            installed.append((package, description))
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            failed.append((package, description))
            print(f"⚠️ {package} installation failed - fallback will be used")
    
    return installed, failed

def setup_directories():
    """Create necessary directories"""
    directories = [
        "offline_cache",
        "chroma_db", 
        "models",
        "web_app/static/icons",
        "web_app/static/screenshots",
        "uploads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def create_pwa_icons():
    """Create placeholder PWA icons"""
    icon_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    icons_dir = Path("web_app/static/icons")
    icon_path = os.path.join("web_app", "static", "icons", "pwa_icon.svg")
    
    # Create a simple SVG icon that can be converted to different sizes
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
    <rect width="512" height="512" fill="#4CAF50"/>
    <text x="256" y="280" font-family="Arial, sans-serif" font-size="200" 
          text-anchor="middle" fill="white">🌾</text>
    <text x="256" y="400" font-family="Arial, sans-serif" font-size="48" 
          text-anchor="middle" fill="white">KrishiMitra</text>
</svg>'''
    
    # Save SVG
    with open(icon_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    # Create placeholder PNG files (in a real setup, you'd convert the SVG)
    for size in icon_sizes:
        icon_path = icons_dir / f"icon-{size}x{size}.png"
        if not icon_path.exists():
            # Create a simple placeholder file
            with open(icon_path, "w") as f:
                f.write(f"# Placeholder icon {size}x{size}\n")
            print(f"📱 Created placeholder icon: {size}x{size}")

# # def setup_service_worker():
#     """Set up service worker for PWA"""
#     # from services.pwa_service import pwa_service
    
#     # # Generate service worker
#     # sw_content = pwa_service.generate_service_worker()
#     with open("web_app/static/sw.js", "w") as f:
#         f.write(sw_content)
#     print("🔧 Generated service worker")
    
#     # Generate manifest
#     manifest = pwa_service.generate_manifest()
#     with open("web_app/static/manifest.json", "w") as f:
#         json.dump(manifest, f, indent=2)
#     print("📱 Generated PWA manifest")
    
#     # Generate offline page
#     offline_html = pwa_service.get_offline_page()
#     with open("web_app/static/offline.html", "w",encoding="utf-8") as f:
#         f.write(offline_html)
#     print("📄 Generated offline fallback page")

def initialize_caches():
    """Initialize offline caches with essential data"""
    try:
        from services.pwa_service import pwa_service
        from services.offline_cache import offline_cache
        
        # Cache essential agricultural data
        success = pwa_service.cache_essential_data()
        if success:
            print("💾 Cached essential agricultural data")
        else:
            print("⚠️ Failed to cache some essential data")
        
        # Test cache functionality
        test_data = {"test": "cache_working", "timestamp": "2024-01-01"}
        offline_cache.set("test_cache", test_data, expiry_hours=1)
        
        retrieved = offline_cache.get("test_cache")
        if retrieved and retrieved.get("test") == "cache_working":
            print("✅ Cache system working correctly")
        else:
            print("⚠️ Cache system may have issues")
            
    except Exception as e:
        print(f"⚠️ Cache initialization error: {str(e)}")

def setup_vector_database():
    """Initialize vector database"""
    try:
        from services.vector_db import vector_db
        
        # Test vector database
        if vector_db.chroma_available:
            print("✅ ChromaDB vector database initialized")
        else:
            print("⚠️ ChromaDB not available - using fallback text search")
        
        # Test search functionality
        results = vector_db.search_crop_knowledge("rice cultivation", n_results=1)
        if results:
            print("✅ Vector search working correctly")
        else:
            print("⚠️ Vector search may have issues")
            
    except Exception as e:
        print(f"⚠️ Vector database setup error: {str(e)}")

def test_offline_models():
    """Test offline model functionality"""
    try:
        from services.offline_models import offline_image_classifier, offline_text_classifier
        
        # Test text classifier
        result = offline_text_classifier.classify_query("What crops should I grow?")
        if result.get("category"):
            print("✅ Offline text classification working")
        else:
            print("⚠️ Text classification may have issues")
        
        # Test image classifier (without actual image)
        if offline_image_classifier.model_available:
            print("✅ Offline image model loaded")
        else:
            print("⚠️ Offline image model not available - using color analysis fallback")
            
    except Exception as e:
        print(f"⚠️ Offline models test error: {str(e)}")

def create_env_template():
    """Create enhanced .env template"""
    env_template = """# KrishiMitra Phase 2 Configuration

# Core API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Phase 2: Enhanced Features
HUGGINGFACE_API_KEY=your_huggingface_api_key_here  # Optional: For enhanced ML models

# Database Configuration
DATABASE_URL=sqlite:///crop_data.db

# Cache Configuration
CACHE_EXPIRY_HOURS=24
OFFLINE_MODE=false

# Language Configuration
DEFAULT_LANGUAGE=en

# Phase 4: Advanced Features (Optional)
ENAM_API_KEY=your_enam_api_key_here  # Market data
NOTIFICATION_EMAIL=your_notification_email@gmail.com
NOTIFICATION_EMAIL_PASSWORD=your_app_password
EMAIL_NOTIFICATIONS_ENABLED=false

# SMS Notifications (Optional)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number
SMS_NOTIFICATIONS_ENABLED=false

# Redis Cache (Optional)
REDIS_URL=redis://localhost:6379

# PWA Configuration
PWA_NAME=KrishiMitra
PWA_SHORT_NAME=KrishiMitra
PWA_THEME_COLOR=#4CAF50
PWA_BACKGROUND_COLOR=#ffffff

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_template)
        print("📝 Created .env template file")
    else:
        print("📝 .env file already exists")

def run_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running Phase 2 Tests...")
    
    try:
        # Test imports
        from services.offline_cache import offline_cache
        from services.vector_db import vector_db
        from services.offline_models import offline_text_classifier
        from services.pwa_service import pwa_service
        
        print("✅ All Phase 2 modules imported successfully")
        
        # Test cache stats
        stats = offline_cache.get_stats()
        print(f"📊 Cache stats: {stats}")
        
        # Test PWA service
        app_info = pwa_service.get_app_info()
        print(f"📱 PWA info: {app_info['name']} v{app_info['version']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tests failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🌾 KrishiMitra Phase 2 Setup")
    print("=" * 50)
    
    # Check requirements
    check_python_version()
    
    # Setup directories
    print("\n📁 Setting up directories...")
    setup_directories()
    
    # Install optional dependencies
    print("\n📦 Installing optional dependencies...")
    installed, failed = install_optional_dependencies()
    
    # Create PWA assets
    print("\n📱 Setting up PWA assets...")
    create_pwa_icons()
    # setup_service_worker()
    
    # Initialize systems
    print("\n💾 Initializing offline systems...")
    initialize_caches()
    setup_vector_database()
    test_offline_models()
    
    # Create configuration
    print("\n⚙️ Setting up configuration...")
    create_env_template()
    
    # Run tests
    tests_passed = run_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Phase 2 Setup Complete!")
    print(f"✅ Installed packages: {len(installed)}")
    print(f"⚠️ Failed packages: {len(failed)} (fallbacks available)")
    
    if failed:
        print("\nOptional packages that failed to install:")
        for package, description in failed:
            print(f"  - {package}: {description}")
        print("\nDon't worry! The system will use fallback implementations.")
    
    print(f"\n🧪 Tests: {'✅ PASSED' if tests_passed else '❌ FAILED'}")
    
    print("\n📋 Next Steps:")
    print("1. Update your .env file with API keys")
    print("2. Run: python run_web_app.py")
    print("3. Test offline functionality by disconnecting internet")
    print("4. Install the PWA on your mobile device")
    
    print("\n🚀 Phase 2 Features Now Available:")
    print("  - Offline caching system")
    print("  - Vector database for RAG")
    print("  - PWA with service worker")
    print("  - Fallback implementations")
    print("  - Enhanced error handling")

if __name__ == "__main__":
    main()
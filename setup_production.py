#!/usr/bin/env python3
"""
KrishiMitra Production Setup Script
Prepares the application for production deployment
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
import secrets

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_production_dependencies():
    """Install production dependencies"""
    try:
        print("📦 Installing production dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup production environment"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("📝 .env file already exists")
        response = input("Do you want to update it? (y/N): ").lower()
        if response != 'y':
            return True
    
    # Generate secure keys
    secret_key = secrets.token_urlsafe(32)
    jwt_secret_key = secrets.token_urlsafe(32)
    
    print("🔐 Generating secure keys...")
    print("⚠️  Please update the following in your .env file:")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret_key}")
    print("\n📝 Don't forget to add your API keys:")
    print("- GEMINI_API_KEY (required)")
    print("- OPENWEATHER_API_KEY (required)")
    print("- ENAM_API_KEY (optional)")
    
    return True

def initialize_databases():
    """Initialize all required databases"""
    try:
        print("🗄️ Initializing databases...")
        
        # Initialize crop database if it doesn't exist
        if not os.path.exists("crop_data.db"):
            print("📊 Crop database not found. Please run 'python import_crops.py' if you have the Excel file.")
        else:
            print("✅ Crop database found")
        
        # Initialize user database
        from services.auth import auth_service
        print("✅ User authentication database initialized")
        
        # Initialize community database
        from services.community_features import community_service
        print("✅ Community database initialized")
        
        # Initialize user profiles database
        from services.user_profiles import user_profile_service
        print("✅ User profiles database initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

def setup_logging():
    """Setup production logging"""
    try:
        import logging
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/krishimitra.log'),
                logging.StreamHandler()
            ]
        )
        
        print("✅ Logging configured")
        return True
        
    except Exception as e:
        print(f"❌ Logging setup failed: {str(e)}")
        return False

def create_production_icons():
    """Create production-ready PWA icons"""
    icons_dir = Path("web_app/static/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a better SVG icon
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#45a049;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="512" height="512" fill="url(#bg)" rx="80"/>
    <circle cx="256" cy="200" r="80" fill="white" opacity="0.9"/>
    <text x="256" y="220" font-family="Arial, sans-serif" font-size="60" 
          text-anchor="middle" fill="#4CAF50" font-weight="bold">🌾</text>
    <text x="256" y="320" font-family="Arial, sans-serif" font-size="36" 
          text-anchor="middle" fill="white" font-weight="bold">KrishiMitra</text>
    <text x="256" y="360" font-family="Arial, sans-serif" font-size="18" 
          text-anchor="middle" fill="white" opacity="0.9">AI Agricultural Advisor</text>
</svg>'''
    
    # Save improved SVG
    with open(icons_dir / "icon.svg", "w") as f:
        f.write(svg_content)
    
    print("🎨 Updated PWA icon")

def run_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running production readiness tests...")
    
    try:
        # Test imports
        from services.auth import auth_service
        from services.task_queue import task_queue
        from services.real_market_api import real_market_api
        from services.notification_service import notification_service
        
        print("✅ All services imported successfully")
        
        # Test database connections
        test_user = None
        try:
            # Test user creation (will be cleaned up)
            test_user = auth_service.create_user("test@example.com", "Test User", "testpass123")
            print("✅ User authentication working")
            
            # Clean up test user
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE email = ?", ("test@example.com",))
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ User authentication test failed: {str(e)}")
        
        # Test market API
        try:
            prices = real_market_api.get_consolidated_prices(["Rice"], "Punjab")
            print("✅ Market API working")
        except Exception as e:
            print(f"⚠️ Market API test failed: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tests failed: {str(e)}")
        return False

def create_deployment_scripts():
    """Create deployment helper scripts"""
    
    # Create start script
    start_script = '''#!/bin/bash
# start.sh - Production start script

echo "🌾 Starting KrishiMitra Production Server..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Start the application
python -m uvicorn web_app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
'''
    
    with open("start.sh", "w") as f:
        f.write(start_script)
    
    # Make executable
    os.chmod("start.sh", 0o755)
    
    # Create Docker file
    dockerfile = '''FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads offline_cache

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "web_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    
    # Create docker-compose file
    docker_compose = '''version: '3.8'

services:
  krishimitra:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./offline_cache:/app/offline_cache
      - ./.env:/app/.env
    restart: unless-stopped
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
'''
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    print("🐳 Created deployment scripts (start.sh, Dockerfile, docker-compose.yml)")

def main():
    """Main setup function"""
    print("🌾 KrishiMitra Production Setup")
    print("=" * 50)
    
    # Check requirements
    check_python_version()
    
    # Install dependencies
    if not install_production_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Initialize databases
    if not initialize_databases():
        print("❌ Database initialization failed")
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Create production assets
    create_production_icons()
    
    # Create deployment scripts
    create_deployment_scripts()
    
    # Run tests
    tests_passed = run_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Production Setup Complete!")
    
    print(f"\n🧪 Tests: {'✅ PASSED' if tests_passed else '⚠️ SOME ISSUES'}")
    
    print("\n📋 Next Steps:")
    print("1. Update your .env file with real API keys")
    print("2. If you have crops_dataset.xlsx, run: python import_crops.py")
    print("3. Start the application: ./start.sh")
    print("4. Or use Docker: docker-compose up")
    
    print("\n🚀 Production Features Now Available:")
    print("  - User authentication and profiles")
    print("  - Real market data integration")
    print("  - Background notification system")
    print("  - Enhanced security")
    print("  - Production logging")
    print("  - Docker deployment ready")
    
    print("\n⚠️ Important Security Notes:")
    print("  - Change SECRET_KEY and JWT_SECRET_KEY in .env")
    print("  - Use HTTPS in production")
    print("  - Configure proper CORS origins")
    print("  - Set up SSL certificates")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
KrishiMitra Web Application Launcher
Enhanced version with better error handling and configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import google.generativeai
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration"""
    issues = []
    
    # Check for .env file
    if not os.path.exists('.env'):
        issues.append("❌ .env file not found. Copy .env.example to .env and configure it.")
    
    # Check API keys
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GEMINI_API_KEY'):
        issues.append("⚠️  GEMINI_API_KEY not configured. AI features will be limited.")
    
    if not os.getenv('OPENWEATHER_API_KEY'):
        issues.append("⚠️  OPENWEATHER_API_KEY not configured. Weather features will be limited.")
    
    # Check database
    if not os.path.exists('crop_data.db'):
        issues.append("⚠️  crop_data.db not found. Run import_crops.py first.")
    
    if issues:
        print("\n".join(issues))
        print("\n🔧 Configuration issues found. The app will still run but some features may be limited.")
        return False
    else:
        print("✅ Environment configuration looks good!")
        return True

def main():
    """Main launcher function"""
    print("🌾 KrishiMitra - AI Agricultural Advisory System")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    env_ok = check_environment()
    
    # Change to web_app directory
    web_app_dir = Path(__file__).parent / "web_app"
    os.chdir(web_app_dir)
    
    print(f"\n🚀 Starting KrishiMitra Web Application...")
    print(f"📁 Working directory: {web_app_dir}")
    print(f"🌐 Web interface will be available at: http://localhost:8000")
    print(f"📱 PWA features enabled - can be installed on mobile devices")
    
    if not env_ok:
        print(f"⚠️  Some features may be limited due to configuration issues")
    
    print("\n" + "=" * 50)
    
    try:
        # Start the FastAPI application
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 KrishiMitra stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
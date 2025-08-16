#!/usr/bin/env python3
"""
API Keys Setup Script for KrishiMitra
Helps users configure their API keys properly
"""

import os
import sys
from dotenv import load_dotenv

def check_api_keys():
    """Check and validate API keys"""
    load_dotenv()
    
    print("🌾 KrishiMitra API Keys Configuration Check")
    print("=" * 50)
    
    api_keys = {
        'GEMINI_API_KEY': {
            'value': os.getenv('GEMINI_API_KEY'),
            'required': True,
            'url': 'https://makersuite.google.com/app/apikey',
            'description': 'Google Gemini AI API for intelligent responses'
        },
        'OPENWEATHER_API_KEY': {
            'value': os.getenv('OPENWEATHER_API_KEY'),
            'required': True,
            'url': 'https://openweathermap.org/api',
            'description': 'OpenWeather API for weather data'
        },
        'ENAM_API_KEY': {
            'value': os.getenv('ENAM_API_KEY'),
            'required': False,
            'url': 'https://data.gov.in/',
            'description': 'e-NAM API for real market prices (optional but recommended)'
        }
    }
    
    all_configured = True
    
    for key_name, key_info in api_keys.items():
        value = key_info['value']
        required = key_info['required']
        
        print(f"\n{key_name}:")
        
        if not value:
            status = "❌ NOT SET"
            all_configured = False
        elif value.startswith('your_') and value.endswith('_here'):
            status = "⚠️  PLACEHOLDER - NEEDS REPLACEMENT"
            all_configured = False
        elif len(value) < 10:
            status = "⚠️  TOO SHORT - LIKELY INVALID"
            all_configured = False
        else:
            status = "✅ CONFIGURED"
            if not required:
                status += " (OPTIONAL)"
        
        print(f"  Status: {status}")
        print(f"  Description: {key_info['description']}")
        
        if status.startswith('❌') or status.startswith('⚠️'):
            print(f"  🔗 Get your key from: {key_info['url']}")
            if required:
                print(f"  ⚠️  This key is REQUIRED for core functionality")
    
    print("\n" + "=" * 50)
    
    if all_configured:
        print("🎉 All API keys are properly configured!")
        print("✅ Your KrishiMitra application should work with real-time data")
    else:
        print("❌ Some API keys need attention")
        print("\n📋 NEXT STEPS:")
        print("1. Get the missing API keys from the URLs provided above")
        print("2. Open your .env file")
        print("3. Replace the placeholder values with your actual API keys")
        print("4. Restart the application")
        print("\n💡 TIP: Free tiers are available for all these services!")
    
    return all_configured

def setup_env_file():
    """Setup .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ .env file created from .env.example")
            print("📝 Please edit .env file and add your actual API keys")
        else:
            print("❌ .env.example file not found")
            return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 KrishiMitra API Keys Setup")
    print("This script will help you configure your API keys for real-time data\n")
    
    # Setup .env file
    if not setup_env_file():
        print("❌ Could not setup .env file")
        sys.exit(1)
    
    # Check API keys
    configured = check_api_keys()
    
    if not configured:
        print(f"\n🔧 QUICK SETUP GUIDE:")
        print(f"1. Visit https://makersuite.google.com/app/apikey")
        print(f"2. Create a Google account if needed")
        print(f"3. Generate a new API key")
        print(f"4. Copy the key and paste it in your .env file")
        print(f"5. Repeat for OpenWeather: https://openweathermap.org/api")
        print(f"6. Run this script again to verify")
        
        print(f"\n💰 COST INFORMATION:")
        print(f"- Gemini API: Free tier includes 15 requests per minute")
        print(f"- OpenWeather API: Free tier includes 1000 calls per day")
        print(f"- e-NAM API: Free government data")
    
    print(f"\n🌾 Once configured, your KrishiMitra will have:")
    print(f"✅ Real-time weather data")
    print(f"✅ Live market prices")
    print(f"✅ Intelligent crop advice")
    print(f"✅ Personalized recommendations")

if __name__ == "__main__":
    main()
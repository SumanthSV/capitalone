# 🔑 API Keys Setup Guide for KrishiMitra

## Quick Start - Get Your API Keys

### 1. 🤖 Google Gemini API Key (REQUIRED)

**What it does:** Powers the AI responses and image analysis

**How to get it:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Paste it in your `.env` file as `GEMINI_API_KEY=your_actual_key_here`

**Cost:** FREE - 15 requests per minute, 1500 requests per day

### 2. 🌤️ OpenWeather API Key (REQUIRED)

**What it does:** Provides real-time weather data and forecasts

**How to get it:**
1. Go to [OpenWeather API](https://openweathermap.org/api)
2. Click "Sign Up" and create a free account
3. Go to "API Keys" section in your dashboard
4. Copy the default API key (or create a new one)
5. Paste it in your `.env` file as `OPENWEATHER_API_KEY=your_actual_key_here`

**Cost:** FREE - 1000 calls per day, 60 calls per minute

### 3. 📊 e-NAM API Key (OPTIONAL)

**What it does:** Provides real-time market prices from government sources

**How to get it:**
1. Go to [Data.gov.in](https://data.gov.in/)
2. Search for "e-NAM" or "market prices"
3. Register for API access
4. Get your API key from the dashboard
5. Paste it in your `.env` file as `ENAM_API_KEY=your_actual_key_here`

**Cost:** FREE - Government data

## 🚀 Quick Setup Commands

```bash
# 1. Copy the environment template
cp .env.example .env

# 2. Check your current API key status
python setup_api_keys.py

# 3. Edit your .env file with actual keys
nano .env

# 4. Verify configuration
python setup_api_keys.py

# 5. Start the application
python run_web_app.py
```

## 🔧 Troubleshooting

### Problem: "API key not found"
**Solution:** Make sure your `.env` file exists and contains the API keys

### Problem: "401 Unauthorized"
**Solution:** Your API key is invalid. Get a new one from the provider

### Problem: "No data available"
**Solution:** The API might be down. The app will use intelligent fallbacks

### Problem: "Rate limit exceeded"
**Solution:** You've exceeded the free tier limits. Wait or upgrade your plan

## 🎯 Testing Your Setup

After setting up your API keys, test them:

```bash
# Test the application
python run_web_app.py

# Open http://localhost:8000
# Try asking: "What's the weather in Punjab?"
# Try asking: "What's the rice price today?"
```

## 💡 Pro Tips

1. **Keep your API keys secret** - Never share them publicly
2. **Monitor your usage** - Check your API dashboards regularly
3. **Set up billing alerts** - Get notified before hitting limits
4. **Use caching** - KrishiMitra caches data to reduce API calls

## 🆘 Need Help?

If you're still having issues:

1. Run `python setup_api_keys.py` to diagnose problems
2. Check the logs in `krishimitra.log`
3. Verify your internet connection
4. Make sure your API keys are active and not expired

## 🌟 What You'll Get

Once properly configured, KrishiMitra will provide:
- ✅ Real-time weather forecasts
- ✅ Live market prices
- ✅ Intelligent crop advice
- ✅ Personalized recommendations
- ✅ Disease detection from photos
- ✅ Profit optimization guidance

**Your farmers will get accurate, real-time agricultural intelligence! 🚀**
# services/real_market_api.py
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from services.offline_cache import offline_cache
from services.error_handler import error_handler, APIError
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Union


class RealMarketAPI:
    """Real market API integration with multiple data sources - NO MOCK DATA"""
    
    def __init__(self):
        self.enam_base_url = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
        self.agmarknet_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"
        self.cache_expiry = 6  # 6 hours for market data
    
    def get_enam_prices(self, commodity: str, state: str = "") -> Optional[List[Dict]]:
        """Get prices from e-NAM - returns None if unavailable"""
        try:
            cache_key = f"enam_prices_{commodity}_{state}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                return cached_data
            
            enam_api_key = os.getenv("ENAM_API_KEY")
            if not enam_api_key:
                print("e-NAM API key not found")
                return None
            
            # Correct API params
            params = {
                "api-key": enam_api_key,
                "format": "json",
                "filters[Commodity]": commodity,
                "filters[State]": state,
                "limit": 100
            }
            
            response = requests.get(
                self.enam_base_url,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = self._parse_enam_data(data)
                if prices:
                    offline_cache.set(cache_key, prices, self.cache_expiry)
                    return prices
            return None   
        
        except Exception as e:
            print(f"e-NAM API error: {str(e)}")
            return None
        

    def get_agmarknet_prices(self, commodity_id: str, state_id: str, market_id: str = "0",
                             start_date: str = "01-Jan-2020", end_date: str = "01-Jan-2025",
                             commodity_name: str = "", state_name: str = "") -> Optional[List[Dict]]:
        """Get prices from AgMarkNet - returns None if unavailable"""
        try:
            cache_key = f"agmarknet_prices_{commodity_id}_{state_id}_{market_id}"
            cached_data = self._get_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Build URL for direct browser access
            url = (
                f"{self.agmarknet_url}?Tx_Commodity={commodity_id}"
                f"&Tx_State={state_id}&Tx_Market={market_id}"
                f"&DateFrom={start_date}&DateTo={end_date}"
                f"&Fr_Date={start_date}&To_Date={end_date}&Tx_Trend=2"
                f"&Tx_CommodityHead={commodity_name}&Tx_StateHead={state_name}"
                f"&Tx_DistrictHead=--Select--&Tx_MarketHead=--Select--"
            )

            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"AgMarkNet request failed: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"id": "ctl00_ContentPlaceHolder1_GridView1"})
            if not table:
                return None

            prices = []
            rows = table.find_all("tr")[1:]  # skip header
            for row in rows:
                cols = row.find_all("td")
                prices.append({
                    "commodity": cols[0].text.strip(),
                    "market": cols[1].text.strip(),
                    "variety": cols[2].text.strip(),
                    "min_price": cols[3].text.strip(),
                    "max_price": cols[4].text.strip(),
                    "modal_price": cols[5].text.strip(),
                    "date": cols[6].text.strip(),
                })

            if prices:
                self._set_cache(cache_key, prices)
                return prices

            return None

        except Exception as e:
            print(f"AgMarkNet error: {str(e)}")
            return None
    
    def get_consolidated_prices(self, crops: List[str], location: str) -> Optional[List[Dict]]:
        """Get consolidated prices from multiple sources - returns None if unavailable"""
        try:
            cache_key = f"consolidated_prices_{'-'.join(crops)}_{location}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                return cached_data
            
            all_prices = []
            
            for crop in crops:
                # Try e-NAM first
                enam_prices = self.get_enam_prices(crop, location)
                
                if enam_prices:
                    all_prices.extend(enam_prices)
                else:
                    # Try AgMarkNet as backup
                    agmarknet_prices = self.get_agmarknet_prices(crop, location)
                    if agmarknet_prices:
                        all_prices.extend(agmarknet_prices)
            
            if all_prices:
                # Cache results for 2 hours
                offline_cache.set(cache_key, all_prices, expiry_hours=2)
                return all_prices
            
            return None
            
        except Exception as e:
            print(f"Consolidated prices error: {str(e)}")
            return None
    
    def get_price_trends(self, crops: List[str], days: int = 30) -> Optional[List[Dict]]:
        """Analyze price trends over time - returns None if insufficient data"""
        trends = []
        
        for crop in crops:
            try:
                # Get historical data
                historical_data = self._get_historical_prices(crop, days)
                
                if len(historical_data) >= 7:  # Need at least a week of data
                    trend_analysis = self._analyze_trend(historical_data)
                    trends.append({
                        "crop": crop,
                        "trend": trend_analysis["direction"],
                        "change_percent": trend_analysis["change_percent"],
                        "volatility": trend_analysis["volatility"],
                        "recommendation": self._generate_price_recommendation(trend_analysis),
                        "confidence": trend_analysis["confidence"]
                    })
            
            except Exception as e:
                print(f"Trend analysis error for {crop}: {str(e)}")
                continue
        
        return trends if trends else None
    
    def get_profit_analysis(self, crop: str, current_price: float, farm_size_acres: float, 
                          location: str) -> Optional[Dict[str, Any]]:
        """Detailed profit analysis for selling decisions"""
        try:
            # Get price trends
            trends = self.get_price_trends([crop], days=30)
            if not trends:
                return None
                
            trend_data = trends[0]
            
            # Estimate yield (crop-specific models)
            yield_per_acre = {
                'rice': 25, 'wheat': 20, 'cotton': 15, 'sugarcane': 350,
                'maize': 22, 'soybean': 12, 'tomato': 200, 'potato': 150
            }
            
            estimated_yield = yield_per_acre.get(crop.lower(), 20) * farm_size_acres
            
            # Calculate costs (region-specific)
            cost_per_acre = {
                'rice': 15000, 'wheat': 12000, 'cotton': 18000, 'sugarcane': 25000,
                'maize': 14000, 'soybean': 13000, 'tomato': 30000, 'potato': 25000
            }
            
            total_cost = cost_per_acre.get(crop.lower(), 15000) * farm_size_acres
            
            # Calculate revenue and profit
            gross_revenue = estimated_yield * current_price
            net_profit = gross_revenue - total_cost
            profit_margin = (net_profit / gross_revenue) * 100 if gross_revenue > 0 else 0
            
            # Future price prediction
            change_percent = trend_data.get('change_percent', 0)
            predicted_price = current_price * (1 + change_percent / 100)
            potential_future_revenue = estimated_yield * predicted_price
            opportunity_cost = potential_future_revenue - gross_revenue
            
            return {
                'current_analysis': {
                    'estimated_yield_quintals': estimated_yield,
                    'current_price_per_quintal': current_price,
                    'gross_revenue': gross_revenue,
                    'estimated_costs': total_cost,
                    'net_profit': net_profit,
                    'profit_margin_percent': profit_margin
                },
                'future_projection': {
                    'predicted_price': predicted_price,
                    'price_trend': trend_data.get('trend', 'stable'),
                    'change_percent': change_percent,
                    'potential_revenue': potential_future_revenue,
                    'opportunity_cost': opportunity_cost
                },
                'recommendation': self._generate_selling_recommendation(
                    profit_margin, change_percent, trend_data.get('confidence', 0.5)
                ),
                'risk_factors': self._identify_selling_risks(trend_data, current_price),
                'location': location,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Profit analysis error: {str(e)}")
            return None
    
    def _parse_enam_data(self, data: Dict) -> List[Dict]:
        """Parse e-NAM API response"""
        prices = []
        records = data.get("records", [])
        
        for record in records:
            prices.append({
                "crop": record.get("commodity", "Unknown"),
                "price": float(record.get("modal_price", 0)),
                "unit": record.get("unit", "quintal"),
                "market": record.get("market", "Unknown"),
                "date": record.get("price_date", datetime.now().strftime("%Y-%m-%d")),
                "source": "enam"
            })
        
        return prices
    
    def _scrape_agmarknet_data(self, commodity: str, market: str) -> Optional[List[Dict]]:
        """Scrape AgMarkNet data - returns None if unavailable"""
        try:
            # This would involve web scraping or API calls to AgMarkNet
            # For now, returning None as real implementation would require
            # specific scraping logic for AgMarkNet website
            return None
        except Exception as e:
            print(f"AgMarkNet scraping error: {str(e)}")
            return None
    
    def _get_historical_prices(self, crop: str, days: int) -> List[Dict]:
        """Get historical price data from cache or APIs"""
        historical = []
        
        # Try to get historical data from cached daily prices
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            cache_key = f"daily_price_{crop}_{date.strftime('%Y-%m-%d')}"
            cached_price = offline_cache.get(cache_key)
            
            if cached_price:
                historical.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "price": cached_price["price"],
                    "crop": crop
                })
        
        return historical
    
    def _analyze_trend(self, historical_data: List[Dict]) -> Dict:
        """Analyze price trend from historical data"""
        prices = [float(record["price"]) for record in historical_data]
        
        if len(prices) < 2:
            return {"direction": "stable", "change_percent": 0, "volatility": 0, "confidence": 0.5}
        
        # Calculate trend
        recent_avg = sum(prices[:7]) / min(7, len(prices))
        older_avg = sum(prices[-7:]) / min(7, len(prices))
        
        change_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        # Determine direction
        if change_percent > 5:
            direction = "increasing"
        elif change_percent < -5:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Calculate volatility (standard deviation)
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        volatility = (variance ** 0.5) / mean_price * 100
        
        # Confidence based on data consistency
        confidence = max(0.5, min(0.95, 1 - (volatility / 100)))
        
        return {
            "direction": direction,
            "change_percent": round(change_percent, 2),
            "volatility": round(volatility, 2),
            "confidence": round(confidence, 2)
        }
    
    def _generate_selling_recommendation(self, profit_margin: float, change_percent: float, confidence: float) -> str:
        """Generate specific selling recommendation"""
        if profit_margin < 10:
            return "⚠️ Low profit margin - consider waiting for better prices or reducing costs"
        elif change_percent > 10 and confidence > 0.7:
            return "🚀 SELL NOW - Strong upward trend with high confidence"
        elif change_percent > 5:
            return "📈 Good time to sell - Prices are rising"
        elif change_percent < -10:
            return "⏳ HOLD - Prices falling, wait for recovery"
        elif profit_margin > 25:
            return "💰 Excellent profit margin - Good time to sell"
        else:
            return "➡️ Moderate conditions - Sell if you need cash flow"
    
    def _identify_selling_risks(self, trend_data: Dict, current_price: float) -> List[str]:
        """Identify risks in selling decision"""
        risks = []
        
        volatility = trend_data.get('volatility', 0)
        if volatility > 20:
            risks.append(f"High price volatility ({volatility:.1f}%) - prices may change rapidly")
        
        confidence = trend_data.get('confidence', 0.5)
        if confidence < 0.6:
            risks.append(f"Low trend confidence ({confidence:.1%}) - predictions may be unreliable")
        
        if current_price < 1000:
            risks.append("Current prices are relatively low - consider market timing")
        
        return risks

# Global instance
real_market_api = RealMarketAPI()
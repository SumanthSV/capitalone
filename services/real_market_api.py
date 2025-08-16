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
        
        # AgMarkNet commodity and state ID mappings
        self.commodity_ids = {
            'rice': '23',
            'wheat': '17',
            'cotton': '384',
            'sugarcane': '29',
            'maize': '25',
            'soybean': '14',
            'tomato': '362',
            'potato': '55',
            'onion': '48',
            'groundnut': '20'
        }
        
        self.state_ids = {
            'karnataka': '12',
            'maharashtra': '14',
            'punjab': '18',
            'haryana': '7',
            'uttar pradesh': '24',
            'bihar': '4',
            'west bengal': '25',
            'gujarat': '6',
            'rajasthan': '19',
            'madhya pradesh': '13',
            'tamil nadu': '22',
            'andhra pradesh': '2',
            'telangana': '36',
            'kerala': '11',
            'odisha': '17'
        }
    
    def get_enam_prices(self, commodity: str, state: str = "") -> Optional[List[Dict]]:
        """Get prices from e-NAM - returns None if unavailable"""
        try:
            cache_key = f"enam_prices_{commodity}_{state}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                print(f"[INFO] Using cached e-NAM data for {commodity}")
                return cached_data
            
            enam_api_key = os.getenv("ENAM_API_KEY")
            if not enam_api_key:
                print(f"[WARNING] e-NAM API key not found in environment variables")
                print(f"[INFO] Set ENAM_API_KEY in your .env file to enable real market data")
                return None
            
            print(f"[INFO] Fetching e-NAM data for {commodity} in {state}")
            
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
            
            print(f"[INFO] e-NAM API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                prices = self._parse_enam_data(data)
                if prices:
                    print(f"[SUCCESS] Got {len(prices)} price records from e-NAM")
                    offline_cache.set(cache_key, prices, self.cache_expiry)
                    return prices
                else:
                    print(f"[WARNING] No price data found in e-NAM response")
            else:
                print(f"[ERROR] e-NAM API returned status {response.status_code}")
                if response.status_code == 401:
                    print(f"[ERROR] Invalid e-NAM API key - check your ENAM_API_KEY")
                elif response.status_code == 403:
                    print(f"[ERROR] e-NAM API access forbidden - check API key permissions")
                
            return None   
        
        except Exception as e:
            print(f"[ERROR] e-NAM API error: {str(e)}")
            return None
        

    def get_agmarknet_prices(self, commodity: str, state: str = "", market_id: str = "0") -> Optional[List[Dict]]:
        """Get prices from AgMarkNet - returns None if unavailable"""
        try:
            cache_key = f"agmarknet_prices_{commodity}_{state}_{market_id}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                print(f"[INFO] Using cached AgMarkNet data for {commodity}")
                return cached_data
            
            # Map commodity and state names to IDs
            commodity_id = self.commodity_ids.get(commodity.lower())
            state_id = self.state_ids.get(state.lower())
            
            if not commodity_id:
                print(f"[WARNING] Commodity '{commodity}' not found in AgMarkNet mapping")
                return None
                
            if not state_id and state:
                print(f"[WARNING] State '{state}' not found in AgMarkNet mapping")
                # Try without state filter
                state_id = "0"
            
            # Set recent date range (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            start_date_str = start_date.strftime("%d-%b-%Y")
            end_date_str = end_date.strftime("%d-%b-%Y")
            
            print(f"[INFO] Fetching AgMarkNet data for commodity_id={commodity_id}, state_id={state_id}")
            
            # Build URL for AgMarkNet
            url = (
                f"{self.agmarknet_url}?Tx_Commodity={commodity_id}"
                f"&Tx_State={state_id or '0'}&Tx_Market={market_id}"
                f"&DateFrom={start_date_str}&DateTo={end_date_str}"
                f"&Fr_Date={start_date_str}&To_Date={end_date_str}&Tx_Trend=2"
                f"&Tx_CommodityHead={commodity}&Tx_StateHead={state}"
                f"&Tx_DistrictHead=--Select--&Tx_MarketHead=--Select--"
            )
            
            print(f"[INFO] AgMarkNet request URL: {url}")
            
            response = requests.get(url, timeout=15)
            print(f"[INFO] AgMarkNet response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[ERROR] AgMarkNet request failed with status {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"id": "ctl00_ContentPlaceHolder1_GridView1"})
            
            if not table:
                print(f"[WARNING] AgMarkNet data table not found in response")
                # Try alternative table selectors
                table = soup.find("table", class_="table")
                if not table:
                    table = soup.find("table")
                
                if not table:
                    print(f"[ERROR] No data table found in AgMarkNet response")
                    return None

            prices = []
            rows = table.find_all("tr")
            
            if len(rows) <= 1:
                print(f"[WARNING] No data rows found in AgMarkNet table")
                return None
                
            # Skip header row
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 7:
                    try:
                        # Parse price data
                        modal_price_text = cols[5].text.strip()
                        if modal_price_text and modal_price_text != '-' and modal_price_text.replace('.', '').isdigit():
                            prices.append({
                                "commodity": cols[0].text.strip(),
                                "market": cols[1].text.strip(),
                                "variety": cols[2].text.strip(),
                                "min_price": cols[3].text.strip(),
                                "max_price": cols[4].text.strip(),
                                "modal_price": modal_price_text,
                                "date": cols[6].text.strip(),
                                "source": "agmarknet"
                            })
                    except Exception as e:
                        print(f"[WARNING] Error parsing AgMarkNet row: {str(e)}")
                        continue

            if prices:
                print(f"[SUCCESS] Got {len(prices)} price records from AgMarkNet")
                offline_cache.set(cache_key, prices, self.cache_expiry)
                return prices
            else:
                print(f"[WARNING] No valid price data found in AgMarkNet response")

            return None

        except Exception as e:
            print(f"[ERROR] AgMarkNet error: {str(e)}")
            return None
    
    def get_consolidated_prices(self, crops: List[str], location: str) -> Optional[List[Dict]]:
        """Get consolidated prices from multiple sources - returns None if unavailable"""
        print(f"\n=== MARKET API DATA COLLECTION START ===")
        print(f"Crops requested: {crops}")
        print(f"Location: {location}")
        
        try:
            if not crops:
                print(f"[WARNING] No crops specified for price lookup")
                print(f"=== MARKET API DATA COLLECTION END ===\n")
                return None
            
            cache_key = f"consolidated_prices_{'-'.join(crops)}_{location}"
            cached_data = offline_cache.get(cache_key)
            if cached_data:
                print(f"[INFO] Using cached market data")
                print(f"=== MARKET API DATA COLLECTION END ===\n")
                return cached_data
            
            all_prices = []
            
            for crop in crops:
                print(f"[INFO] Fetching prices for {crop}...")
                
                # Try e-NAM first
                enam_prices = self.get_enam_prices(crop, location)
                
                if enam_prices and len(enam_prices) > 0:
                    print(f"[SUCCESS] Got e-NAM prices for {crop}: {len(enam_prices)} records")
                    all_prices.extend(enam_prices)
                else:
                    print(f"[WARNING] No e-NAM data for {crop}, trying AgMarkNet...")
                    # Try AgMarkNet as backup
                    agmarknet_prices = self.get_agmarknet_prices(crop, location)
                    if agmarknet_prices and len(agmarknet_prices) > 0:
                        print(f"[SUCCESS] Got AgMarkNet prices for {crop}: {len(agmarknet_prices)} records")
                        all_prices.extend(agmarknet_prices)
                    else:
                        print(f"[WARNING] No AgMarkNet data available for {crop}")
                        # Add a fallback entry to indicate data unavailability
                        all_prices.append({
                            "crop": crop,
                            "price": 0,
                            "unit": "quintal",
                            "market": "Data Unavailable",
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "source": "unavailable",
                            "error": "No real-time data available"
                        })
            
            if all_prices and len(all_prices) > 0:
                # Filter out error entries for caching
                valid_prices = [p for p in all_prices if p.get('source') != 'unavailable']
                if valid_prices:
                    print(f"[INFO] Caching {len(valid_prices)} valid price records")
                    offline_cache.set(cache_key, valid_prices, expiry_hours=2)
                
                print(f"[SUCCESS] Market data collection completed with {len(all_prices)} total records")
                print(f"=== MARKET API DATA COLLECTION END ===\n")
                return all_prices
            
            print(f"[WARNING] No market data available for any requested crops")
            print(f"=== MARKET API DATA COLLECTION END ===\n")
            return None
            
        except Exception as e:
            print(f"[ERROR] Consolidated prices error: {str(e)}")
            print(f"=== MARKET API DATA COLLECTION FAILED ===\n")
            return None
    
    def get_price_trends(self, crops: List[str], days: int = 30) -> Optional[List[Dict]]:
        """Analyze price trends over time - returns None if insufficient data"""
        if not crops:
            return None
            
        trends = []
        
        for crop in crops:
            try:
                # Get historical data
                historical_data = self._get_historical_prices(crop, days)
                
                if historical_data and len(historical_data) >= 7:  # Need at least a week of data
                    trend_analysis = self._analyze_trend(historical_data)
                    trends.append({
                        "crop": crop,
                        "trend": trend_analysis["direction"],
                        "change_percent": trend_analysis["change_percent"],
                        "volatility": trend_analysis["volatility"],
                        "recommendation": self._generate_price_recommendation(trend_analysis),
                        "confidence": trend_analysis["confidence"]
                    })
                else:
                    print(f"[WARNING] Insufficient historical data for {crop} trend analysis")
                    # Add placeholder trend data
                    trends.append({
                        "crop": crop,
                        "trend": "stable",
                        "change_percent": 0.0,
                        "volatility": 0.0,
                        "recommendation": "Insufficient data for trend analysis",
                        "confidence": 0.1
                    })
            
            except Exception as e:
                print(f"[ERROR] Trend analysis error for {crop}: {str(e)}")
                continue
        
        return trends if trends else None
    
    def get_profit_analysis(self, crop: str, current_price: float, farm_size_acres: float, 
                          location: str) -> Optional[Dict[str, Any]]:
        """Detailed profit analysis for selling decisions"""
        try:
            if not crop or current_price <= 0 or farm_size_acres <= 0:
                return None
                
            # Get price trends
            trends = self.get_price_trends([crop], days=30)
            trend_data = trends[0] if trends and len(trends) > 0 else {
                'trend': 'stable', 'change_percent': 0, 'confidence': 0.5
            }
            
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
            print(f"[ERROR] Profit analysis error: {str(e)}")
            return None
    
    def _parse_enam_data(self, data: Dict) -> List[Dict]:
        """Parse e-NAM API response"""
        prices = []
        
        try:
            records = data.get("records", [])
            
            if not records:
                print(f"[WARNING] No records found in e-NAM response")
                return prices
            
            for record in records:
                try:
                    modal_price = record.get("modal_price", "0")
                    if modal_price and str(modal_price).replace('.', '').isdigit():
                        prices.append({
                            "crop": record.get("commodity", "Unknown"),
                            "price": float(modal_price),
                            "unit": record.get("unit", "quintal"),
                            "market": record.get("market", "Unknown"),
                            "date": record.get("price_date", datetime.now().strftime("%Y-%m-%d")),
                            "source": "enam"
                        })
                except Exception as e:
                    print(f"[WARNING] Error parsing e-NAM record: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"[ERROR] e-NAM data parsing error: {str(e)}")
        
        return prices
    
    def _get_historical_prices(self, crop: str, days: int) -> List[Dict]:
        """Get historical price data from cache or APIs"""
        historical = []
        
        try:
            # Try to get historical data from cached daily prices
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                cache_key = f"daily_price_{crop}_{date.strftime('%Y-%m-%d')}"
                cached_price = offline_cache.get(cache_key)
                
                if cached_price and isinstance(cached_price, dict) and 'price' in cached_price:
                    historical.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "price": cached_price["price"],
                        "crop": crop
                    })
        
        except Exception as e:
            print(f"[ERROR] Historical data retrieval error: {str(e)}")
        
        return historical
    
    def _analyze_trend(self, historical_data: List[Dict]) -> Dict:
        """Analyze price trend from historical data"""
        try:
            if not historical_data or len(historical_data) < 2:
                return {"direction": "stable", "change_percent": 0, "volatility": 0, "confidence": 0.1}
            
            prices = []
            for record in historical_data:
                try:
                    price = float(record.get("price", 0))
                    if price > 0:
                        prices.append(price)
                except (ValueError, TypeError):
                    continue
            
            if len(prices) < 2:
                return {"direction": "stable", "change_percent": 0, "volatility": 0, "confidence": 0.1}
            
            # Calculate trend
            recent_avg = sum(prices[:min(7, len(prices))]) / min(7, len(prices))
            older_avg = sum(prices[-min(7, len(prices)):]) / min(7, len(prices))
            
            if older_avg > 0:
                change_percent = ((recent_avg - older_avg) / older_avg) * 100
            else:
                change_percent = 0
            
            # Determine direction
            if change_percent > 5:
                direction = "increasing"
            elif change_percent < -5:
                direction = "decreasing"
            else:
                direction = "stable"
            
            # Calculate volatility (standard deviation)
            if len(prices) > 1:
                mean_price = sum(prices) / len(prices)
                variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
                volatility = (variance ** 0.5) / mean_price * 100 if mean_price > 0 else 0
            else:
                volatility = 0
            
            # Confidence based on data consistency
            confidence = max(0.1, min(0.95, 1 - (volatility / 100)))
            
            return {
                "direction": direction,
                "change_percent": round(change_percent, 2),
                "volatility": round(volatility, 2),
                "confidence": round(confidence, 2)
            }
            
        except Exception as e:
            print(f"[ERROR] Trend analysis error: {str(e)}")
            return {"direction": "stable", "change_percent": 0, "volatility": 0, "confidence": 0.1}
    
    def _generate_price_recommendation(self, trend_analysis: Dict) -> str:
        """Generate specific price recommendation"""
        try:
            direction = trend_analysis.get("direction", "stable")
            change_percent = trend_analysis.get("change_percent", 0)
            confidence = trend_analysis.get("confidence", 0.5)
            
            if direction == "increasing" and change_percent > 10 and confidence > 0.7:
                return "Strong upward trend - good time to sell"
            elif direction == "increasing" and change_percent > 5:
                return "Prices rising - consider selling soon"
            elif direction == "decreasing" and change_percent < -10:
                return "Prices falling - hold if possible"
            elif direction == "decreasing" and change_percent < -5:
                return "Slight decline - monitor closely"
            else:
                return "Stable prices - sell based on your needs"
                
        except Exception as e:
            print(f"[ERROR] Price recommendation error: {str(e)}")
            return "Unable to generate recommendation"
    
    def _generate_selling_recommendation(self, profit_margin: float, change_percent: float, confidence: float) -> str:
        """Generate specific selling recommendation"""
        try:
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
        except Exception as e:
            print(f"[ERROR] Selling recommendation error: {str(e)}")
            return "Unable to generate selling recommendation"
    
    def _identify_selling_risks(self, trend_data: Dict, current_price: float) -> List[str]:
        """Identify risks in selling decision"""
        risks = []
        
        try:
            volatility = trend_data.get('volatility', 0)
            if volatility > 20:
                risks.append(f"High price volatility ({volatility:.1f}%) - prices may change rapidly")
            
            confidence = trend_data.get('confidence', 0.5)
            if confidence < 0.6:
                risks.append(f"Low trend confidence ({confidence:.1%}) - predictions may be unreliable")
            
            if current_price < 1000:
                risks.append("Current prices are relatively low - consider market timing")
            
            if not risks:
                risks.append("No significant risks identified")
                
        except Exception as e:
            print(f"[ERROR] Risk identification error: {str(e)}")
            risks.append("Unable to assess risks")
        
        return risks

# Global instance
real_market_api = RealMarketAPI()
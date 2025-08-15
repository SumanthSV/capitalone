# services/phone_auth.py
import sqlite3
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional
import uuid
import os

class PhoneAuthService:
    """Service for phone number authentication with OTP"""
    
    def __init__(self, db_path: str = "phone_auth.db"):
        self.db_path = db_path
        self.otp_expiry_minutes = 10
        self.init_database()
    
    def init_database(self):
        """Initialize phone auth database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # OTP sessions table
        c.execute('''CREATE TABLE IF NOT EXISTS otp_sessions (
            session_id TEXT PRIMARY KEY,
            phone_number TEXT NOT NULL,
            country_code TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            attempts INTEGER DEFAULT 0
        )''')
        
        # Phone to user mapping
        c.execute('''CREATE TABLE IF NOT EXISTS phone_users (
            phone_number TEXT NOT NULL,
            country_code TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (phone_number, country_code)
        )''')
        
        conn.commit()
        conn.close()
    
    def send_otp(self, phone_number: str, country_code: str = "+91") -> Dict[str, any]:
        """Send OTP to phone number"""
        try:
            # Generate OTP
            otp_code = ''.join(random.choices(string.digits, k=6))
            session_id = str(uuid.uuid4())
            
            # Store OTP session
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            created_at = datetime.now()
            expires_at = created_at + timedelta(minutes=self.otp_expiry_minutes)
            
            c.execute('''INSERT INTO otp_sessions 
                        (session_id, phone_number, country_code, otp_code, 
                         created_at, expires_at, verified, attempts)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (session_id, phone_number, country_code, otp_code,
                      created_at.isoformat(), expires_at.isoformat(), False, 0))
            
            conn.commit()
            conn.close()
            
            # In production, integrate with SMS service (Twilio, etc.)
            success = self._send_sms(phone_number, country_code, otp_code)
            
            if success:
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "OTP sent successfully",
                    "expires_in_minutes": self.otp_expiry_minutes
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send SMS"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OTP generation failed: {str(e)}"
            }
    
    def verify_otp(self, session_id: str, otp_code: str) -> Dict[str, any]:
        """Verify OTP code"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get OTP session
            c.execute('''SELECT phone_number, country_code, otp_code, expires_at, verified, attempts 
                        FROM otp_sessions WHERE session_id = ?''', (session_id,))
            
            session = c.fetchone()
            
            if not session:
                conn.close()
                return {
                    "success": False,
                    "error": "Invalid session"
                }
            
            phone_number, country_code, stored_otp, expires_at, verified, attempts = session
            
            # Check if already verified
            if verified:
                conn.close()
                return {
                    "success": False,
                    "error": "OTP already used"
                }
            
            # Check expiry
            if datetime.now() > datetime.fromisoformat(expires_at):
                conn.close()
                return {
                    "success": False,
                    "error": "OTP expired"
                }
            
            # Check attempts
            if attempts >= 3:
                conn.close()
                return {
                    "success": False,
                    "error": "Too many attempts"
                }
            
            # Verify OTP
            if otp_code == stored_otp:
                # Mark as verified
                c.execute('''UPDATE otp_sessions SET verified = TRUE 
                            WHERE session_id = ?''', (session_id,))
                conn.commit()
                conn.close()
                
                return {
                    "success": True,
                    "phone_number": phone_number,
                    "country_code": country_code,
                    "message": "OTP verified successfully"
                }
            else:
                # Increment attempts
                c.execute('''UPDATE otp_sessions SET attempts = attempts + 1 
                            WHERE session_id = ?''', (session_id,))
                conn.commit()
                conn.close()
                
                return {
                    "success": False,
                    "error": "Invalid OTP"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"OTP verification failed: {str(e)}"
            }
    
    def get_user_by_phone(self, phone_number: str, country_code: str) -> Optional[str]:
        """Get user ID by phone number"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT user_id FROM phone_users 
                    WHERE phone_number = ? AND country_code = ?''',
                 (phone_number, country_code))
        
        result = c.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def link_phone_to_user(self, user_id: str, phone_number: str, country_code: str) -> bool:
        """Link phone number to user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''INSERT OR REPLACE INTO phone_users 
                        (phone_number, country_code, user_id, created_at)
                        VALUES (?, ?, ?, ?)''',
                     (phone_number, country_code, user_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Phone linking error: {str(e)}")
            return False
    
    def _send_sms(self, phone_number: str, country_code: str, otp_code: str) -> bool:
        """Send SMS using external service"""
        try:
            # Check if Twilio is configured
            twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
            
            if twilio_sid and twilio_token and twilio_phone:
                from twilio.rest import Client
                
                client = Client(twilio_sid, twilio_token)
                
                message = client.messages.create(
                    body=f"Your KrishiMitra verification code is: {otp_code}. Valid for {self.otp_expiry_minutes} minutes.",
                    from_=twilio_phone,
                    to=f"{country_code}{phone_number}"
                )
                
                return message.sid is not None
            else:
                # For development/testing - just log the OTP
                print(f"[DEV] OTP for {country_code}{phone_number}: {otp_code}")
                return True
                
        except Exception as e:
            print(f"SMS sending error: {str(e)}")
            return False

# Global phone auth service
phone_auth_service = PhoneAuthService()
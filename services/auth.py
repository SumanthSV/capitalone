# services/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
from dataclasses import dataclass
import sqlite3
import uuid

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

@dataclass
class User:
    id: str
    email: str
    name: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = None

class AuthService:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TEXT NOT NULL
        )''')
        
        conn.commit()
        conn.close()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0],
                email=row[1],
                name=row[2],
                hashed_password=row[3],
                is_active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5])
            )
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0],
                email=row[1],
                name=row[2],
                hashed_password=row[3],
                is_active=bool(row[4]),
                created_at=datetime.fromisoformat(row[5])
            )
        return None
    
    def create_user(self, email: str, name: str, password: str) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        hashed_password = self.get_password_hash(password)
        created_at = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''INSERT INTO users (id, email, name, hashed_password, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (user_id, email, name, hashed_password, True, created_at.isoformat()))
            conn.commit()
            
            return User(
                id=user_id,
                email=email,
                name=name,
                hashed_password=hashed_password,
                is_active=True,
                created_at=created_at
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

# Global auth service
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        user_id = auth_service.verify_token(credentials.credentials)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Optional dependency for routes that work with or without authentication
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        if not credentials:
            return None
        
        user_id = auth_service.verify_token(credentials.credentials)
        if user_id is None:
            return None
        
        user = auth_service.get_user_by_id(user_id)
        return user if user and user.is_active else None
    except:
        return None
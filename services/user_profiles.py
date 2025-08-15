# services/user_profiles.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class FarmSize(Enum):
    SMALL = "small"  # 0-2 acres
    MEDIUM = "medium"  # 2-10 acres
    LARGE = "large"  # 10+ acres

class ExperienceLevel(Enum):
    BEGINNER = "beginner"  # 0-2 years
    INTERMEDIATE = "intermediate"  # 3-10 years
    EXPERIENCED = "experienced"  # 10+ years
    EXPERT = "expert"  # Commercial/Expert

@dataclass
class UserProfile:
    user_id: str
    name: str
    email: str
    phone: Optional[str]
    location: str
    primary_crops: List[str]
    secondary_crops: List[str]
    farm_size: FarmSize
    soil_type: str
    irrigation_type: str
    experience: ExperienceLevel
    preferred_language: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'primary_crops': self.primary_crops,
            'secondary_crops': self.secondary_crops,
            'farm_size': self.farm_size.value,
            'soil_type': self.soil_type,
            'irrigation_type': self.irrigation_type,
            'experience': self.experience.value,
            'preferred_language': self.preferred_language,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class UserInteraction:
    interaction_id: str
    user_id: str
    interaction_type: str
    query: str
    response: str
    confidence_score: float
    data_sources: List[str]
    timestamp: datetime

class UserProfileService:
    """Service for managing user profiles and interactions"""
    
    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize user profiles database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # User profiles table
        c.execute('''CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            location TEXT NOT NULL,
            primary_crops TEXT NOT NULL,  -- JSON array
            secondary_crops TEXT,  -- JSON array
            farm_size TEXT NOT NULL,
            soil_type TEXT NOT NULL,
            irrigation_type TEXT NOT NULL,
            experience TEXT NOT NULL,
            preferred_language TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        # User interactions table
        c.execute('''CREATE TABLE IF NOT EXISTS user_interactions (
            interaction_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            interaction_type TEXT NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            data_sources TEXT,  -- JSON array
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )''')
        
        conn.commit()
        conn.close()
    
    def create_profile(self, data: Dict[str, Any]) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(
            user_id=data['user_id'],
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            location=data['location'],
            primary_crops=data['primary_crops'] if isinstance(data['primary_crops'], list) else data['primary_crops'].split(','),
            secondary_crops=data.get('secondary_crops', []) if isinstance(data.get('secondary_crops', []), list) else data.get('secondary_crops', '').split(','),
            farm_size=FarmSize(data['farm_size']),
            soil_type=data['soil_type'],
            irrigation_type=data['irrigation_type'],
            experience=ExperienceLevel(data['experience']),
            preferred_language=data['preferred_language'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._save_profile(profile)
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return UserProfile(
                user_id=row[0],
                name=row[1],
                email=row[2],
                phone=row[3],
                location=row[4],
                primary_crops=json.loads(row[5]),
                secondary_crops=json.loads(row[6]) if row[6] else [],
                farm_size=FarmSize(row[7]),
                soil_type=row[8],
                irrigation_type=row[9],
                experience=ExperienceLevel(row[10]),
                preferred_language=row[11],
                created_at=datetime.fromisoformat(row[12]),
                updated_at=datetime.fromisoformat(row[13])
            )
        return None
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(profile, key):
                if key == 'farm_size':
                    setattr(profile, key, FarmSize(value))
                elif key == 'experience':
                    setattr(profile, key, ExperienceLevel(value))
                else:
                    setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        self._save_profile(profile)
        return True
    
    def record_interaction(self, user_id: str, interaction_type: str, query: str, 
                          response: str, confidence_score: float, data_sources: List[str]) -> str:
        """Record user interaction"""
        interaction_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO user_interactions 
                    (interaction_id, user_id, interaction_type, query, response, 
                     confidence_score, data_sources, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (interaction_id, user_id, interaction_type, query, response,
                  confidence_score, json.dumps(data_sources), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return interaction_id
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        profile = self.get_profile(user_id)
        if not profile:
            return {}
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get recent interactions
        c.execute('''SELECT * FROM user_interactions 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC LIMIT 10''', (user_id,))
        
        interactions = []
        for row in c.fetchall():
            interactions.append({
                'interaction_id': row[0],
                'interaction_type': row[2],
                'query': row[3],
                'response': row[4][:200] + '...' if len(row[4]) > 200 else row[4],
                'confidence_score': row[5],
                'data_sources': json.loads(row[6]) if row[6] else [],
                'timestamp': row[7]
            })
        
        conn.close()
        
        return {
            'profile': profile.to_dict(),
            'recent_interactions': interactions,
            'total_interactions': len(interactions),
            'avg_confidence': sum(i['confidence_score'] for i in interactions) / len(interactions) if interactions else 0
        }
    
    def _save_profile(self, profile: UserProfile):
        """Save profile to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO user_profiles 
                    (user_id, name, email, phone, location, primary_crops, secondary_crops,
                     farm_size, soil_type, irrigation_type, experience, preferred_language,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (profile.user_id, profile.name, profile.email, profile.phone,
                  profile.location, json.dumps(profile.primary_crops),
                  json.dumps(profile.secondary_crops), profile.farm_size.value,
                  profile.soil_type, profile.irrigation_type, profile.experience.value,
                  profile.preferred_language, profile.created_at.isoformat(),
                  profile.updated_at.isoformat()))
        
        conn.commit()
        conn.close()

# Global user profile service
user_profile_service = UserProfileService()
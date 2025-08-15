# services/contextual_memory.py
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from services.offline_cache import offline_cache

class InteractionType(Enum):
    QUERY = "query"
    IMAGE_ANALYSIS = "image_analysis"
    IRRIGATION_REQUEST = "irrigation_request"
    MARKET_INQUIRY = "market_inquiry"
    WEATHER_CHECK = "weather_check"
    DISEASE_DETECTION = "disease_detection"

class CropStage(Enum):
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MATURITY = "maturity"
    HARVEST = "harvest"

@dataclass
class FarmingContext:
    user_id: str
    location: str
    primary_crops: List[str]
    secondary_crops: List[str]
    farm_size_acres: float
    soil_type: str
    irrigation_method: str
    last_irrigation: Optional[datetime]
    irrigation_frequency_days: int
    fertilizer_schedule: Dict[str, Any]
    crop_stages: Dict[str, CropStage]
    planting_dates: Dict[str, datetime]
    harvest_dates: Dict[str, datetime]
    preferred_language: str
    farming_experience: str
    created_at: datetime
    updated_at: datetime

@dataclass
class ConversationMemory:
    conversation_id: str
    user_id: str
    topic: str
    context_data: Dict[str, Any]
    last_query: str
    last_response: str
    follow_up_questions: List[str]
    unresolved_issues: List[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

@dataclass
class IrrigationHistory:
    irrigation_id: str
    user_id: str
    crop_name: str
    irrigation_date: datetime
    water_amount_liters: float
    irrigation_method: str
    weather_conditions: Dict[str, Any]
    soil_moisture_before: Optional[float]
    soil_moisture_after: Optional[float]
    effectiveness_rating: Optional[int]  # 1-5 scale
    notes: str

class ContextualMemoryService:
    """Advanced contextual memory system for personalized farming advice"""
    
    def __init__(self, db_path: str = "contextual_memory.db"):
        self.db_path = db_path
        self.init_database()
        self.conversation_expiry_days = 30
        self.context_cache_hours = 24
    
    def init_database(self):
        """Initialize contextual memory database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Farming context table
        c.execute('''CREATE TABLE IF NOT EXISTS farming_context (
            user_id TEXT PRIMARY KEY,
            location TEXT,
            primary_crops TEXT,  -- JSON array
            secondary_crops TEXT,  -- JSON array
            farm_size_acres REAL,
            soil_type TEXT,
            irrigation_method TEXT,
            last_irrigation TEXT,
            irrigation_frequency_days INTEGER,
            fertilizer_schedule TEXT,  -- JSON object
            crop_stages TEXT,  -- JSON object
            planting_dates TEXT,  -- JSON object
            harvest_dates TEXT,  -- JSON object
            preferred_language TEXT,
            farming_experience TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')
        
        # Conversation memory table
        c.execute('''CREATE TABLE IF NOT EXISTS conversation_memory (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT,
            topic TEXT,
            context_data TEXT,  -- JSON object
            last_query TEXT,
            last_response TEXT,
            follow_up_questions TEXT,  -- JSON array
            unresolved_issues TEXT,  -- JSON array
            created_at TEXT,
            updated_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES farming_context (user_id)
        )''')
        
        # Irrigation history table
        c.execute('''CREATE TABLE IF NOT EXISTS irrigation_history (
            irrigation_id TEXT PRIMARY KEY,
            user_id TEXT,
            crop_name TEXT,
            irrigation_date TEXT,
            water_amount_liters REAL,
            irrigation_method TEXT,
            weather_conditions TEXT,  -- JSON object
            soil_moisture_before REAL,
            soil_moisture_after REAL,
            effectiveness_rating INTEGER,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES farming_context (user_id)
        )''')
        
        # Interaction patterns table
        c.execute('''CREATE TABLE IF NOT EXISTS interaction_patterns (
            pattern_id TEXT PRIMARY KEY,
            user_id TEXT,
            interaction_type TEXT,
            frequency INTEGER,
            preferred_time_of_day TEXT,
            seasonal_patterns TEXT,  -- JSON object
            success_rate REAL,
            last_interaction TEXT,
            FOREIGN KEY (user_id) REFERENCES farming_context (user_id)
        )''')
        
        # Knowledge preferences table
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge_preferences (
            user_id TEXT PRIMARY KEY,
            preferred_topics TEXT,  -- JSON array
            avoided_topics TEXT,  -- JSON array
            detail_level TEXT,  -- basic, intermediate, advanced
            response_format TEXT,  -- text, voice, visual
            trusted_sources TEXT,  -- JSON array
            learning_style TEXT,  -- visual, auditory, practical
            FOREIGN KEY (user_id) REFERENCES farming_context (user_id)
        )''')
        
        conn.commit()
        conn.close()
    
    def create_farming_context(self, user_id: str, context_data: Dict) -> FarmingContext:
        """Create initial farming context for user"""
        context = FarmingContext(
            user_id=user_id,
            location=context_data.get('location', ''),
            primary_crops=context_data.get('primary_crops', []),
            secondary_crops=context_data.get('secondary_crops', []),
            farm_size_acres=float(context_data.get('farm_size_acres', 1.0)),
            soil_type=context_data.get('soil_type', ''),
            irrigation_method=context_data.get('irrigation_method', 'manual'),
            last_irrigation=None,
            irrigation_frequency_days=context_data.get('irrigation_frequency_days', 7),
            fertilizer_schedule=context_data.get('fertilizer_schedule', {}),
            crop_stages={},
            planting_dates={},
            harvest_dates={},
            preferred_language=context_data.get('preferred_language', 'hindi'),
            farming_experience=context_data.get('farming_experience', 'beginner'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._save_farming_context(context)
        return context
    
    def get_farming_context(self, user_id: str) -> Optional[FarmingContext]:
        """Get farming context for user"""
        # Try cache first
        cache_key = f"farming_context_{user_id}"
        cached_data = offline_cache.get(cache_key)
        
        if cached_data:
            return self._dict_to_farming_context(cached_data)
        
        # Fallback to database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM farming_context WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            context_data = {
                'user_id': row[0], 'location': row[1],
                'primary_crops': json.loads(row[2]) if row[2] else [],
                'secondary_crops': json.loads(row[3]) if row[3] else [],
                'farm_size_acres': row[4], 'soil_type': row[5],
                'irrigation_method': row[6],
                'last_irrigation': datetime.fromisoformat(row[7]) if row[7] else None,
                'irrigation_frequency_days': row[8],
                'fertilizer_schedule': json.loads(row[9]) if row[9] else {},
                'crop_stages': {k: CropStage(v) for k, v in json.loads(row[10]).items()} if row[10] else {},
                'planting_dates': {k: datetime.fromisoformat(v) for k, v in json.loads(row[11]).items()} if row[11] else {},
                'harvest_dates': {k: datetime.fromisoformat(v) for k, v in json.loads(row[12]).items()} if row[12] else {},
                'preferred_language': row[13], 'farming_experience': row[14],
                'created_at': datetime.fromisoformat(row[15]),
                'updated_at': datetime.fromisoformat(row[16])
            }
            
            context = self._dict_to_farming_context(context_data)
            
            # Cache for future use
            offline_cache.set(cache_key, self._farming_context_to_dict(context), 
                            expiry_hours=self.context_cache_hours)
            
            return context
        
        return None
    
    def update_farming_context(self, user_id: str, updates: Dict) -> bool:
        """Update farming context with new information"""
        context = self.get_farming_context(user_id)
        if not context:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(context, key):
                if key in ['planting_dates', 'harvest_dates'] and isinstance(value, dict):
                    # Convert string dates to datetime objects
                    converted_dates = {}
                    for crop, date_str in value.items():
                        if isinstance(date_str, str):
                            converted_dates[crop] = datetime.fromisoformat(date_str)
                        else:
                            converted_dates[crop] = date_str
                    setattr(context, key, converted_dates)
                elif key == 'crop_stages' and isinstance(value, dict):
                    # Convert string stages to CropStage enum
                    converted_stages = {}
                    for crop, stage in value.items():
                        if isinstance(stage, str):
                            converted_stages[crop] = CropStage(stage)
                        else:
                            converted_stages[crop] = stage
                    setattr(context, key, converted_stages)
                else:
                    setattr(context, key, value)
        
        context.updated_at = datetime.now()
        self._save_farming_context(context)
        return True
    
    def record_irrigation(self, user_id: str, irrigation_data: Dict) -> str:
        """Record irrigation event"""
        irrigation_id = str(uuid.uuid4())
        
        irrigation = IrrigationHistory(
            irrigation_id=irrigation_id,
            user_id=user_id,
            crop_name=irrigation_data['crop_name'],
            irrigation_date=datetime.now(),
            water_amount_liters=float(irrigation_data.get('water_amount_liters', 0)),
            irrigation_method=irrigation_data.get('irrigation_method', 'manual'),
            weather_conditions=irrigation_data.get('weather_conditions', {}),
            soil_moisture_before=irrigation_data.get('soil_moisture_before'),
            soil_moisture_after=irrigation_data.get('soil_moisture_after'),
            effectiveness_rating=irrigation_data.get('effectiveness_rating'),
            notes=irrigation_data.get('notes', '')
        )
        
        self._save_irrigation_history(irrigation)
        
        # Update farming context
        self.update_farming_context(user_id, {
            'last_irrigation': datetime.now()
        })
        
        return irrigation_id
    
    def get_irrigation_history(self, user_id: str, days: int = 30) -> List[IrrigationHistory]:
        """Get irrigation history for user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute('''SELECT * FROM irrigation_history 
                    WHERE user_id = ? AND irrigation_date >= ?
                    ORDER BY irrigation_date DESC''', (user_id, since_date))
        
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append(IrrigationHistory(
                irrigation_id=row[0], user_id=row[1], crop_name=row[2],
                irrigation_date=datetime.fromisoformat(row[3]),
                water_amount_liters=row[4], irrigation_method=row[5],
                weather_conditions=json.loads(row[6]) if row[6] else {},
                soil_moisture_before=row[7], soil_moisture_after=row[8],
                effectiveness_rating=row[9], notes=row[10]
            ))
        
        return history
    
    def create_conversation_memory(self, user_id: str, topic: str, 
                                 query: str, response: str, context_data: Dict = None) -> str:
        """Create or update conversation memory"""
        conversation_id = str(uuid.uuid4())
        
        memory = ConversationMemory(
            conversation_id=conversation_id,
            user_id=user_id,
            topic=topic,
            context_data=context_data or {},
            last_query=query,
            last_response=response,
            follow_up_questions=[],
            unresolved_issues=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=self.conversation_expiry_days)
        )
        
        self._save_conversation_memory(memory)
        return conversation_id
    
    def get_conversation_context(self, user_id: str, topic: str = None) -> List[ConversationMemory]:
        """Get recent conversation context for user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if topic:
            c.execute('''SELECT * FROM conversation_memory 
                        WHERE user_id = ? AND topic = ? AND expires_at > ?
                        ORDER BY updated_at DESC LIMIT 5''', 
                     (user_id, topic, datetime.now().isoformat()))
        else:
            c.execute('''SELECT * FROM conversation_memory 
                        WHERE user_id = ? AND expires_at > ?
                        ORDER BY updated_at DESC LIMIT 10''', 
                     (user_id, datetime.now().isoformat()))
        
        rows = c.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            memories.append(ConversationMemory(
                conversation_id=row[0], user_id=row[1], topic=row[2],
                context_data=json.loads(row[3]) if row[3] else {},
                last_query=row[4], last_response=row[5],
                follow_up_questions=json.loads(row[6]) if row[6] else [],
                unresolved_issues=json.loads(row[7]) if row[7] else [],
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9]),
                expires_at=datetime.fromisoformat(row[10])
            ))
        
        return memories
    
    def generate_contextual_prompt(self, user_id: str, current_query: str) -> str:
        """Generate contextual prompt with user's farming history"""
        context = self.get_farming_context(user_id)
        if not context:
            return f"""
FARMER CONTEXT: No farming profile available for this user.

CURRENT QUESTION: {current_query}

Please provide general agricultural advice and suggest the farmer complete their farming profile for personalized recommendations.
"""
        
        # Get recent conversations
        recent_conversations = self.get_conversation_context(user_id)
        
        # Get irrigation history
        irrigation_history = self.get_irrigation_history(user_id, days=14)
        
        # Build contextual prompt
        contextual_info = []
        
        # Detailed farmer profile
        contextual_info.append(f"FARMER'S PERSONAL PROFILE:")
        contextual_info.append(f"- Location: {context.location}")
        contextual_info.append(f"- Primary crops: {', '.join(context.primary_crops)}")
        contextual_info.append(f"- Secondary crops: {', '.join(context.secondary_crops)}")
        contextual_info.append(f"- Farm size: {context.farm_size_acres} acres")
        contextual_info.append(f"- Soil type: {context.soil_type}")
        contextual_info.append(f"- Irrigation method: {context.irrigation_method}")
        contextual_info.append(f"- Irrigation frequency: Every {context.irrigation_frequency_days} days")
        contextual_info.append(f"- Experience level: {context.farming_experience}")
        contextual_info.append(f"- Preferred language: {context.preferred_language}")
        
        # Current crop stages
        if context.crop_stages:
            contextual_info.append(f"CURRENT CROP STAGES:")
            for crop, stage in context.crop_stages.items():
                contextual_info.append(f"- {crop}: {stage.value}")
        
        # Planting and harvest dates
        if context.planting_dates:
            contextual_info.append(f"PLANTING DATES:")
            for crop, date in context.planting_dates.items():
                contextual_info.append(f"- {crop}: {date.strftime('%Y-%m-%d')}")
        
        if context.harvest_dates:
            contextual_info.append(f"EXPECTED HARVEST DATES:")
            for crop, date in context.harvest_dates.items():
                contextual_info.append(f"- {crop}: {date.strftime('%Y-%m-%d')}")
        
        # Recent irrigation
        if context.last_irrigation:
            days_since = (datetime.now() - context.last_irrigation).days
            contextual_info.append(f"LAST IRRIGATION: {days_since} days ago ({context.last_irrigation.strftime('%Y-%m-%d')})")
        
        # Recent conversations (if relevant)
        if recent_conversations:
            contextual_info.append(f"RECENT CONVERSATIONS:")
            for conv in recent_conversations[:3]:
                contextual_info.append(f"- {conv.topic}: {conv.last_query[:150]}...")
                contextual_info.append(f"  Response: {conv.last_response[:100]}...")
        
        # Irrigation patterns
        if irrigation_history:
            avg_frequency = len(irrigation_history) / 2  # Over 2 weeks
            contextual_info.append(f"IRRIGATION PATTERN: {avg_frequency:.1f} times per week")
            
            # Recent irrigation effectiveness
            recent_effectiveness = [h.effectiveness_rating for h in irrigation_history[-3:] 
                                  if h.effectiveness_rating is not None]
            if recent_effectiveness:
                avg_effectiveness = sum(recent_effectiveness) / len(recent_effectiveness)
                contextual_info.append(f"Recent irrigation effectiveness: {avg_effectiveness:.1f}/5")
        
        # Combine with current query
        full_prompt = f"""
PERSONAL FARMING CONTEXT:
{chr(10).join(contextual_info)}

FARMER'S CURRENT QUESTION: "{current_query}"

INSTRUCTIONS: Provide highly personalized advice that:
1. References their specific crops, location, and farm details
2. Considers their farming experience level and irrigation patterns
3. Builds on previous conversations and decisions
4. Focuses on their profit and efficiency
5. Uses their preferred language and communication style
6. Provides specific, actionable steps they can take immediately

Respond as their trusted personal agricultural advisor who knows their farm intimately.
"""
        
        return full_prompt
    
    def _save_farming_context(self, context: FarmingContext):
        """Save farming context to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Convert complex types to JSON
        crop_stages_json = json.dumps({k: v.value for k, v in context.crop_stages.items()})
        planting_dates_json = json.dumps({k: v.isoformat() for k, v in context.planting_dates.items()})
        harvest_dates_json = json.dumps({k: v.isoformat() for k, v in context.harvest_dates.items()})
        
        c.execute('''INSERT OR REPLACE INTO farming_context 
                    (user_id, location, primary_crops, secondary_crops, farm_size_acres,
                     soil_type, irrigation_method, last_irrigation, irrigation_frequency_days,
                     fertilizer_schedule, crop_stages, planting_dates, harvest_dates,
                     preferred_language, farming_experience, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (context.user_id, context.location, json.dumps(context.primary_crops),
                  json.dumps(context.secondary_crops), context.farm_size_acres,
                  context.soil_type, context.irrigation_method,
                  context.last_irrigation.isoformat() if context.last_irrigation else None,
                  context.irrigation_frequency_days, json.dumps(context.fertilizer_schedule),
                  crop_stages_json, planting_dates_json, harvest_dates_json,
                  context.preferred_language, context.farming_experience,
                  context.created_at.isoformat(), context.updated_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update cache
        cache_key = f"farming_context_{context.user_id}"
        offline_cache.set(cache_key, self._farming_context_to_dict(context), 
                         expiry_hours=self.context_cache_hours)
    
    def _save_conversation_memory(self, memory: ConversationMemory):
        """Save conversation memory to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO conversation_memory 
                    (conversation_id, user_id, topic, context_data, last_query, last_response,
                     follow_up_questions, unresolved_issues, created_at, updated_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (memory.conversation_id, memory.user_id, memory.topic,
                  json.dumps(memory.context_data), memory.last_query, memory.last_response,
                  json.dumps(memory.follow_up_questions), json.dumps(memory.unresolved_issues),
                  memory.created_at.isoformat(), memory.updated_at.isoformat(),
                  memory.expires_at.isoformat()))
        
        conn.commit()
        conn.close()
    
    def _save_irrigation_history(self, irrigation: IrrigationHistory):
        """Save irrigation history to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO irrigation_history 
                    (irrigation_id, user_id, crop_name, irrigation_date, water_amount_liters,
                     irrigation_method, weather_conditions, soil_moisture_before, 
                     soil_moisture_after, effectiveness_rating, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (irrigation.irrigation_id, irrigation.user_id, irrigation.crop_name,
                  irrigation.irrigation_date.isoformat(), irrigation.water_amount_liters,
                  irrigation.irrigation_method, json.dumps(irrigation.weather_conditions),
                  irrigation.soil_moisture_before, irrigation.soil_moisture_after,
                  irrigation.effectiveness_rating, irrigation.notes))
        
        conn.commit()
        conn.close()
    
    def _farming_context_to_dict(self, context: FarmingContext) -> Dict:
        """Convert FarmingContext to dictionary"""
        return {
            'user_id': context.user_id,
            'location': context.location,
            'primary_crops': context.primary_crops,
            'secondary_crops': context.secondary_crops,
            'farm_size_acres': context.farm_size_acres,
            'soil_type': context.soil_type,
            'irrigation_method': context.irrigation_method,
            'last_irrigation': context.last_irrigation.isoformat() if context.last_irrigation else None,
            'irrigation_frequency_days': context.irrigation_frequency_days,
            'fertilizer_schedule': context.fertilizer_schedule,
            'crop_stages': {k: v.value for k, v in context.crop_stages.items()},
            'planting_dates': {k: v.isoformat() for k, v in context.planting_dates.items()},
            'harvest_dates': {k: v.isoformat() for k, v in context.harvest_dates.items()},
            'preferred_language': context.preferred_language,
            'farming_experience': context.farming_experience,
            'created_at': context.created_at.isoformat(),
            'updated_at': context.updated_at.isoformat()
        }
    
    def _dict_to_farming_context(self, data: Dict) -> FarmingContext:
        """Convert dictionary to FarmingContext"""
        return FarmingContext(
            user_id=data['user_id'],
            location=data['location'],
            primary_crops=data['primary_crops'],
            secondary_crops=data['secondary_crops'],
            farm_size_acres=data['farm_size_acres'],
            soil_type=data['soil_type'],
            irrigation_method=data['irrigation_method'],
            last_irrigation=datetime.fromisoformat(data['last_irrigation']) if data['last_irrigation'] else None,
            irrigation_frequency_days=data['irrigation_frequency_days'],
            fertilizer_schedule=data['fertilizer_schedule'],
            crop_stages={k: CropStage(v) for k, v in data['crop_stages'].items()},
            planting_dates={k: datetime.fromisoformat(v) for k, v in data['planting_dates'].items()},
            harvest_dates={k: datetime.fromisoformat(v) for k, v in data['harvest_dates'].items()},
            preferred_language=data['preferred_language'],
            farming_experience=data['farming_experience'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )

# Global contextual memory service
contextual_memory_service = ContextualMemoryService()
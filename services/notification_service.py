# services/notification_service.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid

class NotificationType(Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    SUCCESS = "success"
    MARKET_UPDATE = "market_update"
    WEATHER_ALERT = "weather_alert"
    IRRIGATION_REMINDER = "irrigation_reminder"

@dataclass
class Notification:
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    data: Dict[str, Any]
    read: bool
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value,
            'data': self.data,
            'read': self.read,
            'created_at': self.created_at.isoformat()
        }

class NotificationService:
    """Service for managing user notifications"""
    
    def __init__(self, db_path: str = "notifications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize notifications database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL,
            data TEXT,  -- JSON data
            read BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL
        )''')
        
        # Index for faster queries
        c.execute('''CREATE INDEX IF NOT EXISTS idx_user_notifications 
                    ON notifications(user_id, created_at DESC)''')
        
        conn.commit()
        conn.close()
    
    def create_notification(self, user_id: str, title: str, message: str, 
                          notification_type: NotificationType, data: Dict[str, Any] = None) -> str:
        """Create a new notification"""
        notification_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO notifications 
                    (id, user_id, title, message, type, data, read, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (notification_id, user_id, title, message, notification_type.value,
                  json.dumps(data) if data else None, False, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return notification_id
    
    def get_user_notifications(self, user_id: str, limit: int = 20, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        query = "SELECT * FROM notifications WHERE user_id = ?"
        params = [user_id]
        
        if unread_only:
            query += " AND read = FALSE"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'message': row[3],
                'type': row[4],
                'data': json.loads(row[5]) if row[5] else {},
                'read': bool(row[6]),
                'created_at': row[7]
            })
        
        return notifications
    
    def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark a notification as read"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''UPDATE notifications SET read = TRUE 
                    WHERE id = ? AND user_id = ?''',
                 (notification_id, user_id))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def mark_all_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''UPDATE notifications SET read = TRUE 
                    WHERE user_id = ? AND read = FALSE''', (user_id,))
        
        count = c.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """Delete a notification"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''DELETE FROM notifications 
                    WHERE id = ? AND user_id = ?''',
                 (notification_id, user_id))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT COUNT(*) FROM notifications 
                    WHERE user_id = ? AND read = FALSE''', (user_id,))
        
        count = c.fetchone()[0]
        conn.close()
        
        return count
    
    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Clean up old notifications"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        cutoff_date = datetime.now().replace(day=datetime.now().day - days)
        
        c.execute('''DELETE FROM notifications 
                    WHERE created_at < ? AND read = TRUE''',
                 (cutoff_date.isoformat(),))
        
        count = c.rowcount
        conn.commit()
        conn.close()
        
        return count
    
    def send_irrigation_reminder(self, user_id: str, crop: str, days_since_last: int):
        """Send irrigation reminder notification"""
        title = f"🚰 Irrigation Reminder - {crop}"
        message = f"It's been {days_since_last} days since your last irrigation for {crop}. Consider checking soil moisture levels."
        
        self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.IRRIGATION_REMINDER,
            data={'crop': crop, 'days_since_last': days_since_last}
        )
    
    def send_weather_alert(self, user_id: str, alert_type: str, message: str, data: Dict[str, Any]):
        """Send weather-related alert"""
        title = f"🌤️ Weather Alert - {alert_type.title()}"
        
        self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.WEATHER_ALERT,
            data=data
        )
    
    def send_market_update(self, user_id: str, crop: str, price_change: float, current_price: float):
        """Send market price update"""
        direction = "📈" if price_change > 0 else "📉"
        title = f"{direction} Market Update - {crop}"
        message = f"{crop} price {'increased' if price_change > 0 else 'decreased'} by {abs(price_change):.1f}% to ₹{current_price}/quintal"
        
        self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.MARKET_UPDATE,
            data={'crop': crop, 'price_change': price_change, 'current_price': current_price}
        )

# Global notification service
notification_service = NotificationService()
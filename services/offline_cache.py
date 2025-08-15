# services/offline_cache.py
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class OfflineCache:
    def __init__(self, cache_dir="offline_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.init_cache_db()
        self.memory_cache = {}  # In-memory cache for frequently accessed data
        self.max_memory_items = 100
    
    def init_cache_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(os.path.join(self.cache_dir, "cache.db"))
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS cache_entries (
            key TEXT PRIMARY KEY,
            data TEXT,
            timestamp TEXT,
            expiry TEXT,
            access_count INTEGER DEFAULT 0,
            last_accessed TEXT
        )''')
        
        conn.commit()
        conn.close()
    
    def set(self, key: str, data: Any, expiry_hours: int = 24) -> bool:
        """Cache data with expiry"""
        try:
            # Update memory cache
            if len(self.memory_cache) >= self.max_memory_items:
                # Remove oldest item
                oldest_key = min(self.memory_cache.keys(), 
                               key=lambda k: self.memory_cache[k].get('last_accessed', ''))
                del self.memory_cache[oldest_key]
            
            self.memory_cache[key] = {
                'data': data,
                'expiry': (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
                'last_accessed': datetime.now().isoformat()
            }
            
            # Update database cache
            conn = sqlite3.connect(os.path.join(self.cache_dir, "cache.db"))
            c = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            expiry = (datetime.now() + timedelta(hours=expiry_hours)).isoformat()
            
            c.execute('''INSERT OR REPLACE INTO cache_entries 
                        (key, data, timestamp, expiry, access_count, last_accessed) 
                        VALUES (?, ?, ?, ?, 1, ?)''',
                     (key, json.dumps(data), timestamp, expiry, timestamp))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        try:
            # Check memory cache first
            if key in self.memory_cache:
                cached_item = self.memory_cache[key]
                if datetime.now() < datetime.fromisoformat(cached_item['expiry']):
                    cached_item['last_accessed'] = datetime.now().isoformat()
                    return cached_item['data']
                else:
                    del self.memory_cache[key]
            
            # Check database cache
            conn = sqlite3.connect(os.path.join(self.cache_dir, "cache.db"))
            c = conn.cursor()
            
            c.execute('SELECT data, expiry, access_count FROM cache_entries WHERE key = ?', (key,))
            result = c.fetchone()
            
            if result:
                data, expiry, access_count = result
                if datetime.now() < datetime.fromisoformat(expiry):
                    # Update access count and last accessed
                    c.execute('UPDATE cache_entries SET access_count = ?, last_accessed = ? WHERE key = ?',
                             (access_count + 1, datetime.now().isoformat(), key))
                    conn.commit()
                    conn.close()
                    
                    parsed_data = json.loads(data)
                    # Add to memory cache for faster future access
                    self.memory_cache[key] = {
                        'data': parsed_data,
                        'expiry': expiry,
                        'last_accessed': datetime.now().isoformat()
                    }
                    return json.loads(data)
                else:
                    self.delete(key)  # Remove expired entry
            
            conn.close()
            
            return None
        except Exception as e:
            print(f"Cache get error: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cached entry"""
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from database cache
            conn = sqlite3.connect(os.path.join(self.cache_dir, "cache.db"))
            c = conn.cursor()
            c.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Cache delete error: {str(e)}")
            return False
    
    def clear_expired(self) -> int:
        """Clear all expired entries and return count of cleared items"""
        try:
            current_time = datetime.now().isoformat()
            
            # Clear from memory cache
            expired_memory_keys = [
                key for key, item in self.memory_cache.items()
                if datetime.now() >= datetime.fromisoformat(item['expiry'])
            ]
            for key in expired_memory_keys:
                del self.memory_cache[key]
            
            # Clear from database cache
            conn = sqlite3.connect(os.path.join(self.cache_dir, "cache.db"))
            c = conn.cursor()
            
            c.execute('SELECT COUNT(*) FROM cache_entries WHERE expiry < ?', (current_time,))
            expired_count = c.fetchone()[0]
            
            c.execute('DELETE FROM cache_entries WHERE expiry < ?', (current_time,))
            conn.commit()
            conn.close()
            
            return expired_count + len(expired_memory_keys)
        except Exception as e:
            print(f"Cache cleanup error: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(os.path.join(self.cache_dir, "cache.db"))
            c = conn.cursor()
            
            c.execute('SELECT COUNT(*) FROM cache_entries')
            total_entries = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM cache_entries WHERE expiry > ?', 
                     (datetime.now().isoformat(),))
            valid_entries = c.fetchone()[0]
            
            c.execute('SELECT AVG(access_count) FROM cache_entries')
            avg_access = c.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'expired_entries': total_entries - valid_entries,
                'memory_cache_size': len(self.memory_cache),
                'average_access_count': round(avg_access, 2)
            }
        except Exception as e:
            print(f"Cache stats error: {str(e)}")
            return {}

# Global cache instance
offline_cache = OfflineCache()
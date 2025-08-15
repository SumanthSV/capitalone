# services/community_features.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class PostType(Enum):
    QUESTION = "question"
    TIP = "tip"
    SUCCESS_STORY = "success_story"
    MARKET_UPDATE = "market_update"

@dataclass
class Post:
    post_id: str
    user_id: str
    author_name: str
    title: str
    content: str
    post_type: PostType
    location: Optional[str]
    crops_mentioned: List[str]
    likes: int
    views: int
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'post_id': self.post_id,
            'user_id': self.user_id,
            'author_name': self.author_name,
            'title': self.title,
            'content': self.content,
            'post_type': self.post_type.value,
            'location': self.location,
            'crops_mentioned': self.crops_mentioned,
            'likes': self.likes,
            'views': self.views,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class Comment:
    comment_id: str
    post_id: str
    user_id: str
    author_name: str
    content: str
    likes: int
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'comment_id': self.comment_id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'author_name': self.author_name,
            'content': self.content,
            'likes': self.likes,
            'created_at': self.created_at.isoformat()
        }

class CommunityService:
    """Service for managing community features"""
    
    def __init__(self, db_path: str = "community.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize community database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Posts table
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            post_type TEXT NOT NULL,
            location TEXT,
            crops_mentioned TEXT,  -- JSON array
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        # Comments table
        c.execute('''CREATE TABLE IF NOT EXISTS comments (
            comment_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        )''')
        
        # Likes table
        c.execute('''CREATE TABLE IF NOT EXISTS likes (
            like_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            post_id TEXT,
            comment_id TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, post_id),
            UNIQUE(user_id, comment_id)
        )''')
        
        conn.commit()
        conn.close()
    
    def create_post(self, user_id: str, data: Dict[str, Any]) -> Post:
        """Create a new community post"""
        # Get author name from user service
        from services.auth import auth_service
        user = auth_service.get_user_by_id(user_id)
        author_name = user.name if user else "Anonymous"
        
        post = Post(
            post_id=str(uuid.uuid4()),
            user_id=user_id,
            author_name=author_name,
            title=data['title'],
            content=data['content'],
            post_type=PostType(data['post_type']),
            location=data.get('location'),
            crops_mentioned=data.get('crops_mentioned', []) if isinstance(data.get('crops_mentioned', []), list) else data.get('crops_mentioned', '').split(','),
            likes=0,
            views=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self._save_post(post)
        return post
    
    def get_posts(self, filters: Dict[str, Any] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get community posts with optional filters"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        query = "SELECT * FROM posts"
        params = []
        
        if filters:
            conditions = []
            if 'post_type' in filters:
                conditions.append("post_type = ?")
                params.append(filters['post_type'])
            if 'location' in filters:
                conditions.append("location LIKE ?")
                params.append(f"%{filters['location']}%")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        c.execute(query, params)
        rows = c.fetchall()
        
        posts = []
        for row in rows:
            # Get comment count
            c.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (row[0],))
            comment_count = c.fetchone()[0]
            
            post_dict = {
                'post_id': row[0],
                'user_id': row[1],
                'author_name': row[2],
                'title': row[3],
                'content': row[4],
                'post_type': row[5],
                'location': row[6],
                'crops_mentioned': json.loads(row[7]) if row[7] else [],
                'likes': row[8],
                'views': row[9],
                'created_at': row[10],
                'updated_at': row[11],
                'comment_count': comment_count
            }
            posts.append(post_dict)
        
        conn.close()
        return posts
    
    def get_post_details(self, post_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get detailed post information with comments"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get post
        c.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
        post_row = c.fetchone()
        
        if not post_row:
            conn.close()
            return None
        
        # Increment view count
        c.execute("UPDATE posts SET views = views + 1 WHERE post_id = ?", (post_id,))
        
        # Get comments
        c.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY created_at ASC", (post_id,))
        comment_rows = c.fetchall()
        
        comments = []
        for row in comment_rows:
            comments.append({
                'comment_id': row[0],
                'post_id': row[1],
                'user_id': row[2],
                'author_name': row[3],
                'content': row[4],
                'likes': row[5],
                'created_at': row[6]
            })
        
        # Check if user liked the post
        user_liked = False
        if user_id:
            c.execute("SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
            user_liked = c.fetchone() is not None
        
        conn.commit()
        conn.close()
        
        return {
            'post_id': post_row[0],
            'user_id': post_row[1],
            'author_name': post_row[2],
            'title': post_row[3],
            'content': post_row[4],
            'post_type': post_row[5],
            'location': post_row[6],
            'crops_mentioned': json.loads(post_row[7]) if post_row[7] else [],
            'likes': post_row[8],
            'views': post_row[9] + 1,  # Include the increment
            'created_at': post_row[10],
            'updated_at': post_row[11],
            'comments': comments,
            'user_liked': user_liked
        }
    
    def add_comment(self, user_id: str, post_id: str, content: str) -> Comment:
        """Add comment to a post"""
        # Get author name
        from services.auth import auth_service
        user = auth_service.get_user_by_id(user_id)
        author_name = user.name if user else "Anonymous"
        
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
            author_name=author_name,
            content=content,
            likes=0,
            created_at=datetime.now()
        )
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO comments 
                    (comment_id, post_id, user_id, author_name, content, likes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (comment.comment_id, comment.post_id, comment.user_id,
                  comment.author_name, comment.content, comment.likes,
                  comment.created_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        return comment
    
    def like_post(self, user_id: str, post_id: str) -> bool:
        """Toggle like on a post"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if already liked
        c.execute("SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        already_liked = c.fetchone() is not None
        
        if already_liked:
            # Unlike
            c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
            c.execute("UPDATE posts SET likes = likes - 1 WHERE post_id = ?", (post_id,))
            liked = False
        else:
            # Like
            like_id = str(uuid.uuid4())
            c.execute("INSERT INTO likes (like_id, user_id, post_id, created_at) VALUES (?, ?, ?, ?)",
                     (like_id, user_id, post_id, datetime.now().isoformat()))
            c.execute("UPDATE posts SET likes = likes + 1 WHERE post_id = ?", (post_id,))
            liked = True
        
        conn.commit()
        conn.close()
        
        return liked
    
    def get_trending_posts(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending posts based on likes and views"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Calculate trending score: (likes * 2 + views) / days_old
        query = '''
        SELECT *, 
               (likes * 2 + views) / 
               (CASE WHEN (julianday('now') - julianday(created_at)) < 1 
                     THEN 1 
                     ELSE (julianday('now') - julianday(created_at)) 
                END) as trending_score
        FROM posts 
        WHERE julianday('now') - julianday(created_at) <= ?
        ORDER BY trending_score DESC 
        LIMIT ?
        '''
        
        c.execute(query, (days, limit))
        rows = c.fetchall()
        
        posts = []
        for row in rows:
            posts.append({
                'post_id': row[0],
                'user_id': row[1],
                'author_name': row[2],
                'title': row[3],
                'content': row[4],
                'post_type': row[5],
                'location': row[6],
                'crops_mentioned': json.loads(row[7]) if row[7] else [],
                'likes': row[8],
                'views': row[9],
                'created_at': row[10],
                'updated_at': row[11],
                'trending_score': row[12]
            })
        
        conn.close()
        return posts
    
    def _save_post(self, post: Post):
        """Save post to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO posts 
                    (post_id, user_id, author_name, title, content, post_type,
                     location, crops_mentioned, likes, views, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (post.post_id, post.user_id, post.author_name, post.title,
                  post.content, post.post_type.value, post.location,
                  json.dumps(post.crops_mentioned), post.likes, post.views,
                  post.created_at.isoformat(), post.updated_at.isoformat()))
        
        conn.commit()
        conn.close()

# Global community service
community_service = CommunityService()
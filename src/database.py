"""
Database management for the Reddit Topic Modeling System.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import RedditPost, PostEmbedding
from .config import config

class DatabaseManager:
    """Manages SQLite database operations for Reddit posts and embeddings."""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager."""
        self.db_path = db_path or config.database.database_path
        self.ensure_database_directory()
        self.init_database()
    
    def ensure_database_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    author TEXT,
                    subreddit TEXT NOT NULL,
                    score INTEGER,
                    num_comments INTEGER,
                    created_utc TEXT NOT NULL,
                    url TEXT,
                    permalink TEXT,
                    is_self BOOLEAN,
                    upvote_ratio REAL,
                    inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create embeddings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts (subreddit)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts (created_utc)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_embeddings_post_id ON embeddings (post_id)')
            
            conn.commit()
    
    def insert_post(self, post: RedditPost) -> bool:
        """Insert a Reddit post into the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO posts 
                    (id, title, content, author, subreddit, score, num_comments, 
                     created_utc, url, permalink, is_self, upvote_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.id, post.title, post.content, post.author, post.subreddit,
                    post.score, post.num_comments, post.created_utc.isoformat(),
                    post.url, post.permalink, post.is_self, post.upvote_ratio
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error inserting post {post.id}: {e}")
                return False
    
    def insert_posts_batch(self, posts: List[RedditPost]) -> int:
        """Insert multiple posts in a batch."""
        inserted_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for post in posts:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO posts 
                        (id, title, content, author, subreddit, score, num_comments, 
                         created_utc, url, permalink, is_self, upvote_ratio)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        post.id, post.title, post.content, post.author, post.subreddit,
                        post.score, post.num_comments, post.created_utc.isoformat(),
                        post.url, post.permalink, post.is_self, post.upvote_ratio
                    ))
                    inserted_count += 1
                except sqlite3.Error as e:
                    print(f"Error inserting post {post.id}: {e}")
            conn.commit()
        return inserted_count
    
    def insert_embedding(self, embedding: PostEmbedding) -> bool:
        """Insert a post embedding into the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO embeddings (post_id, embedding, model_name, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    embedding.post_id, embedding.to_dict()['embedding'],
                    embedding.model_name, embedding.created_at.isoformat()
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error inserting embedding for post {embedding.post_id}: {e}")
                return False
    
    def get_posts_by_subreddit(self, subreddit: str, limit: int = 100) -> List[RedditPost]:
        """Get posts by subreddit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM posts 
                WHERE subreddit = ? 
                ORDER BY created_utc DESC 
                LIMIT ?
            ''', (subreddit, limit))
            
            rows = cursor.fetchall()
            return [self._row_to_post(row) for row in rows]
    
    def get_posts_without_embeddings(self) -> List[RedditPost]:
        """Get posts that don't have embeddings yet."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.* FROM posts p
                LEFT JOIN embeddings e ON p.id = e.post_id
                WHERE e.post_id IS NULL
            ''')
            
            rows = cursor.fetchall()
            return [self._row_to_post(row) for row in rows]
    
    def get_post_by_id(self, post_id: str) -> Optional[RedditPost]:
        """Get a specific post by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
            row = cursor.fetchone()
            return self._row_to_post(row) if row else None
    
    def get_posts_count(self, subreddit: str = None) -> int:
        """Get total count of posts, optionally filtered by subreddit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if subreddit:
                cursor.execute('SELECT COUNT(*) FROM posts WHERE subreddit = ?', (subreddit,))
            else:
                cursor.execute('SELECT COUNT(*) FROM posts')
            return cursor.fetchone()[0]
    
    def get_embeddings_by_subreddit(self, subreddit: str = None) -> List[PostEmbedding]:
        """Get embeddings, optionally filtered by subreddit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if subreddit:
                cursor.execute('''
                    SELECT e.* FROM embeddings e
                    JOIN posts p ON e.post_id = p.id
                    WHERE p.subreddit = ?
                ''', (subreddit,))
            else:
                cursor.execute('SELECT * FROM embeddings')
            
            rows = cursor.fetchall()
            return [self._row_to_embedding(row) for row in rows]
    
    def get_all_embeddings(self) -> List[PostEmbedding]:
        """Get all embeddings from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM embeddings')
            rows = cursor.fetchall()
            return [self._row_to_embedding(row) for row in rows]
    
    def get_posts_with_embeddings(self, subreddit: str = None) -> List[tuple]:
        """Get posts along with their embeddings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if subreddit:
                cursor.execute('''
                    SELECT p.*, e.embedding, e.model_name, e.created_at as embedding_created_at
                    FROM posts p
                    JOIN embeddings e ON p.id = e.post_id
                    WHERE p.subreddit = ?
                    ORDER BY p.created_utc DESC
                ''', (subreddit,))
            else:
                cursor.execute('''
                    SELECT p.*, e.embedding, e.model_name, e.created_at as embedding_created_at
                    FROM posts p
                    JOIN embeddings e ON p.id = e.post_id
                    ORDER BY p.created_utc DESC
                ''')
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                post = self._row_to_post(row)
                import json
                embedding = PostEmbedding(
                    post_id=row['id'],
                    embedding=json.loads(row['embedding']),  # Convert string back to list
                    model_name=row['model_name'],
                    created_at=datetime.fromisoformat(row['embedding_created_at'])
                )
                results.append((post, embedding))
            return results
    
    def _row_to_embedding(self, row: sqlite3.Row) -> PostEmbedding:
        """Convert database row to PostEmbedding object."""
        import json
        return PostEmbedding(
            post_id=row['post_id'],
            embedding=json.loads(row['embedding']),
            model_name=row['model_name'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    def _row_to_post(self, row: sqlite3.Row) -> RedditPost:
        """Convert database row to RedditPost object."""
        return RedditPost(
            id=row['id'],
            title=row['title'],
            content=row['content'] or '',
            author=row['author'] or '',
            subreddit=row['subreddit'],
            score=row['score'] or 0,
            num_comments=row['num_comments'] or 0,
            created_utc=datetime.fromisoformat(row['created_utc']),
            url=row['url'] or '',
            permalink=row['permalink'] or '',
            is_self=bool(row['is_self']),
            upvote_ratio=row['upvote_ratio'] or 0.0
        ) 
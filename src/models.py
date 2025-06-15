"""
Data models for the Reddit Topic Modeling System.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json

@dataclass
class RedditPost:
    """Represents a Reddit post."""
    id: str
    title: str
    content: str
    author: str
    subreddit: str
    score: int
    num_comments: int
    created_utc: datetime
    url: str
    permalink: str
    is_self: bool
    upvote_ratio: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'subreddit': self.subreddit,
            'score': self.score,
            'num_comments': self.num_comments,
            'created_utc': self.created_utc.isoformat(),
            'url': self.url,
            'permalink': self.permalink,
            'is_self': self.is_self,
            'upvote_ratio': self.upvote_ratio
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RedditPost':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            author=data['author'],
            subreddit=data['subreddit'],
            score=data['score'],
            num_comments=data['num_comments'],
            created_utc=datetime.fromisoformat(data['created_utc']),
            url=data['url'],
            permalink=data['permalink'],
            is_self=data['is_self'],
            upvote_ratio=data['upvote_ratio']
        )

@dataclass
class PostEmbedding:
    """Represents an embedding for a Reddit post."""
    post_id: str
    embedding: List[float]
    model_name: str
    created_at: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'post_id': self.post_id,
            'embedding': json.dumps(self.embedding),
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PostEmbedding':
        """Create from dictionary."""
        return cls(
            post_id=data['post_id'],
            embedding=json.loads(data['embedding']),
            model_name=data['model_name'],
            created_at=datetime.fromisoformat(data['created_at'])
        )

@dataclass
class SearchQuery:
    """Represents a search query configuration."""
    subreddit: str
    timespan: str  # 'day', 'week', 'month', 'year', 'all'
    keyword: Optional[str] = None
    limit: int = 100
    sort: str = 'hot'  # 'hot', 'new', 'top', 'rising'

@dataclass
class ClusterResult:
    """Represents clustering results."""
    post_ids: List[str]
    cluster_id: int
    centroid: List[float]
    size: int
    representative_posts: List[str]  # Top posts representing this cluster 
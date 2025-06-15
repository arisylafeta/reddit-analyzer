"""
Configuration management for the Reddit Topic Modeling System.
"""

import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables
load_dotenv()

@dataclass
class RedditConfig:
    """Reddit API configuration."""
    client_id: str
    client_secret: str
    user_agent: str

@dataclass
class OllamaConfig:
    """Ollama configuration."""
    base_url: str
    model: str

@dataclass
class DatabaseConfig:
    """Database configuration."""
    database_path: str
    vector_db_path: str

@dataclass
class AppConfig:
    """Main application configuration."""
    reddit: RedditConfig
    ollama: OllamaConfig
    database: DatabaseConfig
    http_proxy: Optional[str]
    https_proxy: Optional[str]

def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    reddit_config = RedditConfig(
        client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        user_agent=os.getenv("REDDIT_USER_AGENT", "RedditTopicModeler/1.0")
    )
    
    ollama_config = OllamaConfig(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama2")
    )
    
    database_config = DatabaseConfig(
        database_path=os.getenv("DATABASE_PATH", "./data/reddit_posts.db"),
        vector_db_path=os.getenv("VECTOR_DB_PATH", "./data/chroma_db")
    )
    
    return AppConfig(
        reddit=reddit_config,
        ollama=ollama_config,
        database=database_config,
        http_proxy=os.getenv("HTTP_PROXY"),
        https_proxy=os.getenv("HTTPS_PROXY"),
    )

# Global config instance
config = load_config()

def validate_config() -> bool:
    """Validate that all required configuration is present."""
    if not config.reddit.client_id or not config.reddit.client_secret:
        return False
    return True 
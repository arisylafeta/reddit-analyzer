#!/usr/bin/env python3
"""
Fetch Posts from Multiple Subreddits

This script fetches the last 1000 posts from r/lovable and r/vibecoding,
stores them in the database, and generates embeddings for semantic search.
"""

import sys
from typing import List

from src.config import config, validate_config
from src.reddit_client import RedditClient
from src.database import DatabaseManager
from src.embedding_service import EmbeddingService
from src.models import SearchQuery, RedditPost


def fetch_posts_from_subreddit(subreddit: str, limit: int = 1000) -> List[RedditPost]:
    """
    Fetch posts from a specific subreddit.
    
    Args:
        subreddit: Name of the subreddit (without 'r/')
        limit: Number of posts to fetch
        
    Returns:
        List of RedditPost objects
    """
    print(f"\n📥 Fetching {limit} posts from r/{subreddit}...")
    
    reddit_client = RedditClient()
    
    # Create search query for recent posts
    query = SearchQuery(
        subreddit=subreddit,
        timespan='all',  # Get posts from all time
        keyword=None,
        limit=limit,
        sort='new'  # Get newest posts first
    )
    
    # Fetch posts
    posts = reddit_client.fetch_posts(query)
    print(f"✅ Successfully fetched {len(posts)} posts from r/{subreddit}")
    
    return posts


def store_posts_in_database(posts: List[RedditPost]) -> int:
    """
    Store posts in the database.
    
    Args:
        posts: List of RedditPost objects
        
    Returns:
        Number of posts successfully stored
    """
    if not posts:
        return 0
    
    print(f"💾 Storing {len(posts)} posts in database...")
    
    db = DatabaseManager()
    stored_count = db.insert_posts_batch(posts)
    
    print(f"✅ Successfully stored {stored_count} posts in database")
    return stored_count


def generate_embeddings_for_posts(subreddit: str = None) -> int:
    """
    Generate embeddings for posts that don't have them yet.
    
    Args:
        subreddit: Optional subreddit filter
        
    Returns:
        Number of embeddings generated
    """
    print(f"\n🔧 Generating embeddings for posts...")
    if subreddit:
        print(f"   Filtering by subreddit: r/{subreddit}")
    
    # Initialize services
    db = DatabaseManager()
    embedding_service = EmbeddingService()
    
    # Test Ollama connection
    if not embedding_service.test_connection():
        raise Exception("Cannot connect to Ollama. Make sure it's running: `ollama serve`")
    
    # Ensure model is available
    if not embedding_service.ensure_model_available():
        raise Exception(f"Model {embedding_service.model_name} is not available")
    
    # Get posts without embeddings
    posts = db.get_posts_without_embeddings()
    
    if subreddit:
        posts = [p for p in posts if p.subreddit.lower() == subreddit.lower()]
    
    if not posts:
        print("✅ All posts already have embeddings!")
        return 0
    
    print(f"   Found {len(posts)} posts without embeddings")
    
    # Generate embeddings in batches
    batch_size = 10
    total_generated = 0
    
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        print(f"   Processing batch {i//batch_size + 1}/{(len(posts) + batch_size - 1)//batch_size}...")
        
        # Generate embeddings for this batch
        post_embeddings = embedding_service.embed_posts(batch)
        
        # Store embeddings in database
        for embedding in post_embeddings:
            if db.insert_embedding(embedding):
                total_generated += 1
    
    print(f"✅ Successfully generated {total_generated} embeddings")
    return total_generated


def main():
    """Main function to fetch posts from both subreddits."""
    print("🚀 Reddit Posts Fetcher and Embedder")
    print("=" * 50)
    
    # Validate configuration
    if not validate_config():
        print("❌ Configuration incomplete!")
        print("Please ensure your .env file is properly configured with Reddit API credentials.")
        print("Get credentials from: https://www.reddit.com/prefs/apps")
        sys.exit(1)
    
    print("✅ Configuration validated")
    
    # Subreddits to fetch from
    subreddits = ['lovable', 'vibecoding']
    posts_per_subreddit = 1000
    
    try:
        # Initialize database
        db = DatabaseManager()
        print("✅ Database initialized")
        
        total_posts_fetched = 0
        total_posts_stored = 0
        
        # Fetch posts from each subreddit
        for subreddit in subreddits:
            try:
                # Fetch posts
                posts = fetch_posts_from_subreddit(subreddit, posts_per_subreddit)
                total_posts_fetched += len(posts)
                
                # Store in database
                stored_count = store_posts_in_database(posts)
                total_posts_stored += stored_count
                
                # Show current database stats
                total_in_db = db.get_posts_count(subreddit)
                print(f"📊 Total posts in database for r/{subreddit}: {total_in_db}")
                
            except Exception as e:
                print(f"❌ Error processing r/{subreddit}: {e}")
                continue
        
        print(f"\n📈 Summary:")
        print(f"   Total posts fetched: {total_posts_fetched}")
        print(f"   Total posts stored: {total_posts_stored}")
        
        # Generate embeddings for all posts
        print(f"\n🔧 Generating embeddings for all posts...")
        total_embeddings = generate_embeddings_for_posts()
        
        print(f"\n🎉 Process completed successfully!")
        print(f"   Posts in database: {db.get_posts_count()}")
        print(f"   Embeddings generated: {total_embeddings}")
        print(f"\nYou can now use semantic search:")
        print(f"   python semantic_search.py \"your search query\"")
        print(f"   python main.py search -q \"your search query\"")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
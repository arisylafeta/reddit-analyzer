#!/usr/bin/env python3
"""
Demo script for the Reddit Topic Modeling System.
This script demonstrates the complete workflow from fetching to embedding.
"""

import os
import time
from datetime import datetime

from src.config import config, validate_config
from src.reddit_client import RedditClient
from src.database import DatabaseManager
from src.embedding_service import EmbeddingService
from src.models import SearchQuery

def print_banner():
    """Print a nice banner."""
    print("=" * 60)
    print("🚀 Reddit Topic Modeling System - Demo")
    print("=" * 60)

def demo_reddit_fetch():
    """Demonstrate Reddit post fetching."""
    print("\n📥 Step 1: Fetching Reddit Posts")
    print("-" * 40)
    
    try:
        # Initialize Reddit client
        reddit_client = RedditClient()
        
        # Test connection
        if not reddit_client.test_connection():
            print("❌ Reddit API connection failed. Please check your credentials.")
            return None
        
        # Create a search query for a small dataset
        query = SearchQuery(
            subreddit="MachineLearning",
            timespan="week",
            keyword=None,
            limit=10,  # Small number for demo
            sort="hot"
        )
        
        # Fetch posts
        posts = reddit_client.fetch_posts(query)
        
        if posts:
            print(f"✅ Successfully fetched {len(posts)} posts")
            print("\nSample posts:")
            for i, post in enumerate(posts[:3], 1):
                print(f"{i}. {post.title[:60]}..." if len(post.title) > 60 else f"{i}. {post.title}")
                print(f"   Score: {post.score}, Comments: {post.num_comments}")
        
        return posts
        
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        return None

def demo_database_storage(posts):
    """Demonstrate database storage."""
    if not posts:
        print("\n⏭️  Skipping database demo (no posts to store)")
        return False
    
    print("\n💾 Step 2: Storing Posts in Database")
    print("-" * 40)
    
    try:
        # Initialize database
        db = DatabaseManager()
        
        # Store posts
        inserted_count = db.insert_posts_batch(posts)
        print(f"✅ Stored {inserted_count} posts in database")
        
        # Show database statistics
        total_posts = db.get_posts_count()
        posts_without_embeddings = len(db.get_posts_without_embeddings())
        
        print(f"📊 Database Statistics:")
        print(f"   Total posts: {total_posts}")
        print(f"   Posts without embeddings: {posts_without_embeddings}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with database: {e}")
        return False

def demo_embedding_generation():
    """Demonstrate embedding generation."""
    print("\n🔧 Step 3: Generating Embeddings")
    print("-" * 40)
    
    try:
        # Initialize services
        db = DatabaseManager()
        embedding_service = EmbeddingService()
        
        # Test Ollama connection
        if not embedding_service.test_connection():
            print("❌ Ollama connection failed. Make sure Ollama is running.")
            print("💡 Run: ollama serve")
            return False
        
        # Ensure model is available
        if not embedding_service.ensure_model_available():
            print("❌ Failed to setup embedding model")
            return False
        
        # Get posts without embeddings
        posts = db.get_posts_without_embeddings()
        
        if not posts:
            print("ℹ️  No posts without embeddings found")
            return True
        
        print(f"🔍 Found {len(posts)} posts without embeddings")
        
        # Generate embeddings (limit to first 5 for demo)
        demo_posts = posts[:5]
        print(f"📝 Generating embeddings for {len(demo_posts)} posts (demo limit)")
        
        post_embeddings = embedding_service.embed_posts(demo_posts)
        
        # Store embeddings
        stored_count = 0
        for embedding in post_embeddings:
            if db.insert_embedding(embedding):
                stored_count += 1
        
        print(f"✅ Generated and stored {stored_count} embeddings")
        
        # Show embedding statistics
        if post_embeddings:
            sample_embedding = post_embeddings[0]
            print(f"📊 Embedding Statistics:")
            print(f"   Model: {sample_embedding.model_name}")
            print(f"   Dimension: {len(sample_embedding.embedding)}")
            print(f"   Sample values: {sample_embedding.embedding[:5]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        return False

def demo_similarity_search():
    """Demonstrate similarity search."""
    print("\n🔍 Step 4: Similarity Search Demo")
    print("-" * 40)
    
    try:
        # Initialize services
        db = DatabaseManager()
        embedding_service = EmbeddingService()
        
        # Get a sample post with embedding
        posts = db.get_posts_by_subreddit("MachineLearning", limit=1)
        if not posts:
            print("ℹ️  No posts found for similarity search demo")
            return
        
        sample_post = posts[0]
        print(f"🎯 Using sample post: '{sample_post.title[:50]}...'")
        
        # Generate embedding for a query
        query = "machine learning neural networks"
        print(f"🔍 Searching for: '{query}'")
        
        query_embedding = embedding_service.generate_embedding(query)
        if not query_embedding:
            print("❌ Failed to generate query embedding")
            return
        
        # For demo purposes, just show the similarity computation
        sample_embedding = embedding_service.generate_embedding(sample_post.title)
        if sample_embedding:
            similarity = embedding_service.compute_similarity(query_embedding, sample_embedding)
            print(f"📊 Similarity score: {similarity:.4f}")
        
        print("ℹ️  Full similarity search requires vector database (coming in Phase 2)")
        
    except Exception as e:
        print(f"❌ Error in similarity search: {e}")

def main():
    """Run the complete demo."""
    print_banner()
    
    # Check configuration
    if not validate_config():
        print("❌ Configuration incomplete!")
        print("📝 Please:")
        print("   1. Copy config.env.example to .env")
        print("   2. Add your Reddit API credentials")
        print("   3. Make sure Ollama is running: ollama serve")
        return
    
    print("✅ Configuration loaded")
    
    # Step 1: Fetch posts
    posts = demo_reddit_fetch()
    
    # Step 2: Store in database
    if demo_database_storage(posts):
        print("✅ Database storage successful")
    
    # Step 3: Generate embeddings
    if demo_embedding_generation():
        print("✅ Embedding generation successful")
    
    # Step 4: Similarity search demo
    demo_similarity_search()
    
    # Final summary
    print("\n🎉 Demo Complete!")
    print("-" * 40)
    print("What you can do next:")
    print("• Run 'python main.py status' to see system statistics")
    print("• Fetch more posts: 'python main.py fetch -s [subreddit] -l 100'")
    print("• Generate more embeddings: 'python main.py embed'")
    print("• Check the data/ directory for your database files")
    print("\nHappy topic modeling! 🚀")

if __name__ == "__main__":
    main() 
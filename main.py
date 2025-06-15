#!/usr/bin/env python3
"""
Main CLI interface for the Reddit Topic Modeling System.
"""

import click
import os
from datetime import datetime
from typing import Optional

from src.config import config, validate_config
from src.reddit_client import RedditClient
from src.database import DatabaseManager
from src.embedding_service import EmbeddingService
from src.models import SearchQuery

@click.group()
def cli():
    """Reddit Topic Modeling System - Fetch, embed, and analyze Reddit posts."""
    pass

@cli.command()
def setup():
    """Setup the system and test connections."""
    click.echo("🚀 Setting up Reddit Topic Modeling System...")
    
    # Check configuration
    if not validate_config():
        click.echo("❌ Configuration incomplete!")
        click.echo("Please copy config.env.example to .env and fill in your Reddit API credentials.")
        click.echo("Get credentials from: https://www.reddit.com/prefs/apps")
        return
    
    click.echo("✅ Configuration loaded")
    
    # Test Reddit API connection
    try:
        reddit_client = RedditClient()
        if reddit_client.test_connection():
            click.echo("✅ Reddit API connection successful")
        else:
            click.echo("❌ Reddit API connection failed")
            return
    except Exception as e:
        click.echo(f"❌ Reddit API error: {e}")
        return
    
    # Test Ollama connection
    embedding_service = EmbeddingService()
    if embedding_service.test_connection():
        click.echo("✅ Ollama connection successful")
        if embedding_service.ensure_model_available():
            click.echo(f"✅ Model {embedding_service.model_name} is available")
        else:
            click.echo(f"❌ Model {embedding_service.model_name} setup failed")
    else:
        click.echo("❌ Ollama connection failed")
        click.echo("Make sure Ollama is running: `ollama serve`")
        return
    
    # Initialize database
    try:
        db = DatabaseManager()
        click.echo("✅ Database initialized")
    except Exception as e:
        click.echo(f"❌ Database error: {e}")
        return
    
    click.echo("🎉 Setup complete! You're ready to fetch and analyze Reddit posts.")

@cli.command()
@click.option('--subreddit', '-s', required=True, help='Subreddit to fetch from')
@click.option('--timespan', '-t', default='week', 
              type=click.Choice(['day', 'week', 'month', 'year', 'all']),
              help='Time period for posts')
@click.option('--keyword', '-k', help='Optional keyword filter')
@click.option('--limit', '-l', default=100, help='Number of posts to fetch')
@click.option('--sort', default='hot',
              type=click.Choice(['hot', 'new', 'top', 'rising']),
              help='Sort method for posts')
def fetch(subreddit: str, timespan: str, keyword: Optional[str], limit: int, sort: str):
    """Fetch posts from Reddit and store in database."""
    click.echo(f"📥 Fetching posts from r/{subreddit}...")
    
    # Validate configuration
    if not validate_config():
        click.echo("❌ Please run 'python main.py setup' first")
        return
    
    try:
        # Initialize services
        reddit_client = RedditClient()
        db = DatabaseManager()
        
        # Create search query
        query = SearchQuery(
            subreddit=subreddit,
            timespan=timespan,
            keyword=keyword,
            limit=limit,
            sort=sort
        )
        
        # Fetch posts
        posts = reddit_client.fetch_posts(query)
        
        if not posts:
            click.echo("No posts found matching your criteria.")
            return
        
        # Store in database
        inserted_count = db.insert_posts_batch(posts)
        click.echo(f"✅ Stored {inserted_count} posts in database")
        
        # Show summary
        total_posts = db.get_posts_count(subreddit)
        click.echo(f"📊 Total posts in database for r/{subreddit}: {total_posts}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--subreddit', '-s', help='Filter by subreddit (optional)')
@click.option('--batch-size', '-b', default=10, help='Batch size for embedding generation')
def embed(subreddit: Optional[str], batch_size: int):
    """Generate embeddings for posts without embeddings."""
    click.echo("🔧 Generating embeddings for posts...")
    
    try:
        # Initialize services
        db = DatabaseManager()
        embedding_service = EmbeddingService()
        
        # Get posts without embeddings
        posts = db.get_posts_without_embeddings()
        
        if subreddit:
            posts = [p for p in posts if p.subreddit.lower() == subreddit.lower()]
        
        if not posts:
            click.echo("No posts found without embeddings.")
            return
        
        click.echo(f"Found {len(posts)} posts without embeddings")
        
        # Generate embeddings
        post_embeddings = embedding_service.embed_posts(posts)
        
        # Store embeddings in database
        stored_count = 0
        for embedding in post_embeddings:
            if db.insert_embedding(embedding):
                stored_count += 1
        
        click.echo(f"✅ Generated and stored {stored_count} embeddings")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--subreddit', '-s', help='Filter by subreddit (optional)')
def status(subreddit: Optional[str]):
    """Show system status and statistics."""
    click.echo("📊 System Status")
    click.echo("=" * 50)
    
    try:
        db = DatabaseManager()
        
        # Post statistics
        if subreddit:
            post_count = db.get_posts_count(subreddit)
            click.echo(f"Posts in r/{subreddit}: {post_count}")
        else:
            post_count = db.get_posts_count()
            click.echo(f"Total posts: {post_count}")
        
        # Posts without embeddings
        posts_without_embeddings = len(db.get_posts_without_embeddings())
        click.echo(f"Posts without embeddings: {posts_without_embeddings}")
        
        # Database file size
        if os.path.exists(config.database.database_path):
            size_mb = os.path.getsize(config.database.database_path) / (1024 * 1024)
            click.echo(f"Database size: {size_mb:.2f} MB")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--subreddit', '-s', help='Filter by subreddit (optional)')
@click.option('--top-k', '-k', default=10, help='Number of results to return')
def search(query: str, subreddit: Optional[str], top_k: int):
    """Search for similar posts using embeddings."""
    click.echo(f"🔍 Searching for posts similar to: '{query}'")
    
    try:
        # Initialize services
        db = DatabaseManager()
        embedding_service = EmbeddingService()
        
        # Generate embedding for query
        query_embedding = embedding_service.generate_embedding(query)
        if not query_embedding:
            click.echo("Failed to generate embedding for query")
            return
        
        # Get posts with embeddings
        posts_with_embeddings = db.get_posts_with_embeddings(subreddit)
        
        if not posts_with_embeddings:
            click.echo("No posts with embeddings found.")
            if subreddit:
                click.echo(f"Try running: python main.py embed -s {subreddit}")
            else:
                click.echo("Try running: python main.py embed")
            return
        
        # Extract embeddings for similarity search
        post_embeddings = [embedding for _, embedding in posts_with_embeddings]
        
        # Find similar posts
        similar_posts = embedding_service.find_similar_posts(
            query_embedding, post_embeddings, top_k
        )
        
        if not similar_posts:
            click.echo("No similar posts found.")
            return
        
        # Display results
        click.echo(f"\n📋 Top {len(similar_posts)} similar posts:")
        click.echo("=" * 80)
        
        # Create a lookup dict for posts
        post_lookup = {post.id: post for post, _ in posts_with_embeddings}
        
        for i, (post_id, similarity) in enumerate(similar_posts, 1):
            post = post_lookup.get(post_id)
            if post:
                click.echo(f"\n{i}. [{similarity:.3f}] r/{post.subreddit}")
                click.echo(f"   Title: {post.title}")
                click.echo(f"   Score: {post.score} | Comments: {post.num_comments}")
                click.echo(f"   URL: {post.permalink}")
                if post.content and len(post.content) > 100:
                    click.echo(f"   Content: {post.content[:100]}...")
                elif post.content:
                    click.echo(f"   Content: {post.content}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")

if __name__ == '__main__':
    cli() 
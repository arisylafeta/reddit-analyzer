#!/usr/bin/env python3
"""
Semantic Search Script for Reddit Posts

This script allows you to search for semantically similar posts
based on your query using the embeddings stored in the database.
"""

import argparse
import sys
from typing import List, Optional

from src.config import config, validate_config
from src.database import DatabaseManager
from src.embedding_service import EmbeddingService
from src.models import RedditPost, PostEmbedding


def search_similar_posts(query: str, subreddit: Optional[str] = None, top_k: int = 10) -> List[tuple]:
    """
    Search for posts semantically similar to the given query.
    
    Args:
        query: The search query text
        subreddit: Optional subreddit filter
        top_k: Number of results to return
        
    Returns:
        List of tuples containing (post, similarity_score)
    """
    # Initialize services
    db = DatabaseManager()
    embedding_service = EmbeddingService()
    
    print(f"🔍 Searching for posts similar to: '{query}'")
    if subreddit:
        print(f"   Filtering by subreddit: r/{subreddit}")
    
    # Generate embedding for query
    print("📊 Generating embedding for query...")
    query_embedding = embedding_service.generate_embedding(query)
    if not query_embedding:
        raise Exception("Failed to generate embedding for query")
    
    # Get posts with embeddings
    print("📚 Loading posts with embeddings from database...")
    posts_with_embeddings = db.get_posts_with_embeddings(subreddit)
    
    if not posts_with_embeddings:
        if subreddit:
            raise Exception(f"No posts with embeddings found for r/{subreddit}")
        else:
            raise Exception("No posts with embeddings found in database")
    
    print(f"   Found {len(posts_with_embeddings)} posts with embeddings")
    
    # Extract embeddings for similarity search
    post_embeddings = [embedding for _, embedding in posts_with_embeddings]
    
    # Find similar posts
    print("🧮 Computing similarities...")
    similar_posts = embedding_service.find_similar_posts(
        query_embedding, post_embeddings, top_k
    )
    
    # Create a lookup dict for posts
    post_lookup = {post.id: post for post, _ in posts_with_embeddings}
    
    # Return posts with similarity scores
    results = []
    for post_id, similarity in similar_posts:
        post = post_lookup.get(post_id)
        if post:
            results.append((post, similarity))
    
    return results


def display_results(results: List[tuple], show_content: bool = True):
    """Display search results in a formatted way."""
    if not results:
        print("❌ No similar posts found.")
        return
    
    print(f"\n📋 Top {len(results)} similar posts:")
    print("=" * 100)
    
    for i, (post, similarity) in enumerate(results, 1):
        print(f"\n{i}. [Similarity: {similarity:.4f}] r/{post.subreddit}")
        print(f"   📝 Title: {post.title}")
        print(f"   📊 Score: {post.score} | 💬 Comments: {post.num_comments}")
        print(f"   👤 Author: {post.author}")
        print(f"   📅 Created: {post.created_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔗 URL: {post.permalink}")
        
        if show_content and post.content and post.content.strip():
            content = post.content.strip()
            if len(content) > 200:
                print(f"   📄 Content: {content[:200]}...")
            else:
                print(f"   📄 Content: {content}")
        
        print("-" * 80)


def main():
    """Main function for the semantic search script."""
    parser = argparse.ArgumentParser(
        description="Search for semantically similar Reddit posts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python semantic_search.py "machine learning algorithms"
  python semantic_search.py "web development" --subreddit lovable
  python semantic_search.py "coding best practices" --top-k 5 --no-content
        """
    )
    
    parser.add_argument(
        "query",
        help="The search query text"
    )
    
    parser.add_argument(
        "--subreddit", "-s",
        help="Filter results by subreddit (e.g., 'lovable', 'vibecoding')"
    )
    
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )
    
    parser.add_argument(
        "--no-content",
        action="store_true",
        help="Don't show post content in results"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    if not validate_config():
        print("❌ Configuration incomplete!")
        print("Please ensure your .env file is properly configured.")
        sys.exit(1)
    
    try:
        # Perform search
        results = search_similar_posts(
            query=args.query,
            subreddit=args.subreddit,
            top_k=args.top_k
        )
        
        # Display results
        display_results(results, show_content=not args.no_content)
        
        print(f"\n✅ Search completed! Found {len(results)} similar posts.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Research Automation Script for Multi-Subreddit Data Collection

This script collects Reddit posts from multiple subreddits using multiple search queries
for systematic research and analysis. It integrates with the existing Reddit Topic Modeling System.
"""

import sys
from datetime import datetime
from typing import List, Dict, Optional
import json

from src.reddit_client import RedditClient
from src.database import DatabaseManager
from src.embedding_service import EmbeddingService
from src.models import SearchQuery, RedditPost
from src.config import validate_config

# =============================================================================
# CONFIGURATION VARIABLES - MODIFY THESE TO CUSTOMIZE YOUR RESEARCH
# =============================================================================

# Subreddits to search (without 'r/' prefix)
SUBREDDITS = [
     'sales', 'SDRs' #, 'salesforce', 'SaaS', 'B2BSales',
    # 'entrepreneur', 'marketing', 'smallbusiness', 
    # 'productivity', 'remotework'
]

# Search keywords/queries to use in each subreddit
SEARCH_KEYWORDS = [
    'CRM frustrating',
    'sales tool alternatives',
    # 'manual data entry',
    # 'workflow automation',
    # 'AI for sales',
    # 'ChatGPT sales',
    # 'time consuming admin',
    # 'clunky interface',
    # 'better sales software',
    # 'productivity tools'
]

# Collection settings
POSTS_PER_KEYWORD = 200          # Max posts to collect per keyword per subreddit
TIMESPAN = 'month'               # 'day', 'week', 'month', 'year', 'all'
SORT_METHOD = 'relevance'        # 'relevance', 'hot', 'new', 'top'
COLLECT_COMMENTS = True          # Whether to collect comments for each post
COMMENTS_PER_POST = 2           # Max comments to collect per post
GENERATE_EMBEDDINGS = False       # Whether to generate AI embeddings (requires Ollama)

# =============================================================================

class ResearchAutomation:
    """Automated research pipeline for multi-subreddit data collection"""
    
    def __init__(self):
        """Initialize the research automation system."""
        # Validate configuration first
        if not validate_config():
            raise ValueError("Configuration incomplete. Please check your .env file.")
        
        self.db = DatabaseManager()
        self.reddit_client = RedditClient()
        self.embedding_service = EmbeddingService()

    def setup_database(self):
        """Initialize database - uses existing DatabaseManager setup"""
        print("📊 Setting up database...")
        # Database is already initialized in __init__, just confirm it's ready
        print("✅ Database ready!")

    def collect_posts_from_subreddits(self) -> Dict[str, int]:
        """
        Collect posts using the configured subreddits and keywords.
        For each subreddit, searches each keyword with POSTS_PER_KEYWORD limit.
        Automatically handles duplicates.
        
        Returns:
            Dictionary with collection statistics
        """
        print(f"📊 Starting collection from {len(SUBREDDITS)} subreddits using {len(SEARCH_KEYWORDS)} keywords...")
        print(f"   • Posts per keyword: {POSTS_PER_KEYWORD}")
        print(f"   • Max posts per subreddit: {len(SEARCH_KEYWORDS) * POSTS_PER_KEYWORD:,}")
        print(f"   • Comment collection: {'Enabled' if COLLECT_COMMENTS else 'Disabled'}")
        
        stats = {
            'total_collected': 0,
            'total_comments': 0,
            'by_subreddit': {},
            'by_keyword': {},
            'duplicates_skipped': 0,
            'errors': []
        }
        
        # Track processed post IDs to avoid duplicates
        processed_post_ids = set()
        
        for subreddit in SUBREDDITS:
            print(f"\n🔍 Processing r/{subreddit}...")
            subreddit_posts = 0
            subreddit_comments = 0
            
            for keyword in SEARCH_KEYWORDS:
                try:
                    print(f"  🔎 Searching '{keyword}'...", end=" ")
                    
                    posts = self.reddit_client.search_posts(
                        query=keyword,
                        subreddit=subreddit,
                        limit=POSTS_PER_KEYWORD,
                        sort=SORT_METHOD
                    )
                    
                    # Filter out duplicates
                    new_posts = []
                    duplicates = 0
                    for post in posts:
                        if post.id not in processed_post_ids:
                            new_posts.append(post)
                            processed_post_ids.add(post.id)
                        else:
                            duplicates += 1
                    
                    # Store posts and collect comments
                    stored_count, comments_count = self._store_posts_with_comments(
                        new_posts, f"search_{keyword}_r/{subreddit}"
                    )
                    
                    subreddit_posts += stored_count
                    subreddit_comments += comments_count
                    stats['duplicates_skipped'] += duplicates
                    
                    # Track by keyword
                    if keyword not in stats['by_keyword']:
                        stats['by_keyword'][keyword] = 0
                    stats['by_keyword'][keyword] += stored_count
                    
                    print(f"{stored_count} posts ({duplicates} duplicates)")
                    if COLLECT_COMMENTS and comments_count > 0:
                        print(f"    💬 {comments_count} comments collected")
                    
                except Exception as e:
                    error_msg = f"Error searching '{keyword}' in r/{subreddit}: {e}"
                    print(f"❌ {error_msg}")
                    stats['errors'].append(error_msg)
            
            stats['by_subreddit'][subreddit] = {
                'posts': subreddit_posts,
                'comments': subreddit_comments
            }
            stats['total_collected'] += subreddit_posts
            stats['total_comments'] += subreddit_comments
            
            print(f"  ✅ r/{subreddit} total: {subreddit_posts} posts, {subreddit_comments} comments")
        
        print(f"\n📈 Final Collection Summary:")
        print(f"  • Total posts collected: {stats['total_collected']:,}")
        print(f"  • Total comments collected: {stats['total_comments']:,}")
        print(f"  • Duplicates skipped: {stats['duplicates_skipped']:,}")
        print(f"  • Subreddits processed: {len(SUBREDDITS)}")
        print(f"  • Keywords used: {len(SEARCH_KEYWORDS)}")
        if stats['errors']:
            print(f"  • Errors encountered: {len(stats['errors'])}")
        
        return stats

    def _store_posts_with_comments(self, posts: List[RedditPost], source_tag: str) -> tuple[int, int]:
        """
        Store posts in database and optionally collect their comments.
        
        Args:
            posts: List of RedditPost objects
            source_tag: Tag to identify the source of these posts
            
        Returns:
            Tuple of (posts_stored, comments_collected)
        """
        if not posts:
            return 0, 0
            
        stored_count = 0
        total_comments = 0
        
        for post in posts:
            try:
                # Store post using existing database method
                success = self.db.insert_post(post)
                if success:
                    stored_count += 1
                    
                    # Collect comments if enabled
                    if COLLECT_COMMENTS:
                        try:
                            comments = self._collect_post_comments(post.id)
                            if comments:
                                self._store_comments(post.id, comments)
                                total_comments += len(comments)
                        except Exception as e:
                            print(f"    ⚠️  Error collecting comments for post {post.id}: {e}")
                            
            except Exception as e:
                print(f"    ⚠️  Error storing post {post.id}: {e}")
                continue
        
        return stored_count, total_comments

    def _collect_post_comments(self, post_id: str) -> List[Dict]:
        """
        Collect comments for a specific post.
        
        Args:
            post_id: Reddit post ID
            
        Returns:
            List of comment dictionaries
        """
        try:
            submission = self.reddit_client.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments" objects
            
            comments = []
            for comment in submission.comments.list()[:COMMENTS_PER_POST]:
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    comment_data = {
                        'id': comment.id,
                        'post_id': post_id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc),
                        'parent_id': comment.parent_id,
                        'is_submitter': comment.is_submitter
                    }
                    comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            print(f"    ⚠️  Error fetching comments for post {post_id}: {e}")
            return []

    def _store_comments(self, post_id: str, comments: List[Dict]):
        """
        Store comments in database.
        
        Args:
            post_id: Reddit post ID
            comments: List of comment dictionaries
        """
        # First, ensure comments table exists
        self._ensure_comments_table()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for comment in comments:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO comments 
                        (id, post_id, author, body, score, created_utc, parent_id, is_submitter)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        comment['id'], comment['post_id'], comment['author'], 
                        comment['body'], comment['score'], comment['created_utc'].isoformat(),
                        comment['parent_id'], comment['is_submitter']
                    ))
                except Exception as e:
                    print(f"    ⚠️  Error storing comment {comment['id']}: {e}")
            conn.commit()

    def _ensure_comments_table(self):
        """Ensure the comments table exists in the database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    author TEXT,
                    body TEXT NOT NULL,
                    score INTEGER,
                    created_utc TEXT NOT NULL,
                    parent_id TEXT,
                    is_submitter BOOLEAN,
                    inserted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            ''')
            
            # Create index for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments (post_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_created_utc ON comments (created_utc)')
            
            conn.commit()

    def generate_embeddings(self, subreddit_filter: Optional[str] = None) -> Dict[str, int]:
        """
        Generate embeddings for posts that don't have them yet.
        
        Args:
            subreddit_filter: Optional subreddit to filter posts
            
        Returns:
            Dictionary with embedding generation statistics
        """
        print("🧠 Generating embeddings for collected posts...")
        
        # Test embedding service connection
        if not self.embedding_service.test_connection():
            raise Exception("Cannot connect to Ollama. Please ensure it's running.")
        
        if not self.embedding_service.ensure_model_available():
            raise Exception("Embedding model not available.")
        
        # Get posts without embeddings
        posts_without_embeddings = self.db.get_posts_without_embeddings()
        
        if not posts_without_embeddings:
            print("✅ All posts already have embeddings!")
            return {'total_processed': 0, 'new_embeddings': 0}
        
        print(f"📊 Found {len(posts_without_embeddings)} posts without embeddings")
        
        # Generate embeddings in batches
        post_embeddings = self.embedding_service.embed_posts(posts_without_embeddings)
        
        # Store embeddings
        stored_count = 0
        for embedding in post_embeddings:
            try:
                success = self.db.insert_embedding(embedding)
                if success:
                    stored_count += 1
            except Exception as e:
                print(f"⚠️  Error storing embedding for post {embedding.post_id}: {e}")
        
        stats = {
            'total_processed': len(posts_without_embeddings),
            'new_embeddings': stored_count,
            'success_rate': (stored_count / len(posts_without_embeddings)) * 100 if posts_without_embeddings else 0
        }
        
        print(f"✅ Generated {stored_count} new embeddings ({stats['success_rate']:.1f}% success rate)")
        return stats

    def generate_collection_report(self, stats: Dict) -> str:
        """Generate a summary report of the collection process."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# Research Collection Report
Generated: {timestamp}

## Summary
- **Total Posts Collected**: {stats['total_collected']}
- **Subreddits Processed**: {len(stats['by_subreddit'])}
- **Search Queries Used**: {len(stats['by_query'])}
- **Errors Encountered**: {len(stats['errors'])}

## By Subreddit
"""
        
        for subreddit, count in stats['by_subreddit'].items():
            report += f"- r/{subreddit}: {count} posts\n"
        
        report += "\n## By Search Query\n"
        for query, count in stats['by_query'].items():
            report += f"- '{query}': {count} posts\n"
        
        if stats['errors']:
            report += "\n## Errors\n"
            for error in stats['errors']:
                report += f"- {error}\n"
        
        # Save report to file
        filename = f"collection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"📋 Collection report saved to {filename}")
        return report

def main():
    """Main research automation pipeline"""
    
    try:
        research = ResearchAutomation()
        
        print("🚀 Starting Multi-Subreddit Research Automation")
        print("=" * 50)
        
        # Setup database
        research.setup_database()
        
        # Test connections
        print("\n🔍 Testing connections...")
        if not research.reddit_client.test_connection():
            print("❌ Reddit connection failed. Please check your credentials.")
            return
        
        if not research.embedding_service.test_connection():
            print("⚠️  Ollama connection failed. Embeddings will be skipped.")
            print("   Make sure Ollama is running: `ollama serve`")
            generate_embeddings = False
        else:
            generate_embeddings = True
        
        # Data collection using configured parameters
        print("\n📊 Starting data collection...")
        stats = research.collect_posts_from_subreddits()
        
        # Generate embeddings if possible
        if GENERATE_EMBEDDINGS and generate_embeddings and stats['total_collected'] > 0:
            print("\n🧠 Generating embeddings...")
            embedding_stats = research.generate_embeddings()
            stats['embedding_stats'] = embedding_stats
        
        # Generate report
        print("\n📋 Generating collection report...")
        report = research.generate_collection_report(stats)
        
        print("\n✅ Research automation complete!")
        print(f"📊 Collected {stats['total_collected']:,} posts and {stats['total_comments']:,} comments")
        print(f"🎯 Processed {len(SUBREDDITS)} subreddits with {len(SEARCH_KEYWORDS)} keywords each")
        
        if GENERATE_EMBEDDINGS and generate_embeddings and 'embedding_stats' in stats:
            print(f"🧠 Generated {stats['embedding_stats']['new_embeddings']} embeddings")
        
        print("\n🎯 Next Steps:")
        print("  1. Use semantic_search.py to find similar posts")
        print("  2. Analyze collected data for patterns")
        print("  3. Run additional targeted searches if needed")
        print("  4. Export data for further analysis")
        
    except Exception as e:
        print(f"❌ Error during research automation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Reddit API client for fetching posts.
"""

import praw
from datetime import datetime, timedelta
from typing import List, Optional, Generator
from tqdm import tqdm
import requests

from .models import RedditPost, SearchQuery
from .config import config, validate_config

class RedditClient:
    """Reddit API client for fetching posts."""
    
    def __init__(self):
        """Initialize Reddit client."""
        if not validate_config():
            raise ValueError("Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
        
        requestor_kwargs = {}
        if config.http_proxy or config.https_proxy:
            proxies = {
                'http': config.http_proxy,
                'https': config.https_proxy,
            }
            print(f"Using proxies: {proxies}")
            session = requests.Session()
            session.proxies = proxies
            requestor_kwargs['session'] = session

        self.reddit = praw.Reddit(
            client_id=config.reddit.client_id,
            client_secret=config.reddit.client_secret,
            user_agent=config.reddit.user_agent,
            requestor_kwargs=requestor_kwargs
        )
    
    def fetch_posts(self, query: SearchQuery) -> List[RedditPost]:
        """Fetch posts based on search query."""
        subreddit = self.reddit.subreddit(query.subreddit)
        posts = []
        
        print(f"Fetching posts from r/{query.subreddit}...")
        
        # Get posts based on sort type
        if query.sort == 'hot':
            submissions = subreddit.hot(limit=query.limit)
        elif query.sort == 'new':
            submissions = subreddit.new(limit=query.limit)
        elif query.sort == 'top':
            submissions = subreddit.top(time_filter=query.timespan, limit=query.limit)
        elif query.sort == 'rising':
            submissions = subreddit.rising(limit=query.limit)
        else:
            submissions = subreddit.hot(limit=query.limit)
        
        # Convert PRAW submissions to our RedditPost model
        for submission in tqdm(submissions, desc="Processing posts"):
            # Filter by keyword if provided
            if query.keyword and query.keyword.lower() not in submission.title.lower():
                continue
            
            # Filter by timespan if not using 'top' sort
            if query.sort != 'top' and not self._is_within_timespan(submission.created_utc, query.timespan):
                continue
            
            post = self._submission_to_post(submission)
            posts.append(post)
        
        print(f"Fetched {len(posts)} posts from r/{query.subreddit}")
        return posts
    
    def fetch_posts_by_ids(self, post_ids: List[str]) -> List[RedditPost]:
        """Fetch specific posts by their IDs."""
        posts = []
        for post_id in tqdm(post_ids, desc="Fetching posts by ID"):
            try:
                submission = self.reddit.submission(id=post_id)
                post = self._submission_to_post(submission)
                posts.append(post)
            except Exception as e:
                print(f"Error fetching post {post_id}: {e}")
        return posts
    
    def search_posts(self, query: str, subreddit: str, limit: int = 100, sort: str = 'relevance') -> List[RedditPost]:
        """Search for posts in a subreddit."""
        subreddit_obj = self.reddit.subreddit(subreddit)
        posts = []
        
        print(f"Searching for '{query}' in r/{subreddit}...")
        
        search_results = subreddit_obj.search(query, sort=sort, limit=limit)
        
        for submission in tqdm(search_results, desc="Processing search results"):
            post = self._submission_to_post(submission)
            posts.append(post)
        
        print(f"Found {len(posts)} posts matching '{query}'")
        return posts
    
    def _submission_to_post(self, submission) -> RedditPost:
        """Convert PRAW submission to RedditPost."""
        return RedditPost(
            id=submission.id,
            title=submission.title,
            content=submission.selftext if submission.is_self else '',
            author=str(submission.author) if submission.author else '[deleted]',
            subreddit=submission.subreddit.display_name,
            score=submission.score,
            num_comments=submission.num_comments,
            created_utc=datetime.fromtimestamp(submission.created_utc),
            url=submission.url,
            permalink=f"https://reddit.com{submission.permalink}",
            is_self=submission.is_self,
            upvote_ratio=submission.upvote_ratio
        )
    
    def _is_within_timespan(self, created_utc: float, timespan: str) -> bool:
        """Check if post creation time is within the specified timespan."""
        if timespan == 'all':
            return True
        
        now = datetime.now()
        post_time = datetime.fromtimestamp(created_utc)
        
        if timespan == 'day':
            return (now - post_time).days <= 1
        elif timespan == 'week':
            return (now - post_time).days <= 7
        elif timespan == 'month':
            return (now - post_time).days <= 30
        elif timespan == 'year':
            return (now - post_time).days <= 365
        else:
            return True
    
    def get_subreddit_info(self, subreddit_name: str) -> dict:
        """Get information about a subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            return {
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.description,
                'subscribers': subreddit.subscribers,
                'active_users': subreddit.active_user_count,
                'created_utc': datetime.fromtimestamp(subreddit.created_utc)
            }
        except Exception as e:
            print(f"Error getting subreddit info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test Reddit API connection."""
        print("🔍 Debugging Reddit API connection...")
        print(f"  Client ID: {config.reddit.client_id}")
        print(f"  Client Secret: {'*' * (len(config.reddit.client_secret) - 4) + config.reddit.client_secret[-4:] if config.reddit.client_secret else 'Not Set'}")
        print(f"  User Agent: {config.reddit.user_agent}")
        if config.http_proxy or config.https_proxy:
            print(f"  HTTP Proxy: {config.http_proxy or 'Not set'}")
            print(f"  HTTPS Proxy: {config.https_proxy or 'Not set'}")

        proxies = {
            'http': config.http_proxy,
            'https': config.https_proxy
        }

        try:
            print("\n  📡 Testing basic connectivity to Reddit...")
            response = requests.head("https://www.reddit.com", timeout=10, proxies=proxies)
            response.raise_for_status()
            print("  ✅ Basic connectivity to Reddit.com successful")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Cannot reach Reddit.com: {e}")
            return False

        try:
            print("\n  🔑 Testing Reddit API endpoint (praw)...")
            subreddit = self.reddit.subreddit('test')
            subreddit.title
            print("  ✅ Reddit API connection successful!")
            return True
        except Exception as e:
            print(f"  ❌ Reddit API connection failed: {e}")
            return False 
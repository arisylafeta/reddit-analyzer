# Reddit Semantic Search - Usage Guide

This guide will help you fetch Reddit posts from r/lovable and r/vibecoding, generate embeddings, and perform semantic search.

## Prerequisites

1. **Reddit API Credentials**: Get them from https://www.reddit.com/prefs/apps
2. **Ollama**: Install and run Ollama with an embedding model
3. **Python Environment**: Install dependencies from requirements.txt

## Setup

### 1. Configure Environment Variables

Make sure your `.env` file contains:

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID="your_client_id"
REDDIT_CLIENT_SECRET="your_client_secret"
REDDIT_USER_AGENT="YourApp/1.0 by YourUsername"

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL="mxbai-embed-large"

# Database Configuration
DATABASE_PATH=./data/reddit_posts.db
VECTOR_DB_PATH=./data/chroma_db
```

### 2. Start Ollama

```bash
# Start Ollama server
ollama serve

# Pull the embedding model (in another terminal)
ollama pull mxbai-embed-large
```

### 3. Test Setup

```bash
python main.py setup
```

## Quick Start - Fetch and Embed Posts

### Option 1: Use the Automated Script (Recommended)

```bash
# Fetch 1000 posts from both r/lovable and r/vibecoding, store them, and generate embeddings
python fetch_subreddits.py
```

This script will:
- Fetch 1000 posts from r/lovable
- Fetch 1000 posts from r/vibecoding  
- Store all posts in the database
- Generate embeddings for titles and content combined
- Show progress and statistics

### Option 2: Manual Step-by-Step Process

```bash
# 1. Fetch posts from r/lovable
python main.py fetch -s lovable -l 1000 --sort new

# 2. Fetch posts from r/vibecoding
python main.py fetch -s vibecoding -l 1000 --sort new

# 3. Generate embeddings for all posts
python main.py embed

# 4. Check status
python main.py status
```

## Semantic Search

### Using the Dedicated Search Script (Recommended)

```bash
# Basic search
python semantic_search.py "machine learning algorithms"

# Search within a specific subreddit
python semantic_search.py "web development" --subreddit lovable

# Get top 5 results without content preview
python semantic_search.py "coding best practices" --top-k 5 --no-content

# Search for AI-related posts
python semantic_search.py "artificial intelligence and neural networks"
```

### Using the CLI Command

```bash
# Basic search
python main.py search -q "machine learning"

# Search within subreddit
python main.py search -q "web development" -s lovable

# Get top 5 results
python main.py search -q "coding practices" -k 5
```

## Example Searches

Here are some example searches you can try:

```bash
# Technology and Programming
python semantic_search.py "javascript frameworks and libraries"
python semantic_search.py "python data science tools"
python semantic_search.py "web development best practices"
python semantic_search.py "machine learning algorithms"

# Development Tools
python semantic_search.py "code editors and IDEs"
python semantic_search.py "version control and git"
python semantic_search.py "debugging techniques"

# Career and Learning
python semantic_search.py "learning programming as a beginner"
python semantic_search.py "software engineering career advice"
python semantic_search.py "coding interview preparation"

# Specific Technologies
python semantic_search.py "react hooks and state management"
python semantic_search.py "database design patterns"
python semantic_search.py "API development and REST"
```

## Understanding the Results

The search results show:
- **Similarity Score**: How similar the post is to your query (0.0 to 1.0)
- **Subreddit**: Which subreddit the post came from
- **Title**: The post title
- **Score**: Reddit upvotes/downvotes
- **Comments**: Number of comments
- **Author**: Post author
- **Created**: When the post was created
- **URL**: Direct link to the Reddit post
- **Content**: Preview of post content (if available)

## Advanced Usage

### Filtering by Subreddit

```bash
# Only search in r/lovable
python semantic_search.py "your query" --subreddit lovable

# Only search in r/vibecoding
python semantic_search.py "your query" --subreddit vibecoding
```

### Adjusting Number of Results

```bash
# Get top 20 results
python semantic_search.py "your query" --top-k 20

# Get just top 3 results
python semantic_search.py "your query" --top-k 3
```

### Database Management

```bash
# Check database status
python main.py status

# Check status for specific subreddit
python main.py status -s lovable

# Generate embeddings for specific subreddit
python main.py embed -s vibecoding
```

## How It Works

1. **Fetching**: Posts are fetched from Reddit using the PRAW library
2. **Storage**: Posts are stored in a SQLite database with full metadata
3. **Embedding**: Both title and content are combined and embedded using Ollama
4. **Search**: Query text is embedded and compared against all post embeddings using cosine similarity
5. **Ranking**: Results are ranked by similarity score and returned

## Troubleshooting

### Common Issues

1. **"Reddit API connection failed"**
   - Check your Reddit API credentials in `.env`
   - Ensure you have the correct client ID and secret

2. **"Ollama connection failed"**
   - Make sure Ollama is running: `ollama serve`
   - Check if the model is available: `ollama list`
   - Pull the model if needed: `ollama pull mxbai-embed-large`

3. **"No posts with embeddings found"**
   - Run the embedding generation: `python main.py embed`
   - Or use the automated script: `python fetch_subreddits.py`

4. **Slow embedding generation**
   - Embedding generation can take time depending on your hardware
   - The script processes posts in batches to show progress
   - Consider using a smaller, faster model if needed

### Performance Tips

- Use `--no-content` flag in semantic search for faster display
- Limit results with `--top-k` for quicker searches
- Generate embeddings in smaller batches if you have memory issues

## File Structure

```
├── main.py                 # Main CLI interface
├── fetch_subreddits.py     # Automated fetching script
├── semantic_search.py      # Dedicated search script
├── src/
│   ├── reddit_client.py    # Reddit API integration
│   ├── database.py         # Database management
│   ├── embedding_service.py # Ollama embedding service
│   ├── models.py           # Data models
│   └── config.py           # Configuration management
└── data/
    ├── reddit_posts.db     # SQLite database
    └── chroma_db/          # Vector database (future use)
```

## Next Steps

After setting up and running your first searches, you can:

1. Experiment with different search queries
2. Analyze which types of posts are most similar
3. Use the results to discover interesting content
4. Extend the system with additional subreddits
5. Implement more advanced filtering and ranking
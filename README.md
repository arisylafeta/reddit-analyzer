# Reddit Topic Modeling System

A comprehensive system for fetching Reddit posts, generating embeddings using Ollama, and performing topic analysis and clustering.

## Features

- **Reddit API Integration**: Fetch posts from any subreddit with flexible filtering
- **Local Embeddings**: Generate embeddings using Ollama (no external API required)
- **Data Storage**: SQLite database for posts and embeddings
- **Topic Analysis**: Clustering and similarity search capabilities
- **CLI Interface**: Easy-to-use command-line interface
- **Flexible Filtering**: By subreddit, timespan, keywords, and more

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Reddit API    │───▶│   Data Fetcher   │───▶│  SQLite Database│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Clustering &    │◀───│ Ollama Embedding │◀───│   Posts without │
│ Topic Analysis  │    │    Service       │    │   Embeddings    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Prerequisites

1. **Python 3.8+**
2. **Reddit API Credentials** - Get them from [Reddit Apps](https://www.reddit.com/prefs/apps)
3. **Ollama** - Install from [ollama.ai](https://ollama.ai)

## Installation

1. **Clone and setup the environment:**
   ```bash
   git clone [your-repo-url]
   cd Reddit
   pip install -r requirements.txt
   ```

2. **Configure Reddit API credentials:**
   ```bash
   cp config.env.example .env
   # Edit .env and add your Reddit API credentials
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   ```

4. **Setup the system:**
   ```bash
   python main.py setup
   ```

## Usage

### Basic Workflow

1. **Fetch Reddit posts:**
   ```bash
   # Fetch hot posts from r/MachineLearning
   python main.py fetch -s MachineLearning -t week -l 50
   
   # Fetch posts with keyword filter
   python main.py fetch -s programming -k "python" -t month -l 100
   ```

2. **Generate embeddings:**
   ```bash
   # Generate embeddings for all posts without embeddings
   python main.py embed
   
   # Generate embeddings for specific subreddit
   python main.py embed -s MachineLearning
   ```

3. **Check system status:**
   ```bash
   # Overall status
   python main.py status
   
   # Status for specific subreddit
   python main.py status -s MachineLearning
   ```

### Command Reference

#### Setup Command
```bash
python main.py setup
```
Tests all connections and initializes the database.

#### Fetch Command
```bash
python main.py fetch [OPTIONS]
```

Options:
- `-s, --subreddit TEXT` (required): Subreddit to fetch from
- `-t, --timespan [day|week|month|year|all]`: Time period (default: week)
- `-k, --keyword TEXT`: Optional keyword filter
- `-l, --limit INTEGER`: Number of posts to fetch (default: 100)
- `--sort [hot|new|top|rising]`: Sort method (default: hot)

#### Embed Command
```bash
python main.py embed [OPTIONS]
```

Options:
- `-s, --subreddit TEXT`: Filter by subreddit (optional)
- `-b, --batch-size INTEGER`: Batch size for processing (default: 10)

#### Status Command
```bash
python main.py status [OPTIONS]
```

Options:
- `-s, --subreddit TEXT`: Filter by subreddit (optional)

## Configuration

Edit your `.env` file with the following variables:

```env
# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=your_app_name/1.0 by your_username

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Database Configuration
DATABASE_PATH=./data/reddit_posts.db
VECTOR_DB_PATH=./data/chroma_db
```

### Getting Reddit API Credentials

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the required fields
5. Use the client ID (under the app name) and client secret

## Examples

### Example 1: Analyze Machine Learning Discussions
```bash
# Fetch recent ML posts
python main.py fetch -s MachineLearning -t week -l 200

# Generate embeddings
python main.py embed -s MachineLearning

# Check status
python main.py status -s MachineLearning
```

### Example 2: Research Specific Topics
```bash
# Fetch posts about "transformers" in AI subreddit
python main.py fetch -s artificial -k "transformers" -t month -l 50

# Generate embeddings
python main.py embed -s artificial
```

### Example 3: Monitor Multiple Subreddits
```bash
# Fetch from multiple subreddits
python main.py fetch -s programming -t day -l 100
python main.py fetch -s Python -t day -l 100
python main.py fetch -s MachineLearning -t day -l 100

# Generate embeddings for all
python main.py embed
```

## File Structure

```
Reddit/
├── main.py                 # CLI interface
├── requirements.txt        # Python dependencies
├── config.env.example     # Configuration template
├── README.md              # This file
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── database.py        # Database operations
│   ├── reddit_client.py   # Reddit API client
│   └── embedding_service.py # Ollama embedding service
└── data/                  # Created automatically
    ├── reddit_posts.db    # SQLite database
    └── chroma_db/         # Vector database (future)
```

## Development Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Reddit API integration
- [x] SQLite database storage
- [x] Ollama embedding service
- [x] CLI interface
- [x] Configuration management

### Phase 2: Advanced Features (Next)
- [ ] Vector database integration (ChromaDB)
- [ ] Clustering algorithms (K-means, DBSCAN)
- [ ] Similarity search
- [ ] Topic visualization
- [ ] Web interface (Streamlit)

### Phase 3: Analytics & Insights
- [ ] Topic trend analysis
- [ ] Post performance correlation
- [ ] Automated topic summarization
- [ ] Export capabilities (CSV, JSON)

## Troubleshooting

### Common Issues

1. **Reddit API Connection Failed**
   - Check your credentials in `.env`
   - Ensure your Reddit app is configured as "script" type
   - Verify user agent format

2. **Ollama Connection Failed**
   - Make sure Ollama is running: `ollama serve`
   - Check if the model is available: `ollama list`
   - Try pulling the model: `ollama pull llama2`

3. **Database Errors**
   - Ensure the `data/` directory has write permissions
   - Check if SQLite is properly installed

### Getting Help

1. Run `python main.py setup` to diagnose connection issues
2. Check the console output for detailed error messages
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

## Contributing

This is a research/personal project. Feel free to extend and modify as needed.

## License

MIT License - feel free to use and modify. 
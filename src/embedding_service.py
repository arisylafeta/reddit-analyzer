"""
Embedding service using Ollama for generating text embeddings.
"""

import ollama
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from tqdm import tqdm

from .models import RedditPost, PostEmbedding
from .config import config

class EmbeddingService:
    """Service for generating embeddings using Ollama."""
    
    def __init__(self, model_name: str = None):
        """Initialize embedding service."""
        self.model_name = model_name or config.ollama.model
        self.base_url = config.ollama.base_url
        self.client = ollama.Client(host=self.base_url)
    
    def test_connection(self) -> bool:
        """Test connection to Ollama server."""
        try:
            models = self.client.list()
            model_names = [m.model for m in models.models]
            print(f"Ollama connection successful! Available models: {model_names}")
            return True
        except Exception as e:
            print(f"Ollama connection failed: {e}")
            print("Make sure Ollama is running: `ollama serve`")
            return False
    
    def ensure_model_available(self) -> bool:
        """Ensure the specified model is available, pull if necessary."""
        try:
            models = self.client.list()
            available_models = [m.model for m in models.models]
            
            # Check if model exists (with or without :latest suffix)
            model_exists = False
            for available_model in available_models:
                if (available_model == self.model_name or 
                    available_model == f"{self.model_name}:latest" or
                    available_model.startswith(f"{self.model_name}:")):
                    model_exists = True
                    # Update model name to match exactly what's available
                    self.model_name = available_model
                    break
            
            if not model_exists:
                print(f"Model {self.model_name} not found. Pulling from Ollama...")
                self.client.pull(self.model_name)
                print(f"Successfully pulled {self.model_name}")
            
            return True
        except Exception as e:
            print(f"Error ensuring model availability: {e}")
            return False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response.embedding
        except Exception as e:
            print(f"Error generating embedding for text: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = []
        
        print(f"Generating embeddings for {len(texts)} texts using {self.model_name}...")
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Processing batches"):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                embedding = self.generate_embedding(text)
                batch_embeddings.append(embedding)
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def embed_posts(self, posts: List[RedditPost]) -> List[PostEmbedding]:
        """Generate embeddings for Reddit post titles and content combined."""
        if not posts:
            return []
        
        # Combine title and content for better semantic representation
        combined_texts = []
        for post in posts:
            # Combine title and content, with title getting more weight
            combined_text = f"Title: {post.title}"
            if post.content and post.content.strip():
                combined_text += f"\n\nContent: {post.content}"
            combined_texts.append(combined_text)
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(combined_texts)
        
        # Create PostEmbedding objects
        post_embeddings = []
        for post, embedding in zip(posts, embeddings):
            if embedding is not None:
                post_embedding = PostEmbedding(
                    post_id=post.id,
                    embedding=embedding,
                    model_name=self.model_name,
                    created_at=datetime.now()
                )
                post_embeddings.append(post_embedding)
            else:
                print(f"Failed to generate embedding for post: {post.id}")
        
        print(f"Successfully generated {len(post_embeddings)} embeddings out of {len(posts)} posts")
        return post_embeddings
    
    def embed_single_post(self, post: RedditPost) -> Optional[PostEmbedding]:
        """Generate embedding for a single Reddit post."""
        # Combine title and content for better semantic representation
        combined_text = f"Title: {post.title}"
        if post.content and post.content.strip():
            combined_text += f"\n\nContent: {post.content}"
        
        embedding = self.generate_embedding(combined_text)
        
        if embedding:
            return PostEmbedding(
                post_id=post.id,
                embedding=embedding,
                model_name=self.model_name,
                created_at=datetime.now()
            )
        
        return None
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            
            if norm_product == 0:
                return 0.0
            
            return dot_product / norm_product
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0
    
    def find_similar_posts(self, query_embedding: List[float], post_embeddings: List[PostEmbedding], 
                          top_k: int = 10) -> List[tuple]:
        """Find most similar posts to a query embedding."""
        similarities = []
        
        for post_embedding in post_embeddings:
            similarity = self.compute_similarity(query_embedding, post_embedding.embedding)
            similarities.append((post_embedding.post_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_embedding_stats(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """Get statistics about a set of embeddings."""
        if not embeddings:
            return {}
        
        # Convert to numpy array
        embedding_matrix = np.array(embeddings)
        
        return {
            'count': len(embeddings),
            'dimension': len(embeddings[0]) if embeddings else 0,
            'mean_norm': np.mean(np.linalg.norm(embedding_matrix, axis=1)),
            'std_norm': np.std(np.linalg.norm(embedding_matrix, axis=1)),
            'min_value': np.min(embedding_matrix),
            'max_value': np.max(embedding_matrix),
            'mean_value': np.mean(embedding_matrix),
            'std_value': np.std(embedding_matrix)
        } 
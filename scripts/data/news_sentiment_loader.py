#!/usr/bin/env python3
"""
Financial News Sentiment Loader (Task #098)
Protocol: v4.3 (Hub-Native Edition)

Ingests financial news from EODHD API, performs sentiment analysis using FinBERT,
generates embeddings using Sentence-Transformers, and stores in ChromaDB.
"""

import os
import sys
import json
import logging
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import torch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from scripts.data.vector_client import VectorClient
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NewsSentimentLoader:
    """Loads financial news and performs sentiment analysis."""

    def __init__(self, device: str = "cpu"):
        """Initialize models and clients."""
        self.device = device
        logger.info(f"📦 Initializing models on device: {self.device}")

        # Load models
        device_idx = 0 if device == "cuda" else -1
        self.sentiment_model = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            device=device_idx
        )

        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device=self.device
        )

        # Initialize vector client
        self.vector_client = VectorClient()
        logger.info("✅ Models and vector client initialized")

    def fetch_news(
        self,
        symbol: str,
        days: int = 7
    ) -> List[Dict]:
        """Fetch news from EODHD API."""
        api_token = os.getenv("EODHD_API_TOKEN")
        if not api_token:
            logger.error("❌ EODHD_API_TOKEN not configured")
            return []

        # Calculate date range
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        url = (
            f"https://eodhd.com/api/news?"
            f"s={symbol}&"
            f"from={from_date}&"
            f"to={to_date}&"
            f"api_token={api_token}&"
            f"fmt=json"
        )

        try:
            logger.info(
                f"📰 Fetching news for {symbol} from {from_date} to {to_date}"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            news_items = response.json()
            if isinstance(news_items, list):
                logger.info(f"✅ Fetched {len(news_items)} news items")
                return news_items
            else:
                logger.warning(f"⚠️  Unexpected API response format")
                return []

        except requests.RequestException as e:
            logger.error(f"❌ Failed to fetch news: {e}")
            return []

    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text using FinBERT."""
        try:
            result = self.sentiment_model(text[:512])  # Limit to 512 chars
            return {
                "label": result[0]["label"],
                "score": result[0]["score"]
            }
        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {e}")
            return {"label": "NEUTRAL", "score": 0.5}

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return []

    def process_news_batch(
        self,
        news_items: List[Dict],
        collection_name: str = "financial_news",
        batch_size: int = 1
    ) -> int:
        """Process news items and store in ChromaDB."""
        if not news_items:
            logger.warning("⚠️  No news items to process")
            return 0

        # Ensure collection exists
        collection = self.vector_client.ensure_collection(collection_name)
        logger.info(f"📚 Processing {len(news_items)} news items...")

        vectors = []
        metadatas = []
        documents = []
        processed_count = 0

        for i, news in enumerate(news_items):
            try:
                # Extract news content
                title = news.get("title", "")
                link = news.get("link", "")
                published = news.get("date", "")

                if not title:
                    continue

                # Analyze sentiment
                sentiment = self.analyze_sentiment(title)

                # Generate embedding
                embedding = self.generate_embedding(title)
                if not embedding:
                    continue

                vectors.append(embedding)
                metadatas.append({
                    "sentiment_label": sentiment["label"],
                    "sentiment_score": sentiment["score"],
                    "published": published,
                    "link": link
                })
                documents.append(title)

                logger.info(
                    f"[SENTIMENT] Title: {title[:50]}... | "
                    f"Score: {sentiment['score']:.2f} "
                    f"({sentiment['label']})"
                )

                processed_count += 1

                # Batch insert
                if len(vectors) >= batch_size:
                    self.vector_client.insert_vectors(
                        collection_name=collection_name,
                        vectors=vectors,
                        metadatas=metadatas,
                        documents=documents
                    )
                    vectors = []
                    metadatas = []
                    documents = []

            except Exception as e:
                logger.error(f"❌ Error processing news item: {e}")
                continue

        # Insert remaining items
        if vectors:
            self.vector_client.insert_vectors(
                collection_name=collection_name,
                vectors=vectors,
                metadatas=metadatas,
                documents=documents
            )

        logger.info(f"✅ Processed {processed_count} news items")
        return processed_count

    def query_similar_news(
        self,
        query: str,
        collection_name: str = "financial_news",
        n_results: int = 3
    ) -> List[Dict]:
        """Query similar news by semantic similarity."""
        try:
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []

            results = self.vector_client.query_vectors(
                collection_name=collection_name,
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # Format results
            formatted_results = []
            if results and results.get("documents"):
                for i, (doc_id, distance, document) in enumerate(
                    zip(
                        results["ids"][0],
                        results["distances"][0],
                        results["documents"][0]
                    )
                ):
                    metadata = results["metadatas"][0][i]
                    formatted_results.append({
                        "document": document,
                        "distance": distance,
                        "sentiment_score": metadata.get("sentiment_score", 0),
                        "sentiment_label": metadata.get(
                            "sentiment_label",
                            "UNKNOWN"
                        )
                    })

            logger.info(
                f"🔍 Found {len(formatted_results)} similar news items "
                f"for query: '{query}'"
            )
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Financial News Sentiment Loader"
    )
    parser.add_argument(
        "--symbol",
        default="AAPL",
        help="Stock symbol (default: AAPL)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to fetch (default: 7)"
    )
    parser.add_argument(
        "--task-id",
        default="098",
        help="Task ID for tracking"
    )
    parser.add_argument(
        "--collection",
        default="financial_news",
        help="ChromaDB collection name"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Set device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"🔧 Using device: {device}")

    # Initialize loader
    loader = NewsSentimentLoader(device=device)

    # Fetch and process news
    news_items = loader.fetch_news(args.symbol, args.days)
    if news_items:
        processed = loader.process_news_batch(
            news_items,
            collection_name=args.collection,
            batch_size=1
        )

        # Query example
        logger.info("\n" + "="*70)
        logger.info("🔍 Testing semantic search...")
        similar = loader.query_similar_news(
            f"{args.symbol} earnings",
            collection_name=args.collection,
            n_results=3
        )

        if similar:
            logger.info(f"📊 Found {len(similar)} similar news items:")
            for result in similar:
                logger.info(
                    f"  • {result['document'][:60]}... "
                    f"(sentiment: {result['sentiment_score']:.2f})"
                )

        logger.info("="*70)

        logger.info(f"✅ Task #{args.task_id} completed successfully")
        return 0
    else:
        logger.error("❌ Failed to fetch news items")
        return 1


if __name__ == "__main__":
    sys.exit(main())

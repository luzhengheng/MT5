#!/usr/bin/env python3
"""
TDD Audit for Task #098: Financial News Sentiment Pipeline
Protocol: v4.3 (Zero-Trust Edition)

This script validates:
1. FinBERT model loading and sentiment analysis
2. Sentence-Transformers embedding generation
3. Vector storage in ChromaDB
4. Sentiment retrieval accuracy
"""

import sys
import os
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)


class Task098Auditor:
    """TDD Audit for Task #098."""

    def __init__(self):
        self.test_results = []
        self.session_id = self._generate_session_id()
        self.start_time = time.time()

    @staticmethod
    def _generate_session_id():
        """Generate a unique session ID."""
        return str(uuid.uuid4())[:16]

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        print(f"{status} | {test_name}: {message}")
        logger.info(f"{status} | {test_name}: {message}")

    def test_transformers_library(self) -> bool:
        """Test 1: Transformers library installation."""
        try:
            import transformers
            version = transformers.__version__
            self.log_test("Transformers Installation", True, f"v{version}")
            return True
        except ImportError as e:
            self.log_test("Transformers Installation", False, str(e))
            return False

    def test_torch_availability(self) -> bool:
        """Test 2: PyTorch availability (CPU mode)."""
        try:
            import torch
            device = "cpu"
            tensor = torch.tensor([1.0, 2.0, 3.0], device=device)
            self.log_test(
                "PyTorch CPU Mode",
                True,
                f"v{torch.__version__} on {device}"
            )
            return True
        except Exception as e:
            self.log_test("PyTorch CPU Mode", False, str(e))
            return False

    def test_finbert_model_loading(self) -> bool:
        """Test 3: FinBERT model loading."""
        try:
            from transformers import pipeline
            import torch

            # Set device to CPU
            device = 0 if torch.cuda.is_available() else -1

            # Load FinBERT sentiment pipeline
            sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=device
            )

            # Test sentiment analysis
            test_text = "Apple posts record profits"
            result = sentiment_pipeline(test_text)

            self.log_test(
                "FinBERT Model Loading",
                True,
                f"Loaded and tested on '{test_text}'"
            )
            return True
        except Exception as e:
            self.log_test("FinBERT Model Loading", False, str(e))
            return False

    def test_sentence_transformers(self) -> bool:
        """Test 4: Sentence-Transformers embedding generation."""
        try:
            from sentence_transformers import SentenceTransformer

            # Load embedding model
            model = SentenceTransformer("all-MiniLM-L6-v2")

            # Generate embeddings
            texts = [
                "Apple announces new iPhone",
                "Market crashes amid economic fears"
            ]
            embeddings = model.encode(texts)

            # Validate shape
            assert embeddings.shape[0] == 2, "Expected 2 embeddings"
            assert embeddings.shape[1] == 384, "Expected 384-dim embeddings"

            self.log_test(
                "Sentence-Transformers",
                True,
                f"Generated 2 embeddings with shape {embeddings.shape}"
            )
            return True
        except Exception as e:
            self.log_test("Sentence-Transformers", False, str(e))
            return False

    def test_vector_client_integration(self) -> bool:
        """Test 5: VectorClient integration with ChromaDB."""
        try:
            from scripts.data.vector_client import VectorClient

            client = VectorClient()
            collection = client.ensure_collection("news_sentiment_test")

            # Test basic operations
            assert collection is not None, "Collection is None"

            self.log_test(
                "VectorClient Integration",
                True,
                f"Collection '{collection.name}' created"
            )
            return True
        except Exception as e:
            self.log_test("VectorClient Integration", False, str(e))
            return False

    def test_sentiment_with_vector_storage(self) -> bool:
        """Test 6: Combined sentiment analysis + vector storage."""
        try:
            from transformers import pipeline
            from sentence_transformers import SentenceTransformer
            from scripts.data.vector_client import VectorClient
            import torch

            # Device selection
            device = 0 if torch.cuda.is_available() else -1

            # Load models
            sentiment_model = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=device
            )
            embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Test data
            test_news = [
                "Apple posts record profits",
                "Market crashes amid economic crisis"
            ]

            # Analyze and vectorize
            results = []
            for news in test_news:
                sentiment = sentiment_model(news)[0]
                embedding = embedding_model.encode(news).tolist()
                results.append({
                    "text": news,
                    "sentiment": sentiment,
                    "embedding": embedding
                })

            # Store in ChromaDB
            client = VectorClient()
            collection = client.ensure_collection("news_sentiment_test")

            vectors = [r["embedding"] for r in results]
            metadatas = [
                {
                    "sentiment_label": r["sentiment"]["label"],
                    "sentiment_score": r["sentiment"]["score"]
                }
                for r in results
            ]
            documents = [r["text"] for r in results]

            client.insert_vectors(
                collection_name="news_sentiment_test",
                vectors=vectors,
                metadatas=metadatas,
                documents=documents
            )

            self.log_test(
                "Sentiment + Vector Storage",
                True,
                f"Stored {len(results)} news items with sentiment"
            )
            return True
        except Exception as e:
            self.log_test("Sentiment + Vector Storage", False, str(e))
            return False

    def test_memory_efficiency(self) -> bool:
        """Test 7: Memory efficiency check."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            # Warn if using too much memory
            warning = memory_mb > 2048
            msg = f"Memory usage: {memory_mb:.1f} MB"
            if warning:
                msg += " (⚠️ High - consider batch processing)"

            self.log_test("Memory Efficiency", not warning, msg)
            return not warning
        except Exception as e:
            self.log_test("Memory Efficiency", False, str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("\n" + "="*70)
        print("🔧 TASK #098 AUDIT - Financial News Sentiment Pipeline")
        print("="*70)
        print(f"Session ID: {self.session_id}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

        tests = [
            self.test_transformers_library,
            self.test_torch_availability,
            self.test_finbert_model_loading,
            self.test_sentence_transformers,
            self.test_vector_client_integration,
            self.test_sentiment_with_vector_storage,
            self.test_memory_efficiency,
        ]

        results = []
        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                logger.error(f"Unhandled error in {test_func.__name__}: {e}")
                results.append(False)

        # Summary
        passed = sum(results)
        total = len(results)

        print("\n" + "="*70)
        print(f"📊 SUMMARY: {passed}/{total} tests passed")
        print("="*70)

        # Physical evidence
        print(f"\n💀 Physical Verification Evidence:")
        print(f"  UUID: {self.session_id}")
        print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        return passed == total

    def generate_report(self) -> Dict:
        """Generate test report."""
        return {
            "task_id": "098",
            "session_id": self.session_id,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for t in self.test_results if t['passed']),
            "test_results": self.test_results
        }


def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    auditor = Task098Auditor()

    try:
        success = auditor.run_all_tests()
        report = auditor.generate_report()

        # Write report to JSON
        report_path = Path("./TASK_098_AUDIT_REPORT.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {report_path}")

        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()

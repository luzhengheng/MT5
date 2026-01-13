#!/usr/bin/env python3
"""
Vector Database Client for ChromaDB
Task #097: 向量数据库基础设施构建

This module provides a singleton pattern wrapper around ChromaDB
for managing high-dimensional vector storage and retrieval.
"""

import chromadb
from chromadb.config import Settings
import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VectorClient:
    """Singleton pattern wrapper for ChromaDB client."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_dir: str = "./data/chroma", use_persistent: bool = True):
        """
        Initialize ChromaDB client.

        Args:
            persist_dir: Directory for persistent storage (if use_persistent=True)
            use_persistent: Whether to use persistent storage (requires SQLite >= 3.35)
        """
        if self._initialized:
            return

        self.persist_dir = Path(persist_dir)
        self.use_persistent = use_persistent

        # Initialize ChromaDB
        try:
            if use_persistent:
                # Try persistent mode (requires SQLite >= 3.35)
                self.persist_dir.mkdir(parents=True, exist_ok=True)
                settings = Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(self.persist_dir),
                    anonymized_telemetry=False,
                )
                self._client = chromadb.Client(settings)
                logger.info(
                    f"✅ ChromaDB client initialized "
                    f"with persist_dir: {self.persist_dir}"
                )
            else:
                # Use ephemeral/memory mode for older SQLite versions
                self._client = chromadb.EphemeralClient()
                logger.info("✅ ChromaDB client initialized in ephemeral mode")
        except Exception as e:
            logger.warning(
                f"⚠️ Persistent mode failed ({e}), "
                f"falling back to ephemeral"
            )
            try:
                self._client = chromadb.EphemeralClient()
                self.use_persistent = False
                logger.info(
                    "✅ ChromaDB client initialized "
                    "in ephemeral mode (fallback)"
                )
            except Exception as e2:
                logger.error(f"❌ Failed to initialize ChromaDB: {e2}")
                raise

        self._initialized = True

    @staticmethod
    def get_client():
        """Get the singleton ChromaDB client instance."""
        return VectorClient()._client

    def ensure_collection(
        self, name: str, metadata: Optional[Dict] = None
    ) -> object:
        """
        Ensure a collection exists, create if not.

        Args:
            name: Collection name
            metadata: Optional metadata dict

        Returns:
            ChromaDB collection object
        """
        try:
            collection = self._client.get_or_create_collection(
                name=name,
                metadata=metadata or {"task": "097"}
            )
            logger.info(
                f"✅ Collection '{name}' ensured "
                f"(count: {collection.count()})"
            )
            return collection
        except Exception as e:
            logger.error(f"❌ Failed to ensure collection '{name}': {e}")
            raise

    def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadatas: List[Dict],
        documents: List[str],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Insert vectors into a collection.

        Args:
            collection_name: Target collection name
            vectors: List of vector embeddings (each is a list of floats)
            metadatas: List of metadata dicts (one per vector)
            documents: List of document strings (one per vector)
            ids: Optional list of document IDs (auto-generated if None)
        """
        collection = self.ensure_collection(collection_name)

        if ids is None:
            # Auto-generate IDs from documents
            ids = [
                hashlib.md5(doc.encode()).hexdigest()[:16]
                for doc in documents
            ]

        try:
            collection.add(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(
                f"✅ Inserted {len(vectors)} vectors "
                f"into '{collection_name}'"
            )
            msg = (
                f"[SUCCESS] Vector Inserted: {len(vectors)} "
                f"records into {collection_name}"
            )
            print(msg)
        except Exception as e:
            logger.error(f"❌ Failed to insert vectors: {e}")
            raise

    def query_vectors(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query vectors by similarity.

        Args:
            collection_name: Collection to query
            query_embeddings: List of query vectors
            n_results: Number of results to return per query
            where: Optional metadata filter

        Returns:
            Query results dict with ids, distances, and documents
        """
        collection = self.ensure_collection(collection_name)

        try:
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            logger.info(
                f"✅ Query completed: {len(results['ids'])} result "
                f"groups"
            )
            return results
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            raise

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            self._client.delete_collection(name=name)
            logger.info(f"✅ Collection '{name}' deleted")
        except Exception as e:
            logger.error(f"❌ Failed to delete collection: {e}")

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self._client.list_collections()
            names = [c.name for c in collections]
            logger.info(f"✅ Found {len(names)} collections: {names}")
            return names
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return []


def test_write_vectors(task_id: str = "097"):
    """Test writing vectors to ChromaDB."""
    print(f"\n🔧 Testing Vector Write (Task #{task_id})...")

    client = VectorClient()
    collection_name = f"test_collection_{task_id}"

    # Create test vectors (384-dim with 1.0 values)
    test_vectors = [
        [0.1 * i for i in range(384)] for _ in range(10)
    ]

    test_metadatas = [
        {"source": "test", "index": i} for i in range(10)
    ]

    test_documents = [
        f"Test document {i}" for i in range(10)
    ]

    # Insert vectors
    client.insert_vectors(
        collection_name=collection_name,
        vectors=test_vectors,
        metadatas=test_metadatas,
        documents=test_documents
    )

    # Query vectors
    query_vector = [[0.1 * i for i in range(384)]]
    results = client.query_vectors(
        collection_name=collection_name,
        query_embeddings=query_vector,
        n_results=3
    )

    # Calculate distances
    if results['distances'] and len(results['distances'][0]) > 0:
        min_distance = min(results['distances'][0])
        success = min_distance < 0.1
        print(
            f"[SUCCESS] Vector query returned distance < 0.1: "
            f"{success}"
        )
        print(f"  Min distance: {min_distance:.6f}")
        print(f"  Matched document: {results['documents'][0][0]}")
        return True
    else:
        print("[FAIL] No results returned from query")
        return False


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - "
               "%(message)s"
    )

    parser = argparse.ArgumentParser(description="Vector Database Client")
    parser.add_argument(
        "--test-write", action="store_true", help="Run write test"
    )
    parser.add_argument("--task-id", default="097", help="Task ID")
    parser.add_argument(
        "--list-collections", action="store_true",
        help="List all collections"
    )

    args = parser.parse_args()

    if args.test_write:
        test_write_vectors(task_id=args.task_id)
    elif args.list_collections:
        client = VectorClient()
        collections = client.list_collections()
        print(json.dumps(collections, indent=2))
    else:
        # Default: show info
        client = VectorClient()
        print("✅ Vector Client initialized")
        print(f"   Persist dir: {client.persist_dir}")
        print(f"   Collections: {client.list_collections()}")

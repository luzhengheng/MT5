#!/usr/bin/env python3
"""
TDD Audit for Task #097: Vector Database Infrastructure
Protocol: v4.3 (Zero-Trust Edition)

This script validates:
1. ChromaDB connectivity and health
2. Collection creation and management
3. Vector write operations
4. KNN search accuracy
5. Data persistence
"""

import sys
import os
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our vector client
from scripts.data.vector_client import VectorClient

logger = logging.getLogger(__name__)


class Task097Auditor:
    """TDD Audit for Task #097."""

    def __init__(self):
        self.test_results = []
        self.session_id = self._generate_session_id()
        self.start_time = time.time()

    @staticmethod
    def _generate_session_id():
        """Generate a unique session ID."""
        import uuid
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

    def test_chromadb_installation(self) -> bool:
        """Test 1: ChromaDB package installed."""
        try:
            import chromadb
            version = chromadb.__version__
            self.log_test("ChromaDB Installation", True, f"v{version}")
            return True
        except ImportError as e:
            self.log_test("ChromaDB Installation", False, f"Import failed: {e}")
            return False

    def test_client_initialization(self) -> bool:
        """Test 2: VectorClient singleton initialization."""
        try:
            client = VectorClient()
            assert client._client is not None, "Client is None"
            self.log_test("VectorClient Initialization", True, "Singleton created")
            self.client = client
            return True
        except Exception as e:
            self.log_test("VectorClient Initialization", False, str(e))
            return False

    def test_collection_creation(self) -> bool:
        """Test 3: Collection creation and retrieval."""
        try:
            collection = self.client.ensure_collection(
                "test_audit_097",
                metadata={"task": "097", "phase": "test"}
            )
            assert collection is not None, "Collection is None"
            assert collection.name == "test_audit_097", f"Name mismatch: {collection.name}"
            self.log_test("Collection Creation", True, f"Collection '{collection.name}' created")
            self.collection = collection
            return True
        except Exception as e:
            self.log_test("Collection Creation", False, str(e))
            return False

    def test_vector_write(self) -> bool:
        """Test 4: Vector write operations."""
        try:
            # Create test vectors (384-dimensional)
            vectors = [
                [0.1 * j for j in range(384)] for _ in range(5)
            ]
            metadatas = [
                {"index": i, "source": "test_audit"} for i in range(5)
            ]
            documents = [
                f"Test document {i} for audit" for i in range(5)
            ]

            self.client.insert_vectors(
                collection_name="test_audit_097",
                vectors=vectors,
                metadatas=metadatas,
                documents=documents
            )

            # Verify count
            count = self.collection.count()
            assert count >= 5, f"Expected at least 5 vectors, got {count}"
            self.log_test("Vector Write", True, f"{count} vectors inserted")
            return True
        except Exception as e:
            self.log_test("Vector Write", False, str(e))
            return False

    def test_knn_search(self) -> bool:
        """Test 5: KNN search accuracy."""
        try:
            # Query with the first test vector
            query_vector = [[0.1 * j for j in range(384)]]

            results = self.client.query_vectors(
                collection_name="test_audit_097",
                query_embeddings=query_vector,
                n_results=3
            )

            # Validate results structure
            assert 'ids' in results, "Missing 'ids' in results"
            assert 'distances' in results, "Missing 'distances' in results"
            assert 'documents' in results, "Missing 'documents' in results"

            # Check distance threshold
            distances = results['distances'][0]
            min_distance = min(distances) if distances else float('inf')

            passed = min_distance < 0.1
            self.log_test(
                "KNN Search",
                passed,
                f"Min distance: {min_distance:.6f} (threshold: 0.1)"
            )
            return passed
        except Exception as e:
            self.log_test("KNN Search", False, str(e))
            return False

    def test_persistence(self) -> bool:
        """Test 6: Data persistence check."""
        try:
            persist_dir = Path("./data/chroma")
            assert persist_dir.exists(), f"Persist dir not found: {persist_dir}"

            # List files
            files = list(persist_dir.glob("**/*"))
            assert len(files) > 0, "No files in persist directory"

            self.log_test(
                "Data Persistence",
                True,
                f"{len(files)} files in {persist_dir}"
            )
            return True
        except Exception as e:
            self.log_test("Data Persistence", False, str(e))
            return False

    def test_list_collections(self) -> bool:
        """Test 7: List all collections."""
        try:
            collections = self.client.list_collections()
            assert "test_audit_097" in collections, "test_audit_097 not found"
            self.log_test(
                "List Collections",
                True,
                f"Found {len(collections)} collections"
            )
            return True
        except Exception as e:
            self.log_test("List Collections", False, str(e))
            return False

    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("\n" + "="*70)
        print("🔧 TASK #097 AUDIT - Vector Database Infrastructure")
        print("="*70)
        print(f"Session ID: {self.session_id}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

        tests = [
            self.test_chromadb_installation,
            self.test_client_initialization,
            self.test_collection_creation,
            self.test_vector_write,
            self.test_knn_search,
            self.test_persistence,
            self.test_list_collections,
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

        # Output physical evidence for forensic verification
        print(f"\n💀 Physical Verification Evidence:")
        print(f"  UUID: {self.session_id}")
        print(f"  Token Usage: N/A (local execution)")
        print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        return passed == total

    def generate_report(self) -> Dict:
        """Generate test report."""
        return {
            "task_id": "097",
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

    auditor = Task097Auditor()

    try:
        success = auditor.run_all_tests()
        report = auditor.generate_report()

        # Write report to JSON
        report_path = Path("./TASK_097_AUDIT_REPORT.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {report_path}")

        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()

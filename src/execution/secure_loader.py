#!/usr/bin/env python3
"""
Secure Module Loader - File Integrity & Path Validation

Provides secure loading of Python modules with file integrity verification.
Prevents path traversal attacks and supply chain compromises.

Protocol v4.3 (Zero-Trust Edition)
"""

import hashlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger('SecureLoader')


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class SecureModuleLoader:
    """
    Secure module loader with file integrity verification

    Features:
      - Path traversal prevention
      - SHA256 integrity verification
      - Allowlist-based loading
      - Detailed security logging
    """

    # Cached hashes to avoid re-computing on every load
    _hash_cache = {}

    def __init__(self, allowed_base_dir: Optional[Path] = None):
        """
        Initialize secure loader

        Args:
            allowed_base_dir: Base directory for allowed modules (defaults to parent of this file)
        """
        if allowed_base_dir is None:
            allowed_base_dir = Path(__file__).parent.parent

        self.allowed_base_dir = allowed_base_dir.resolve()
        logger.debug(f"Secure loader initialized with base: {self.allowed_base_dir}")

    @staticmethod
    def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
        """
        Compute file hash for integrity verification

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (default: sha256)

        Returns:
            Hex digest as string "algorithm:hexdigest"
        """
        hasher = hashlib.new(algorithm)

        # Read file in chunks to handle large files
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        return f"{algorithm}:{hasher.hexdigest()}"

    def _validate_path(self, module_path: Path) -> None:
        """
        Validate module path for security

        Checks:
          1. File exists
          2. Path is within allowed directory
          3. Path doesn't traverse outside allowed directory

        Raises:
            SecurityError: If validation fails
        """
        # Ensure file exists
        if not module_path.exists():
            raise SecurityError(f"Module not found: {module_path}")

        # Resolve to absolute path
        absolute_path = module_path.resolve()

        # Check if path is within allowed directory
        try:
            # Python 3.9+: Use is_relative_to
            if hasattr(absolute_path, 'is_relative_to'):
                if not absolute_path.is_relative_to(self.allowed_base_dir):
                    raise SecurityError(
                        f"Path traversal detected: {absolute_path} "
                        f"is outside allowed directory {self.allowed_base_dir}"
                    )
            else:
                # Fallback for Python 3.8
                try:
                    absolute_path.relative_to(self.allowed_base_dir)
                except ValueError:
                    raise SecurityError(
                        f"Path traversal detected: {absolute_path} "
                        f"is outside allowed directory {self.allowed_base_dir}"
                    )
        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Path validation failed: {e}")

    def _verify_integrity(self, file_path: Path, expected_hash: Optional[str] = None) -> str:
        """
        Verify file integrity using hash

        Args:
            file_path: Path to file
            expected_hash: Expected hash in format "algorithm:hexdigest"

        Returns:
            Computed hash

        Raises:
            SecurityError: If integrity check fails
        """
        if not expected_hash:
            # No hash provided, compute and cache
            if file_path not in self._hash_cache:
                computed = self.compute_file_hash(file_path)
                self._hash_cache[file_path] = computed
            return self._hash_cache[file_path]

        # Verify against expected hash
        computed = self.compute_file_hash(file_path)

        if computed != expected_hash:
            raise SecurityError(
                f"File integrity check failed for {file_path}\n"
                f"  Expected: {expected_hash}\n"
                f"  Computed: {computed}"
            )

        return computed

    def load_module(
        self,
        module_path: Path,
        module_name: Optional[str] = None,
        expected_hash: Optional[str] = None,
        strict_mode: bool = True
    ) -> Any:
        """
        Securely load a Python module

        Args:
            module_path: Path to module file
            module_name: Name for the loaded module (defaults to filename stem)
            expected_hash: Expected SHA256 hash for integrity check
            strict_mode: If True, enforce hash verification when provided

        Returns:
            Loaded module object

        Raises:
            SecurityError: If any security check fails

        Example:
            loader = SecureModuleLoader()
            cb_module = loader.load_module(
                Path("src/risk/circuit_breaker.py"),
                module_name="circuit_breaker"
            )
            CircuitBreaker = cb_module.CircuitBreaker
        """
        module_path = Path(module_path)

        # Step 1: Validate path (path traversal prevention)
        logger.debug(f"Validating path: {module_path}")
        self._validate_path(module_path)
        logger.debug("✓ Path validation passed")

        # Step 2: Verify integrity (if hash provided)
        if expected_hash:
            logger.debug(f"Verifying integrity with hash: {expected_hash[:16]}...")
            try:
                self._verify_integrity(module_path, expected_hash)
                logger.debug("✓ Integrity verification passed")
            except SecurityError:
                if strict_mode:
                    raise
                else:
                    logger.warning("⚠️  Integrity verification failed (non-strict mode)")

        # Step 3: Load module
        module_name = module_name or module_path.stem

        logger.info(f"Loading module: {module_name} from {module_path}")

        try:
            spec = importlib.util.spec_from_file_location(module_name, str(module_path))
            if spec is None or spec.loader is None:
                raise SecurityError(f"Failed to create module spec for {module_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            logger.info(f"✅ Module loaded successfully: {module_name}")
            return module

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Failed to load module {module_path}: {e}")


# Global loader instance (lazy-initialized)
_global_loader = None


def get_secure_loader(allowed_base_dir: Optional[Path] = None) -> SecureModuleLoader:
    """Get or create global secure loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = SecureModuleLoader(allowed_base_dir)
    return _global_loader


def load_module_secure(
    module_path: Path,
    module_name: Optional[str] = None,
    expected_hash: Optional[str] = None
) -> Any:
    """
    Convenience function for secure module loading

    Args:
        module_path: Path to module
        module_name: Module name
        expected_hash: Expected hash for verification

    Returns:
        Loaded module
    """
    loader = get_secure_loader()
    return loader.load_module(module_path, module_name, expected_hash)

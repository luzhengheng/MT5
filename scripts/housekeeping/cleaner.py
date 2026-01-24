#!/usr/bin/env python3
"""
Cleaner Module - Recursive cleanup of pycache and temp files
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from pathlib import Path
from typing import List, Set, Tuple, Dict, Any
from datetime import datetime
import fnmatch

from .base_module import BaseModule, ModuleResult, FileOperation, OperationType
from .config import CleanerConfig


class Cleaner(BaseModule):
    """
    Cleaner module for removing cache directories and temporary files.

    Responsibilities:
    - Recursively find and delete __pycache__ directories
    - Remove .pyc, .pyo, and other compiled Python files
    - Clean up temporary directories and files
    - Respect exclusion patterns for protected directories
    """

    def __init__(
        self,
        root_path: Path,
        config: CleanerConfig = None,
        dry_run: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the Cleaner module.

        Args:
            root_path: Absolute path to project root
            config: CleanerConfig instance
            dry_run: If True, only simulate deletions
            verbose: If True, output detailed logs
        """
        super().__init__(root_path, dry_run, verbose)
        self.config = config or CleanerConfig()
        self._dirs_to_delete: List[Path] = []
        self._files_to_delete: List[Path] = []

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded from scanning."""
        # Check each part of the path against exclusion patterns
        for part in path.parts:
            if part in self.config.exclude_dirs:
                return True
        return False

    def _scan_cache_directories(self) -> List[Path]:
        """Find all cache directories matching patterns."""
        cache_dirs = []

        for pattern in self.config.delete_dir_patterns:
            self.logger.debug(f"Scanning for directories matching: {pattern}")

            # Handle glob patterns
            if '*' in pattern:
                for match in self.root_path.rglob(pattern):
                    if match.is_dir() and not self._should_exclude(match):
                        cache_dirs.append(match)
            else:
                # Exact directory name match
                for match in self.root_path.rglob(pattern):
                    if match.is_dir() and match.name == pattern and not self._should_exclude(match):
                        cache_dirs.append(match)

        # Remove duplicates and sort
        cache_dirs = sorted(set(cache_dirs))
        self.logger.info(f"Found {len(cache_dirs)} cache directories to clean")

        return cache_dirs

    def _scan_temp_files(self) -> List[Path]:
        """Find all temporary files matching patterns."""
        temp_files = []

        # Scan for temp file patterns in the entire tree
        for pattern in self.config.temp_file_patterns:
            self.logger.debug(f"Scanning for files matching: {pattern}")

            for match in self.root_path.rglob(pattern):
                if match.is_file() and not self._should_exclude(match):
                    temp_files.append(match)

        # Also scan specific temp directories
        for temp_dir_name in self.config.temp_directories:
            temp_dir = self.root_path / temp_dir_name
            if temp_dir.exists() and temp_dir.is_dir():
                self.logger.debug(f"Scanning temp directory: {temp_dir}")
                for file_path in temp_dir.rglob('*'):
                    if file_path.is_file():
                        temp_files.append(file_path)

        # Remove duplicates and sort
        temp_files = sorted(set(temp_files))
        self.logger.info(f"Found {len(temp_files)} temporary files to clean")

        return temp_files

    def _scan_temp_directories(self) -> List[Path]:
        """Find temporary directories to clean."""
        temp_dirs = []

        for temp_dir_name in self.config.temp_directories:
            temp_dir = self.root_path / temp_dir_name
            if temp_dir.exists() and temp_dir.is_dir():
                temp_dirs.append(temp_dir)

        self.logger.info(f"Found {len(temp_dirs)} temporary directories")
        return temp_dirs

    def scan(self) -> List[Path]:
        """
        Scan for all files and directories to clean.

        Returns:
            Combined list of all paths to be cleaned
        """
        self.logger.info(f"Starting scan from: {self.root_path}")

        self._dirs_to_delete = self._scan_cache_directories()
        self._files_to_delete = self._scan_temp_files()

        # Combine all paths
        all_paths = self._dirs_to_delete + self._files_to_delete

        self.logger.info(
            f"Scan complete: {len(self._dirs_to_delete)} directories, "
            f"{len(self._files_to_delete)} files to clean"
        )

        return all_paths

    def execute(self) -> ModuleResult:
        """
        Execute the cleaning operation.

        Returns:
            ModuleResult with details of all operations
        """
        self._result = ModuleResult(module_name="Cleaner")
        self._result.start_time = datetime.now()

        try:
            # Perform scan if not already done
            if not self._dirs_to_delete and not self._files_to_delete:
                self.scan()

            # Delete cache directories
            self.logger.info("Cleaning cache directories...")
            for dir_path in self._dirs_to_delete:
                operation = self._safe_delete_dir(dir_path)
                self._result.operations.append(operation)

            # Delete temporary files
            self.logger.info("Cleaning temporary files...")
            for file_path in self._files_to_delete:
                # Skip files that were inside deleted directories
                if not file_path.exists():
                    continue
                operation = self._safe_delete_file(file_path)
                self._result.operations.append(operation)

            self._result.success = True

        except Exception as e:
            self._result.success = False
            self._result.error_message = str(e)
            self.logger.error(f"Cleaner execution failed: {e}")

        finally:
            self._result.end_time = datetime.now()

        # Log summary
        self.logger.info(
            f"Cleaner complete: {self._result.successful_operations} successful, "
            f"{self._result.failed_operations} failed, "
            f"{self._result.total_bytes_processed:,} bytes freed"
        )

        return self._result

    def get_size_summary(self) -> Dict[str, int]:
        """Get summary of sizes before cleanup."""
        total_dirs_size = sum(self._get_dir_size(d) for d in self._dirs_to_delete if d.exists())
        total_files_size = sum(self._get_file_size(f) for f in self._files_to_delete if f.exists())

        return {
            "cache_dirs_bytes": total_dirs_size,
            "temp_files_bytes": total_files_size,
            "total_bytes": total_dirs_size + total_files_size,
            "cache_dirs_count": len(self._dirs_to_delete),
            "temp_files_count": len(self._files_to_delete),
        }

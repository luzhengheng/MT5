#!/usr/bin/env python3
"""
Base Module for Housekeeping Operations
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import logging
import os


class OperationType(Enum):
    """Types of housekeeping operations."""
    DELETE = "delete"
    ARCHIVE = "archive"
    MOVE = "move"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class FileOperation:
    """Represents a single file operation."""
    source_path: Path
    operation: OperationType
    destination_path: Optional[Path] = None
    size_bytes: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "source": str(self.source_path),
            "operation": self.operation.value,
            "destination": str(self.destination_path) if self.destination_path else None,
            "size_bytes": self.size_bytes,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error_message,
        }


@dataclass
class ModuleResult:
    """Result of a module execution."""
    module_name: str
    operations: List[FileOperation] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: bool = True
    error_message: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def total_files_processed(self) -> int:
        """Count total files processed."""
        return len(self.operations)

    @property
    def total_bytes_processed(self) -> int:
        """Sum of all bytes processed."""
        return sum(op.size_bytes for op in self.operations)

    @property
    def successful_operations(self) -> int:
        """Count successful operations."""
        return sum(1 for op in self.operations if op.success)

    @property
    def failed_operations(self) -> int:
        """Count failed operations."""
        return sum(1 for op in self.operations if not op.success)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "module_name": self.module_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "summary": {
                "total_files": self.total_files_processed,
                "total_bytes": self.total_bytes_processed,
                "successful": self.successful_operations,
                "failed": self.failed_operations,
            },
            "operations": [op.to_dict() for op in self.operations],
        }


class BaseModule(ABC):
    """
    Abstract base class for all housekeeping modules.

    Provides common functionality for file scanning, logging,
    and result reporting.
    """

    def __init__(
        self,
        root_path: Path,
        dry_run: bool = False,
        verbose: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the base module.

        Args:
            root_path: Absolute path to project root
            dry_run: If True, only simulate operations
            verbose: If True, output detailed logs
            logger: Optional custom logger instance
        """
        self.root_path = root_path.resolve()
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = logger or self._create_logger()
        self._result = ModuleResult(module_name=self.__class__.__name__)

    def _create_logger(self) -> logging.Logger:
        """Create a configured logger for this module."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _get_file_size(self, path: Path) -> int:
        """Safely get file size in bytes."""
        try:
            return path.stat().st_size if path.is_file() else 0
        except (OSError, PermissionError):
            return 0

    def _get_dir_size(self, path: Path) -> int:
        """Calculate total size of directory contents."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += self._get_file_size(entry)
        except (OSError, PermissionError):
            pass
        return total

    def _safe_delete_file(self, path: Path) -> FileOperation:
        """Safely delete a file with error handling."""
        operation = FileOperation(
            source_path=path,
            operation=OperationType.DELETE,
            size_bytes=self._get_file_size(path)
        )

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would delete file: {path}")
            return operation

        try:
            path.unlink()
            self.logger.debug(f"Deleted file: {path}")
        except PermissionError as e:
            operation.success = False
            operation.error_message = f"Permission denied: {e}"
            self.logger.warning(f"Cannot delete {path}: {e}")
        except OSError as e:
            operation.success = False
            operation.error_message = str(e)
            self.logger.error(f"Error deleting {path}: {e}")

        return operation

    def _safe_delete_dir(self, path: Path) -> FileOperation:
        """Safely delete a directory recursively."""
        operation = FileOperation(
            source_path=path,
            operation=OperationType.DELETE,
            size_bytes=self._get_dir_size(path)
        )

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would delete directory: {path}")
            return operation

        try:
            import shutil
            shutil.rmtree(path)
            self.logger.debug(f"Deleted directory: {path}")
        except PermissionError as e:
            operation.success = False
            operation.error_message = f"Permission denied: {e}"
            self.logger.warning(f"Cannot delete {path}: {e}")
        except OSError as e:
            operation.success = False
            operation.error_message = str(e)
            self.logger.error(f"Error deleting {path}: {e}")

        return operation

    def _safe_move(self, source: Path, destination: Path) -> FileOperation:
        """Safely move a file or directory."""
        operation = FileOperation(
            source_path=source,
            operation=OperationType.MOVE,
            destination_path=destination,
            size_bytes=self._get_file_size(source) if source.is_file() else self._get_dir_size(source)
        )

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would move: {source} -> {destination}")
            return operation

        try:
            import shutil
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            self.logger.debug(f"Moved: {source} -> {destination}")
        except PermissionError as e:
            operation.success = False
            operation.error_message = f"Permission denied: {e}"
            self.logger.warning(f"Cannot move {source}: {e}")
        except OSError as e:
            operation.success = False
            operation.error_message = str(e)
            self.logger.error(f"Error moving {source}: {e}")

        return operation

    def _matches_pattern(self, name: str, patterns: List[str]) -> bool:
        """Check if a name matches any of the given patterns."""
        import fnmatch
        return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)

    @abstractmethod
    def scan(self) -> List[Path]:
        """
        Scan for files/directories to process.

        Returns:
            List of paths to be processed
        """
        pass

    @abstractmethod
    def execute(self) -> ModuleResult:
        """
        Execute the housekeeping operation.

        Returns:
            ModuleResult containing operation details
        """
        pass

    def report(self) -> Dict[str, Any]:
        """Generate a report of operations performed."""
        return self._result.to_dict()

# RFC-137: System Housekeeping Technical Specification

**Protocol Version**: 4.4  
**Task ID**: #137  
**Status**: Draft  
**Depends On**: Task #136 (Completed)  
**Author**: System Architect  
**Date**: 2025-01-13

---

## 1. 背景 (Context)

### 1.1 任务背景

随着项目开发迭代，系统中积累了大量临时文件、缓存目录和冗余脚本。这些文件占用磁盘空间，影响代码库的整洁性，并可能导致版本控制混乱。

### 1.2 前置任务

Task #136 已完成，为本任务提供了稳定的系统基础环境。

### 1.3 任务目标

1. **递归清理**: 删除所有 `__pycache__` 目录和 `/tmp` 临时文件
2. **归档处理**: 将 `.bak` 和 `.log` 文件移动至归档目录
3. **脚本整合**: 识别并迁移冗余脚本至 `legacy_archive` 目录

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Housekeeping System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Cleaner   │    │  Archiver   │    │ ScriptConsolidator  │ │
│  │   Module    │    │   Module    │    │      Module         │ │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘ │
│         │                  │                      │             │
│         └──────────────────┼──────────────────────┘             │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │  HousekeepingOrchestrator                  │
│                   └────────┬────────┘                          │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │  ReportGenerator │                          │
│                   └─────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
[Project Root]
      │
      ▼
┌─────────────────┐
│  File Scanner   │──────────────────────────────────────┐
└────────┬────────┘                                      │
         │                                               │
         ▼                                               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ __pycache__     │  │ .bak/.log files │  │ Redundant Scripts   │
│ /tmp files      │  │                 │  │                     │
└────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘
         │                    │                      │
         ▼                    ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│    DELETE       │  │    ARCHIVE      │  │   MOVE TO LEGACY    │
│                 │  │ /archive/logs/  │  │  /legacy_archive/   │
│                 │  │ /archive/backup/│  │                     │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
         │                    │                      │
         └────────────────────┼──────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Summary Report │
                    │  housekeeping_  │
                    │  report.json    │
                    └─────────────────┘
```

### 2.3 类图

```
┌────────────────────────────────────────┐
│           BaseModule (ABC)             │
├────────────────────────────────────────┤
│ + root_path: Path                      │
│ + dry_run: bool                        │
│ + logger: Logger                       │
├────────────────────────────────────────┤
│ + execute() -> ModuleResult            │
│ + scan() -> List[Path]                 │
│ + report() -> Dict                     │
└───────────────────┬────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌─────────────────┐
│  Cleaner  │ │  Archiver │ │ScriptConsolidator│
├───────────┤ ├───────────┤ ├─────────────────┤
│ patterns  │ │ archive_  │ │ redundancy_     │
│           │ │ base_path │ │ patterns        │
├───────────┤ ├───────────┤ ├─────────────────┤
│ clean()   │ │ archive() │ │ consolidate()   │
└───────────┘ └───────────┘ └─────────────────┘

┌────────────────────────────────────────┐
│      HousekeepingOrchestrator          │
├────────────────────────────────────────┤
│ + modules: List[BaseModule]            │
│ + config: HousekeepingConfig           │
├────────────────────────────────────────┤
│ + run() -> OrchestratorResult          │
│ + generate_report() -> Path            │
└────────────────────────────────────────┘
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 目录结构

```
/project_root/
├── scripts/
│   └── housekeeping/
│       ├── __init__.py
│       ├── config.py
│       ├── base_module.py
│       ├── cleaner.py
│       ├── archiver.py
│       ├── script_consolidator.py
│       ├── orchestrator.py
│       └── run_housekeeping.py
├── archive/
│   ├── logs/
│   └── backup/
├── legacy_archive/
└── reports/
    └── housekeeping/
```

### 3.2 配置模块

**文件路径**: `/project_root/scripts/housekeeping/config.py`

```python
#!/usr/bin/env python3
"""
Housekeeping Configuration Module
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set
from datetime import datetime
import json


@dataclass
class CleanerConfig:
    """Configuration for the Cleaner module."""
    
    # Directories to recursively delete
    delete_dir_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "*.egg-info",
        ".tox",
        ".nox",
    ])
    
    # Temporary file patterns to delete
    temp_file_patterns: List[str] = field(default_factory=lambda: [
        "*.pyc",
        "*.pyo",
        "*.tmp",
        "*.temp",
        "*~",
        ".DS_Store",
        "Thumbs.db",
    ])
    
    # Directories to scan for temp files (relative to root)
    temp_directories: List[str] = field(default_factory=lambda: [
        "tmp",
        "temp",
        ".tmp",
    ])
    
    # Directories to exclude from scanning
    exclude_dirs: Set[str] = field(default_factory=lambda: {
        ".git",
        ".svn",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
    })


@dataclass
class ArchiverConfig:
    """Configuration for the Archiver module."""
    
    # File extensions to archive
    archive_extensions: List[str] = field(default_factory=lambda: [
        ".bak",
        ".backup",
        ".log",
        ".log.1",
        ".log.2",
        ".old",
    ])
    
    # Archive destination directories (relative to root)
    log_archive_dir: str = "archive/logs"
    backup_archive_dir: str = "archive/backup"
    
    # Preserve directory structure in archive
    preserve_structure: bool = True
    
    # Compress archived files older than N days
    compress_after_days: int = 7
    
    # Maximum archive size before rotation (MB)
    max_archive_size_mb: int = 100


@dataclass
class ScriptConsolidatorConfig:
    """Configuration for the Script Consolidator module."""
    
    # Legacy archive directory (relative to root)
    legacy_archive_dir: str = "legacy_archive"
    
    # Patterns indicating redundant/deprecated scripts
    redundancy_indicators: List[str] = field(default_factory=lambda: [
        "_old",
        "_backup",
        "_deprecated",
        "_legacy",
        "_v1",
        "_v2",
        ".bak",
        "_copy",
        "_temp",
        "test_old_",
        "old_",
    ])
    
    # Script directories to scan
    script_directories: List[str] = field(default_factory=lambda: [
        "scripts",
        "tools",
        "utils",
        "bin",
    ])
    
    # File extensions considered as scripts
    script_extensions: List[str] = field(default_factory=lambda: [
        ".py",
        ".sh",
        ".bash",
        ".zsh",
        ".ps1",
        ".bat",
        ".cmd",
    ])
    
    # Files to never consolidate (exact names)
    protected_files: Set[str] = field(default_factory=lambda: {
        "__init__.py",
        "setup.py",
        "conftest.py",
        "manage.py",
    })


@dataclass
class HousekeepingConfig:
    """Master configuration for the Housekeeping system."""
    
    # Project root path (absolute)
    root_path: Path = field(default_factory=lambda: Path.cwd())
    
    # Module configurations
    cleaner: CleanerConfig = field(default_factory=CleanerConfig)
    archiver: ArchiverConfig = field(default_factory=ArchiverConfig)
    consolidator: ScriptConsolidatorConfig = field(default_factory=ScriptConsolidatorConfig)
    
    # Global settings
    dry_run: bool = False  # If True, only report what would be done
    verbose: bool = True
    create_report: bool = True
    report_dir: str = "reports/housekeeping"
    
    # Safety settings
    require_confirmation: bool = True
    max_files_without_confirmation: int = 50
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "housekeeping.log"
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        return {
            "root_path": str(self.root_path),
            "dry_run": self.dry_run,
            "verbose": self.verbose,
            "create_report": self.create_report,
            "report_dir": self.report_dir,
            "cleaner": {
                "delete_dir_patterns": self.cleaner.delete_dir_patterns,
                "temp_file_patterns": self.cleaner.temp_file_patterns,
                "temp_directories": self.cleaner.temp_directories,
                "exclude_dirs": list(self.cleaner.exclude_dirs),
            },
            "archiver": {
                "archive_extensions": self.archiver.archive_extensions,
                "log_archive_dir": self.archiver.log_archive_dir,
                "backup_archive_dir": self.archiver.backup_archive_dir,
                "preserve_structure": self.archiver.preserve_structure,
            },
            "consolidator": {
                "legacy_archive_dir": self.consolidator.legacy_archive_dir,
                "redundancy_indicators": self.consolidator.redundancy_indicators,
                "script_directories": self.consolidator.script_directories,
            },
        }
    
    @classmethod
    def from_file(cls, config_path: Path) -> "HousekeepingConfig":
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        config = cls()
        config.root_path = Path(data.get("root_path", Path.cwd()))
        config.dry_run = data.get("dry_run", False)
        config.verbose = data.get("verbose", True)
        
        return config
    
    def save(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


def get_default_config(root_path: Path = None) -> HousekeepingConfig:
    """Get default configuration with optional root path override."""
    config = HousekeepingConfig()
    if root_path:
        config.root_path = root_path.resolve()
    return config
```

### 3.3 基础模块

**文件路径**: `/project_root/scripts/housekeeping/base_module.py`

```python
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
```

### 3.4 清理模块

**文件路径**: `/project_root/scripts/housekeeping/cleaner.py`

```python
#!/usr/bin/env python3
"""
Cleaner Module - Recursive cleanup of pycache and temp files
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from pathlib import Path
from typing import List, Set, Tuple
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
    
    def get_size_summary(self) ->
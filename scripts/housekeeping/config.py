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

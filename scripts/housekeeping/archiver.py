#!/usr/bin/env python3
"""
Archiver Module - Archive .bak, .log files to archive directory
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import fnmatch

from .base_module import BaseModule, ModuleResult, FileOperation, OperationType
from .config import ArchiverConfig


class Archiver(BaseModule):
    """
    Archiver module for moving backup and log files to archive directory.

    Responsibilities:
    - Find all .bak, .backup, .log files
    - Move them to appropriate archive directories
    - Preserve directory structure if configured
    - Track all archived files
    """

    def __init__(
        self,
        root_path: Path,
        config: ArchiverConfig = None,
        dry_run: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the Archiver module.

        Args:
            root_path: Absolute path to project root
            config: ArchiverConfig instance
            dry_run: If True, only simulate archiving
            verbose: If True, output detailed logs
        """
        super().__init__(root_path, dry_run, verbose)
        self.config = config or ArchiverConfig()
        self._files_to_archive: List[Path] = []
        self._log_dir = root_path / self.config.log_archive_dir
        self._backup_dir = root_path / self.config.backup_archive_dir

    def _get_archive_destination(self, file_path: Path) -> Path:
        """Determine the archive destination for a file."""
        # Determine if it's a log or backup file
        if file_path.suffix in ['.log', '.log.1', '.log.2'] or 'log' in file_path.name.lower():
            base_archive = self._log_dir
        else:
            base_archive = self._backup_dir

        # Preserve structure or flatten?
        if self.config.preserve_structure:
            # Create relative path structure in archive
            relative_path = file_path.relative_to(self.root_path)
            parent_structure = relative_path.parent
            return base_archive / parent_structure / file_path.name
        else:
            return base_archive / file_path.name

    def _scan_archive_files(self) -> List[Path]:
        """Find all files matching archive patterns."""
        archive_files = []

        for pattern in self.config.archive_extensions:
            self.logger.debug(f"Scanning for files matching: {pattern}")

            for match in self.root_path.rglob('*'):
                if match.is_file() and fnmatch.fnmatch(match.name, f"*{pattern}" if not pattern.startswith('*') else pattern):
                    # Skip files already in archive directories
                    if 'archive' not in str(match):
                        archive_files.append(match)

        # Remove duplicates and sort
        archive_files = sorted(set(archive_files))
        self.logger.info(f"Found {len(archive_files)} files to archive")

        return archive_files

    def scan(self) -> List[Path]:
        """
        Scan for all files to archive.

        Returns:
            List of paths to be archived
        """
        self.logger.info(f"Starting scan from: {self.root_path}")

        self._files_to_archive = self._scan_archive_files()

        self.logger.info(f"Scan complete: {len(self._files_to_archive)} files to archive")

        return self._files_to_archive

    def execute(self) -> ModuleResult:
        """
        Execute the archiving operation.

        Returns:
            ModuleResult with details of all operations
        """
        self._result = ModuleResult(module_name="Archiver")
        self._result.start_time = datetime.now()

        try:
            # Perform scan if not already done
            if not self._files_to_archive:
                self.scan()

            # Archive files
            self.logger.info("Archiving files...")
            for file_path in self._files_to_archive:
                if not file_path.exists():
                    continue

                destination = self._get_archive_destination(file_path)
                operation = self._safe_move(file_path, destination)
                self._result.operations.append(operation)

            self._result.success = True

        except Exception as e:
            self._result.success = False
            self._result.error_message = str(e)
            self.logger.error(f"Archiver execution failed: {e}")

        finally:
            self._result.end_time = datetime.now()

        # Log summary
        self.logger.info(
            f"Archiver complete: {self._result.successful_operations} successful, "
            f"{self._result.failed_operations} failed, "
            f"{self._result.total_bytes_processed:,} bytes archived"
        )

        return self._result

    def get_archive_summary(self) -> Dict[str, Any]:
        """Get summary of files to be archived."""
        total_size = sum(self._get_file_size(f) for f in self._files_to_archive if f.exists())

        return {
            "total_files": len(self._files_to_archive),
            "total_bytes": total_size,
            "log_dir": str(self._log_dir),
            "backup_dir": str(self._backup_dir),
        }

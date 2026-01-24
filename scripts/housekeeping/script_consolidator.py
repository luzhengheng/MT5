#!/usr/bin/env python3
"""
Script Consolidator Module - Move redundant scripts to legacy archive
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .base_module import BaseModule, ModuleResult, FileOperation, OperationType
from .config import ScriptConsolidatorConfig


class ScriptConsolidator(BaseModule):
    """
    Script Consolidator module for identifying and archiving deprecated scripts.

    Responsibilities:
    - Identify scripts matching redundancy patterns
    - Move them to legacy_archive directory
    - Preserve directory structure
    - Protect critical files
    """

    def __init__(
        self,
        root_path: Path,
        config: ScriptConsolidatorConfig = None,
        dry_run: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the Script Consolidator module.

        Args:
            root_path: Absolute path to project root
            config: ScriptConsolidatorConfig instance
            dry_run: If True, only simulate consolidation
            verbose: If True, output detailed logs
        """
        super().__init__(root_path, dry_run, verbose)
        self.config = config or ScriptConsolidatorConfig()
        self._scripts_to_consolidate: List[Path] = []
        self._legacy_archive = root_path / self.config.legacy_archive_dir

    def _is_redundant_script(self, file_path: Path) -> bool:
        """Check if a script file matches redundancy patterns."""
        file_name = file_path.name

        # Check if file is protected
        if file_name in self.config.protected_files:
            return False

        # Check against redundancy indicators
        for indicator in self.config.redundancy_indicators:
            if indicator in file_name:
                return True

        return False

    def _scan_scripts(self) -> List[Path]:
        """Find all scripts matching redundancy patterns."""
        scripts = []

        # Scan each script directory
        for script_dir_name in self.config.script_directories:
            script_dir = self.root_path / script_dir_name

            if not script_dir.exists() or not script_dir.is_dir():
                self.logger.debug(f"Script directory not found: {script_dir}")
                continue

            self.logger.debug(f"Scanning script directory: {script_dir}")

            for file_path in script_dir.rglob('*'):
                if not file_path.is_file():
                    continue

                # Check if it has a script extension
                if file_path.suffix not in self.config.script_extensions:
                    continue

                # Check if it's redundant
                if self._is_redundant_script(file_path):
                    scripts.append(file_path)

        # Remove duplicates and sort
        scripts = sorted(set(scripts))
        self.logger.info(f"Found {len(scripts)} redundant scripts to consolidate")

        return scripts

    def _get_consolidation_destination(self, file_path: Path) -> Path:
        """Determine the consolidation destination for a script."""
        # Preserve relative structure from script directory
        for script_dir_name in self.config.script_directories:
            script_dir = self.root_path / script_dir_name

            if file_path.is_relative_to(script_dir) if hasattr(Path, 'is_relative_to') else str(file_path).startswith(str(script_dir)):
                try:
                    relative_path = file_path.relative_to(script_dir)
                    return self._legacy_archive / script_dir_name / relative_path
                except ValueError:
                    pass

        # Fallback: just use filename
        return self._legacy_archive / file_path.name

    def scan(self) -> List[Path]:
        """
        Scan for all redundant scripts.

        Returns:
            List of paths to be consolidated
        """
        self.logger.info(f"Starting scan from: {self.root_path}")

        self._scripts_to_consolidate = self._scan_scripts()

        self.logger.info(f"Scan complete: {len(self._scripts_to_consolidate)} redundant scripts found")

        return self._scripts_to_consolidate

    def execute(self) -> ModuleResult:
        """
        Execute the consolidation operation.

        Returns:
            ModuleResult with details of all operations
        """
        self._result = ModuleResult(module_name="ScriptConsolidator")
        self._result.start_time = datetime.now()

        try:
            # Perform scan if not already done
            if not self._scripts_to_consolidate:
                self.scan()

            # Consolidate scripts
            self.logger.info("Consolidating redundant scripts...")
            for script_path in self._scripts_to_consolidate:
                if not script_path.exists():
                    continue

                destination = self._get_consolidation_destination(script_path)
                operation = self._safe_move(script_path, destination)
                self._result.operations.append(operation)

            self._result.success = True

        except Exception as e:
            self._result.success = False
            self._result.error_message = str(e)
            self.logger.error(f"Script Consolidator execution failed: {e}")

        finally:
            self._result.end_time = datetime.now()

        # Log summary
        self.logger.info(
            f"Script Consolidator complete: {self._result.successful_operations} successful, "
            f"{self._result.failed_operations} failed, "
            f"{self._result.total_bytes_processed:,} bytes consolidated"
        )

        return self._result

    def get_consolidation_summary(self) -> Dict[str, Any]:
        """Get summary of scripts to be consolidated."""
        total_size = sum(self._get_file_size(f) for f in self._scripts_to_consolidate if f.exists())

        return {
            "total_scripts": len(self._scripts_to_consolidate),
            "total_bytes": total_size,
            "legacy_archive_dir": str(self._legacy_archive),
        }

#!/usr/bin/env python3
"""
Housekeeping Orchestrator - Coordinates all housekeeping modules
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from .config import HousekeepingConfig, get_default_config
from .base_module import BaseModule, ModuleResult
from .cleaner import Cleaner
from .archiver import Archiver
from .script_consolidator import ScriptConsolidator


class HousekeepingOrchestrator:
    """
    Main orchestrator for coordinating all housekeeping modules.

    Responsibilities:
    - Initialize and configure all modules
    - Execute modules in sequence
    - Collect and aggregate results
    - Generate comprehensive reports
    """

    def __init__(self, config: HousekeepingConfig = None):
        """
        Initialize the orchestrator.

        Args:
            config: HousekeepingConfig instance or None for defaults
        """
        self.config = config or get_default_config()
        self.logger = self._create_logger()
        self.modules: List[BaseModule] = []
        self.results: List[ModuleResult] = []
        self._initialize_modules()

    def _create_logger(self) -> logging.Logger:
        """Create a configured logger for the orchestrator."""
        logger = logging.getLogger("HousekeepingOrchestrator")
        logger.setLevel(getattr(logging, self.config.log_level))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_modules(self) -> None:
        """Initialize all housekeeping modules."""
        self.logger.info("Initializing housekeeping modules...")

        # Create Cleaner module
        cleaner = Cleaner(
            root_path=self.config.root_path,
            config=self.config.cleaner,
            dry_run=self.config.dry_run,
            verbose=self.config.verbose
        )
        self.modules.append(cleaner)

        # Create Archiver module
        archiver = Archiver(
            root_path=self.config.root_path,
            config=self.config.archiver,
            dry_run=self.config.dry_run,
            verbose=self.config.verbose
        )
        self.modules.append(archiver)

        # Create Script Consolidator module
        consolidator = ScriptConsolidator(
            root_path=self.config.root_path,
            config=self.config.consolidator,
            dry_run=self.config.dry_run,
            verbose=self.config.verbose
        )
        self.modules.append(consolidator)

        self.logger.info(f"Initialized {len(self.modules)} housekeeping modules")

    def run(self) -> bool:
        """
        Execute all housekeeping modules.

        Returns:
            True if all modules executed successfully, False otherwise
        """
        self.logger.info("=" * 80)
        self.logger.info("HOUSEKEEPING ORCHESTRATOR - STARTING EXECUTION")
        self.logger.info("=" * 80)
        self.logger.info(f"Dry Run Mode: {self.config.dry_run}")
        self.logger.info(f"Project Root: {self.config.root_path}")
        self.logger.info("")

        all_success = True

        for module in self.modules:
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"Module: {module.__class__.__name__}")
            self.logger.info(f"{'='*80}")

            try:
                # Scan for items to process
                self.logger.info(f"\nScanning for items to {module.__class__.__name__.lower()}...")
                items = module.scan()
                self.logger.info(f"Scan found {len(items)} items")

                # Execute the module
                self.logger.info(f"\nExecuting {module.__class__.__name__}...")
                result = module.execute()
                self.results.append(result)

                # Log result
                self.logger.info(f"\n{module.__class__.__name__} Results:")
                self.logger.info(f"  Success: {result.success}")
                self.logger.info(f"  Operations: {result.total_files_processed}")
                self.logger.info(f"  Successful: {result.successful_operations}")
                self.logger.info(f"  Failed: {result.failed_operations}")
                self.logger.info(f"  Bytes Processed: {result.total_bytes_processed:,}")
                self.logger.info(f"  Duration: {result.duration_seconds:.2f}s")

                if not result.success:
                    all_success = False
                    self.logger.error(f"  Error: {result.error_message}")

            except Exception as e:
                all_success = False
                self.logger.error(f"Exception in {module.__class__.__name__}: {e}")

        self.logger.info(f"\n{'='*80}")
        self.logger.info("HOUSEKEEPING ORCHESTRATOR - EXECUTION COMPLETE")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Overall Success: {all_success}\n")

        return all_success

    def generate_report(self) -> Optional[Path]:
        """
        Generate a comprehensive housekeeping report.

        Returns:
            Path to the generated report file, or None if generation failed
        """
        if not self.config.create_report:
            self.logger.info("Report generation disabled in config")
            return None

        try:
            self.logger.info("Generating housekeeping report...")

            # Create report directory
            report_dir = self.config.root_path / self.config.report_dir
            report_dir.mkdir(parents=True, exist_ok=True)

            # Generate report data
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.config.dry_run,
                "project_root": str(self.config.root_path),
                "modules": [result.to_dict() for result in self.results],
                "summary": self._generate_summary(),
            }

            # Write report file
            report_file = report_dir / "housekeeping_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Report generated: {report_file}")
            return report_file

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return None

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics from all module results."""
        total_files = sum(r.total_files_processed for r in self.results)
        total_bytes = sum(r.total_bytes_processed for r in self.results)
        total_successful = sum(r.successful_operations for r in self.results)
        total_failed = sum(r.failed_operations for r in self.results)
        total_duration = sum(r.duration_seconds for r in self.results)

        return {
            "total_modules": len(self.results),
            "total_files_processed": total_files,
            "total_bytes_processed": total_bytes,
            "total_successful_operations": total_successful,
            "total_failed_operations": total_failed,
            "total_duration_seconds": total_duration,
            "all_successful": all(r.success for r in self.results),
        }

    def print_summary(self) -> None:
        """Print a summary of operations to console."""
        summary = self._generate_summary()

        print("\n" + "=" * 80)
        print("HOUSEKEEPING SUMMARY")
        print("=" * 80)
        print(f"Total Modules Run: {summary['total_modules']}")
        print(f"Total Files Processed: {summary['total_files_processed']}")
        print(f"Total Bytes Processed: {summary['total_bytes_processed']:,}")
        print(f"Successful Operations: {summary['total_successful_operations']}")
        print(f"Failed Operations: {summary['total_failed_operations']}")
        print(f"Total Duration: {summary['total_duration_seconds']:.2f}s")
        print(f"Overall Success: {summary['all_successful']}")
        print("=" * 80 + "\n")

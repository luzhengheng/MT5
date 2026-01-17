#!/usr/bin/env python3
"""
Inventory Audit Script - Global Data Asset Audit Execution (Task #110)
Protocol: v4.3 (Zero-Trust Edition)

This script orchestrates the global data asset audit, generates reports,
and produces physical evidence for the zero-trust verification protocol.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audit.asset_auditor import AssetAuditor


def setup_logging(log_file: str = 'VERIFY_LOG.log') -> logging.Logger:
    """Setup logging to both console and file."""
    logger = logging.getLogger('AuditInventory')
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler (append mode for Gate 1 zero-trust protocol)
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def ensure_output_directory() -> Path:
    """Ensure output directory exists for reports."""
    task_dir = Path('/opt/mt5-crs/docs/archive/tasks/TASK_110_DATA_AUDIT')
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def main():
    """Main execution flow."""
    # Setup logging
    logger = setup_logging()

    # Print header
    logger.info("="*80)
    logger.info("TASK #110: Global Historical Data Asset Deep Audit")
    logger.info("Protocol: v4.3 (Zero-Trust Edition)")
    logger.info(f"Execution started: {datetime.now().isoformat()}")
    logger.info("="*80)

    try:
        # Ensure output directory
        output_dir = ensure_output_directory()
        logger.info(f"Output directory: {output_dir}")

        # Create auditor instance
        logger.info("\nInitializing AssetAuditor...")
        auditor = AssetAuditor(logger=logger)

        # Get data roots to scan
        data_roots = auditor._get_default_roots()
        logger.info(f"Configured data roots: {len(data_roots)}")
        for root in data_roots:
            logger.info(f"  - {root}")

        # Execute full scan
        logger.info("\nStarting comprehensive data asset scan...")
        results = auditor.scan_all(data_roots)

        logger.info(f"\n✓ Scan completed successfully")
        logger.info(f"✓ Total files scanned: {len(results)}")
        logger.info(f"✓ Total errors: {len(auditor.errors)}")

        # Generate JSON report
        logger.info("\nGenerating JSON report...")
        json_report = auditor.generate_json_report()

        json_file = output_dir / 'DATA_MAP.json'
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        logger.info(f"✓ JSON report written to: {json_file}")

        # Generate Markdown report
        logger.info("\nGenerating Markdown report...")
        md_report = auditor.generate_markdown_report()

        md_file = output_dir / 'DATA_INVENTORY_REPORT.md'
        with open(md_file, 'w') as f:
            f.write(md_report)
        logger.info(f"✓ Markdown report written to: {md_file}")

        # Physical evidence logging for zero-trust protocol
        logger.info("\n" + "="*80)
        logger.info("PHYSICAL EVIDENCE FOR ZERO-TRUST VERIFICATION")
        logger.info("="*80)

        logger.info(f"UUID: audit-task-110-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Total Files Scanned: {len(results)}")
        logger.info(f"Total Size: {json_report['total_size_mb']:.2f} MB")
        logger.info(f"Scan Duration: {json_report['scan_duration_seconds']:.2f} seconds")

        quality = json_report['data_quality']
        logger.info(f"Quality Stats:")
        logger.info(f"  - Healthy: {quality['healthy']}")
        logger.info(f"  - Incomplete: {quality['incomplete']}")
        logger.info(f"  - Corrupted: {quality['corrupted']}")

        logger.info(f"Timeframe identification completed: {len(auditor.results)} files analyzed")

        logger.info("\n" + "="*80)
        logger.info("AUDIT EXECUTION COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        logger.info(f"Completion time: {datetime.now().isoformat()}")

        return 0

    except Exception as e:
        logger.error(f"FATAL ERROR: {str(e)}", exc_info=True)
        logger.error("Audit execution failed")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

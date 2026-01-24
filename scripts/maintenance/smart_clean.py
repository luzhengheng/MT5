#!/usr/bin/env python3
"""
Smart Housekeeping Cleanup Entry Point
RFC-137: System Housekeeping
Protocol v4.4 Compliant

Usage:
    python3 scripts/maintenance/smart_clean.py --dry-run
    python3 scripts/maintenance/smart_clean.py --execute
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.housekeeping import (
    HousekeepingOrchestrator,
    HousekeepingConfig,
    get_default_config,
)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Smart Housekeeping Cleanup Tool - RFC-137",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run        # Preview what would be cleaned (default)
  %(prog)s --execute        # Actually perform the cleanup
  %(prog)s --verbose        # Show detailed output
  %(prog)s --root /path     # Use custom project root
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Preview operations without making changes (default)'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform the cleanup operations'
    )

    parser.add_argument(
        '--root',
        type=Path,
        default=None,
        help='Project root path (default: current working directory)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Show detailed output'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation'
    )

    return parser


def main():
    """Main entry point for the housekeeping tool."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Determine project root
    if args.root:
        project_root = args.root.resolve()
    else:
        # Try to find the project root by looking for common markers
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists() or (current / 'setup.py').exists():
                project_root = current
                break
            current = current.parent
        else:
            project_root = Path.cwd()

    # Create configuration
    config = HousekeepingConfig(
        root_path=project_root,
        dry_run=not args.execute,  # If execute flag is set, dry_run is False
        verbose=args.verbose and not args.quiet,
        create_report=not args.no_report,
    )

    print("\n" + "=" * 80)
    print("SMART HOUSEKEEPING CLEANUP TOOL - RFC-137")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Mode: {'DRY RUN' if config.dry_run else 'EXECUTE'}")
    print(f"Verbose: {config.verbose}")
    print("=" * 80 + "\n")

    # Create and run orchestrator
    orchestrator = HousekeepingOrchestrator(config)

    try:
        # Run all modules
        success = orchestrator.run()

        # Print summary
        orchestrator.print_summary()

        # Generate report
        report_path = orchestrator.generate_report()
        if report_path:
            print(f"📄 Report saved: {report_path}\n")

        # Return appropriate exit code
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\nCleanup interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

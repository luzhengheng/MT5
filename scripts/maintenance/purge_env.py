#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Safe Purge Protocol

Task #024.01: Safely reset runtime state while protecting configuration.

This script provides a "Reset Button" for the MT5 trading system:
- Stops Docker services
- Clears caches and logs
- Protects critical files (models, config, .env, source code)
- Requires user confirmation
- Verifies safety before deletion

Usage:
  python3 scripts/maintenance/purge_env.py                # Interactive
  python3 scripts/maintenance/purge_env.py --force       # Automatic
  python3 scripts/maintenance/purge_env.py --dry-run     # Preview
  python3 scripts/maintenance/purge_env.py --full        # Include volumes
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class SafePurge:
    """Environment purge protocol with safety guards"""

    # Paths that should NEVER be deleted
    PROTECTED_PATHS = {
        'models',
        'config',
        'src',
        'scripts',
        'docs',
        '.git',
        '.gitignore',
        '.env',
        '.env.example',
        'requirements.txt',
        'Dockerfile.strategy',
        'Dockerfile.api',
        'docker-compose.prod.yml'
    }

    # Paths that are safe to delete
    EPHEMERAL_PATHS = [
        'logs',
        'data/redis',
        'data/temp'
    ]

    def __init__(self, project_root=None, dry_run=False, force=False, full=False, verbose=False):
        self.project_root = Path(project_root or os.getcwd())
        self.dry_run = dry_run
        self.force = force
        self.full = full
        self.verbose = verbose
        self.deleted_items = []
        self.total_size = 0

    def is_protected(self, path):
        """Check if path is in protected list"""
        path_obj = Path(path)

        # Check direct matches
        if path_obj.name in self.PROTECTED_PATHS:
            return True

        # Check parent directories
        for protected in self.PROTECTED_PATHS:
            if protected in str(path):
                return True

        return False

    def log(self, message):
        """Print message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def confirm(self):
        """Ask user for confirmation"""
        if self.force:
            return True

        print()
        print(f"{RED}⚠️  Are you sure you want to proceed? (y/n): {RESET}", end="", flush=True)

        response = input().strip().lower()

        if response != 'y':
            print(f"{YELLOW}Purge cancelled{RESET}")
            return False

        return True

    def stop_services(self):
        """Stop Docker services"""
        if self.verbose:
            self.log("Stopping Docker services...")

        if self.dry_run:
            self.log(f"{YELLOW}[DRY-RUN]{RESET} docker compose down")
            return

        try:
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                self.log(f"{GREEN}✅ Docker services stopped{RESET}")
            else:
                self.log(f"{YELLOW}⚠️  Docker compose down: {result.stderr.decode()}{RESET}")

        except FileNotFoundError:
            self.log(f"{YELLOW}⚠️  docker-compose not installed, skipping{RESET}")
        except Exception as e:
            self.log(f"{RED}❌ Error stopping services: {e}{RESET}")

    def delete_path(self, path):
        """Safely delete a path"""
        full_path = self.project_root / path

        # Safety check
        if self.is_protected(str(full_path)):
            self.log(f"{YELLOW}⚠️  Skipping protected path: {path}{RESET}")
            return

        if not full_path.exists():
            if self.verbose:
                self.log(f"{YELLOW}ℹ️  Path doesn't exist: {path}{RESET}")
            return

        if self.dry_run:
            self.log(f"{YELLOW}[DRY-RUN]{RESET} rm -rf {path}")
            return

        try:
            if full_path.is_file():
                size = full_path.stat().st_size
                full_path.unlink()
            else:
                size = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
                shutil.rmtree(full_path)

            self.total_size += size
            self.deleted_items.append((path, size))
            self.log(f"{GREEN}✅ Deleted {path}{RESET} ({self._format_size(size)})")

        except PermissionError:
            self.log(f"{RED}❌ Permission denied: {path}{RESET}")
        except Exception as e:
            self.log(f"{RED}❌ Error deleting {path}: {e}{RESET}")

    def purge_logs(self):
        """Remove log files"""
        if self.verbose:
            self.log("Purging logs...")

        self.delete_path('logs')

    def purge_cache(self):
        """Remove Redis cache"""
        if self.verbose:
            self.log("Purging cache...")

        self.delete_path('data/redis')
        self.delete_path('data/temp')

    def cleanup_docker_volumes(self):
        """Remove Docker named volumes"""
        if not self.full:
            return

        if self.verbose:
            self.log("Cleaning up Docker volumes...")

        if self.dry_run:
            self.log(f"{YELLOW}[DRY-RUN]{RESET} docker volume rm redis_data postgres_data prometheus_data grafana_data logs_volume")
            return

        volumes = ['redis_data', 'postgres_data', 'prometheus_data', 'grafana_data', 'logs_volume']

        for volume in volumes:
            try:
                subprocess.run(
                    ["docker", "volume", "rm", volume],
                    capture_output=True,
                    timeout=10
                )
                self.log(f"{GREEN}✅ Removed Docker volume: {volume}{RESET}")
            except Exception as e:
                self.log(f"{YELLOW}⚠️  Could not remove volume {volume}: {e}{RESET}")

    def verify_protection(self):
        """Verify protected paths still exist"""
        if self.verbose:
            self.log("Verifying protection...")

        missing = []

        for protected_path in self.PROTECTED_PATHS:
            full_path = self.project_root / protected_path

            if not full_path.exists():
                missing.append(protected_path)
                self.log(f"{RED}❌ Missing: {protected_path}{RESET}")
            else:
                if self.verbose:
                    self.log(f"{GREEN}✅ Protected: {protected_path}{RESET}")

        return len(missing) == 0

    @staticmethod
    def _format_size(bytes_size):
        """Format bytes to human-readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"

    def show_summary(self):
        """Display purge summary"""
        print()
        print("=" * 80)
        print(f"📊 PURGE SUMMARY")
        print("=" * 80)
        print()

        if self.dry_run:
            print(f"{YELLOW}[DRY-RUN MODE]{RESET}")
            print("The above items WOULD be deleted but were NOT actually deleted.")
        else:
            if self.deleted_items:
                print(f"{GREEN}Successfully deleted:{RESET}")
                for path, size in self.deleted_items:
                    print(f"  ✓ {path} ({self._format_size(size)})")
                print()

        print(f"Total size reclaimed: {self._format_size(self.total_size)}")
        print()

        if self.verify_protection():
            print(f"{GREEN}✅ All protected paths verified safe{RESET}")
        else:
            print(f"{RED}❌ Some protected paths are missing! Please verify.{RESET}")

        print()

    def run(self):
        """Execute purge protocol"""
        print()
        print("=" * 80)
        print(f"{CYAN}🚨 ENVIRONMENT PURGE PROTOCOL{RESET}")
        print(f"{CYAN}Task #024.01: Safe Runtime Reset{RESET}")
        print("=" * 80)
        print()

        print("This will DELETE:")
        for path in self.EPHEMERAL_PATHS:
            print(f"  ✓ {path:<30} (ephemeral data)")

        if self.full:
            print(f"  ✓ Docker named volumes        (named volumes)")

        print()
        print("This will NOT delete:")
        protected_list = sorted(self.PROTECTED_PATHS)
        for path in protected_list[:10]:  # Show first 10
            print(f"  ✓ {path:<30} (PROTECTED)")
        if len(protected_list) > 10:
            print(f"  ... and {len(protected_list)-10} more protected paths")

        print()

        if self.dry_run:
            print(f"{YELLOW}[DRY-RUN MODE] - Nothing will be deleted{RESET}")
            print()

        if not self.confirm():
            return 1

        # Execute purge
        print()
        if self.verbose:
            self.log("Starting purge protocol...")

        self.stop_services()
        self.purge_logs()
        self.purge_cache()
        self.cleanup_docker_volumes()

        # Show summary
        self.show_summary()

        return 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Environment Safe Purge Protocol - Reset runtime state safely"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help="Also delete Docker named volumes (more destructive)"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Verbose output"
    )
    parser.add_argument(
        '--root',
        type=str,
        default=None,
        help="Project root directory"
    )

    args = parser.parse_args()

    purge = SafePurge(
        project_root=args.root,
        dry_run=args.dry_run,
        force=args.force,
        full=args.full,
        verbose=args.verbose
    )

    return purge.run()


if __name__ == "__main__":
    sys.exit(main())

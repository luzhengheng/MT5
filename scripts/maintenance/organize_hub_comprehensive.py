#!/usr/bin/env python3
"""
Comprehensive HUB Organization Tool

Extended version with additional file pattern support for:
- Documentation files (*.md excluding README.md)
- Temporary scripts (*.py in root)
- Output directories (outputs/, exports/, logs/, data/, data_lake/, plans/)
- Archive directories (_archive_*)
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Tuple


class ComprehensiveOrganizer:
    """Extended file organizer for MT5-CRS HUB."""

    # Core directories to keep in root
    CORE_DIRS = {
        "src", "scripts", "config", "docs", "tests",
        "alembic", "etc", "examples", "models"
    }

    # Core files to keep in root
    CORE_FILES = {
        "requirements.txt", "README.md", ".gitignore",
        "docker-compose.yml", "docker-compose.prod.yml",
        "Dockerfile.api", "Dockerfile.serving", "Dockerfile.strategy",
        "pyproject.toml", "alembic.ini", "pytest.ini",
        ".git", "gemini_review_bridge.py", "QUICK_START.md"
    }

    # Directories to archive (preserve structure)
    ARCHIVE_DIRS = ("outputs", "exports", "logs", "data", "data_lake", "plans",
                    "_archive_*", "_backup_*")

    # File patterns to archive
    ARCHIVE_PATTERNS = (
        # Documentation
        "*_RULES.md", "*_PLAN.md", "*_GUIDE.md", "*_SETUP.md", "*_COMPLETE.md",
        "*_SUMMARY.txt", "*_REPORT.txt", "FINAL_*.txt", "CLAUDE_*.txt",
        "*_REMEDIATION.md", "*_UPDATE.md", "*_PROTOCOL.md",
        # Scripts
        "*_startup.py", "*cleanup*.py", "*check*.py", "*create*.py",
        "*export*.py", "*nexus*.py", "update_*.py",
        "*.sh"
    )

    # Files to delete
    DELETE_PATTERNS = ("__pycache__", ".DS_Store", "*.pyc", "Thumbs.db", "*.tmp")

    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.manifest: List[Dict] = []
        self.stats = {
            "archived": 0,
            "deleted": 0,
            "kept": 0,
            "total": 0
        }

    def should_keep(self, item: Path) -> bool:
        """Check if item should be kept in root."""
        if item.name in self.CORE_FILES or item.name in self.CORE_DIRS:
            return True
        return False

    def should_archive_dir(self, dir_name: str) -> bool:
        """Check if directory should be archived."""
        for pattern in self.ARCHIVE_DIRS:
            if pattern.replace("*", "") in dir_name or dir_name == pattern.replace("*", ""):
                return True
        return False

    def should_archive_file(self, filename: str) -> bool:
        """Check if file matches archive patterns."""
        for pattern in self.ARCHIVE_PATTERNS:
            if pattern.startswith("*"):
                suffix = pattern[1:]
                if filename.endswith(suffix):
                    return True
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                if filename.startswith(prefix):
                    return True
            elif filename == pattern:
                return True
        return False

    def should_delete(self, filename: str) -> bool:
        """Check if file should be deleted."""
        for pattern in self.DELETE_PATTERNS:
            if pattern.startswith("*"):
                if filename.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                if filename.startswith(pattern[:-1]):
                    return True
            elif filename == pattern or filename.startswith(pattern):
                return True
        return False

    def process(self) -> None:
        """Process all items in root directory."""
        print(f"\nProcessing root directory: {self.project_root}\n")

        for item in sorted(self.project_root.iterdir()):
            if item.name.startswith("."):
                continue

            self.stats["total"] += 1

            # Skip if should keep
            if self.should_keep(item):
                print(f"[KEEP] {item.name}")
                self.stats["kept"] += 1
                continue

            # Handle directories
            if item.is_dir():
                if self.should_archive_dir(item.name):
                    self.archive_item(item, "directory")
                else:
                    print(f"[KEEP?] {item.name}/ (unknown directory)")
                    self.stats["kept"] += 1

            # Handle files
            else:
                if self.should_delete(item.name):
                    self.delete_item(item)
                elif self.should_archive_file(item.name):
                    self.archive_item(item, "file")
                else:
                    print(f"[KEEP?] {item.name} (unknown file)")
                    self.stats["kept"] += 1

    def archive_item(self, item: Path, item_type: str) -> None:
        """Archive an item to docs/archive/."""
        # Determine destination
        if item_type == "directory":
            dest = self.project_root / "docs" / "archive" / item.name
        else:
            dest = self.project_root / "docs" / "archive" / item.name

        if self.dry_run:
            print(f"[ARCHIVE] {item.name} -> docs/archive/{item.name}")
        else:
            # Use system command to move directory
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
            else:
                shutil.move(str(item), str(dest))
            print(f"[ARCHIVED] {item.name}")

        # Record in manifest
        self.manifest.append({
            "name": item.name,
            "type": item_type,
            "original": str(item.relative_to(self.project_root)),
            "archive": f"docs/archive/{item.name}",
            "operation": "archive",
            "timestamp": datetime.now().isoformat()
        })

        self.stats["archived"] += 1

    def delete_item(self, item: Path) -> None:
        """Delete an item."""
        if self.dry_run:
            print(f"[DELETE] {item.name}")
        else:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            print(f"[DELETED] {item.name}")

        self.manifest.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "operation": "delete",
            "timestamp": datetime.now().isoformat()
        })

        self.stats["deleted"] += 1

    def save_manifest(self) -> Path:
        """Save manifest."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_path = (self.project_root / "docs" / "archive" /
                        f"manifest_comprehensive_{timestamp}.json")

        if not self.dry_run:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": timestamp,
                    "operation": "comprehensive_archive",
                    "dry_run": self.dry_run,
                    "statistics": self.stats,
                    "files": self.manifest
                }, f, indent=2, ensure_ascii=False)
            print(f"\n[MANIFEST] {manifest_path.relative_to(self.project_root)}")

        return manifest_path

    def print_summary(self) -> None:
        """Print summary."""
        print("\n" + "="*60)
        print("COMPREHENSIVE ARCHIVE SUMMARY")
        print("="*60)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        print(f"\n  Items archived:    {self.stats['archived']}")
        print(f"  Items deleted:     {self.stats['deleted']}")
        print(f"  Items kept:        {self.stats['kept']}")
        print(f"  ─────────────────────────")
        print(f"  Total processed:   {self.stats['total']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive HUB organization tool"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute operations (default: dry-run)"
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("/opt/mt5-crs"),
        help="Project root directory"
    )

    args = parser.parse_args()

    organizer = ComprehensiveOrganizer(
        args.project_root,
        dry_run=not args.execute
    )

    print("\n" + "="*60)
    print("COMPREHENSIVE HUB ORGANIZER")
    print("="*60)

    organizer.process()
    organizer.save_manifest()
    organizer.print_summary()

    if organizer.dry_run:
        print("\n[INFO] Dry run. Use --execute to apply changes.")

    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
MT5-CRS HUB Organization Tool (Protocol v3.4 Compliant)

This script archives scattered files in the project root to maintain a clean
"code repository + documentation center" structure.

Usage:
    python3 scripts/maintenance/organize_hub_v3.4.py --dry-run    # Preview changes
    python3 scripts/maintenance/organize_hub_v3.4.py --execute    # Perform archival
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Tuple


class FileOrganizer:
    """Intelligent file organizer for MT5-CRS HUB."""

    # Archive Constitution - Tier Definitions
    TIER_1_KEEP = {
        "src", "scripts", "config", "docs", "tests",
        "requirements.txt", "README.md", ".gitignore",
        "docker-compose.yml", "pyproject.toml", ".git"
    }

    # Patterns for different tiers
    TIER_2_REPORTS = ("_REPORT.md", "_SUMMARY.md", "_REVIEW.md",
                      "core_files.md", "documents.md", "git_history.md", "project_structure.md")

    TIER_3_PROMPTS = ("AI_PROMPT_", "CONTEXT_", "PROMPT_")

    TIER_4_LOGS = (".log",)

    TIER_5_CLEAN = ("__pycache__", ".DS_Store", ".pyc", "Thumbs.db")

    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.manifest: List[Dict] = []
        self.stats = {
            "tier_2": 0,
            "tier_3": 0,
            "tier_4": 0,
            "tier_5": 0,
            "total": 0
        }

    def compute_sha256(self, filepath: Path) -> str:
        """Compute SHA256 hash of a file."""
        hash_sha256 = sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            return f"ERROR: {e}"

    def classify_file(self, filepath: Path) -> Tuple[str, Path]:
        """
        Classify a file and return (tier, destination_path).

        Returns:
            (tier, destination): Tier identifier and target path
        """
        name = filepath.name

        # Tier 5: Clean (delete)
        if name in self.TIER_5_CLEAN or filepath.name.startswith("__pycache__"):
            return "tier_5", None

        # Tier 2: Reports
        if name.endswith(self.TIER_2_REPORTS) or name in self.TIER_2_REPORTS:
            dest = self.project_root / "docs" / "archive" / "reports" / name
            return "tier_2", dest

        # Tier 3: Prompts (organize by year/month)
        if name.startswith(self.TIER_3_PROMPTS):
            # Extract date from filename (format: PREFIX_YYYYMMDD_*)
            parts = name.split("_")
            if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) >= 6:
                year_month = parts[1][:6]  # YYYYMM
                dest = (self.project_root / "docs" / "archive" / "prompts" /
                       year_month / name)
            else:
                # Default to current month if no date in filename
                current_ym = datetime.now().strftime("%Y%m")
                dest = (self.project_root / "docs" / "archive" / "prompts" /
                       current_ym / name)
            return "tier_3", dest

        # Tier 4: Logs
        if name.endswith(self.TIER_4_LOGS):
            dest = self.project_root / "docs" / "archive" / "logs" / name
            return "tier_4", dest

        # Unknown: Keep in place
        return "unknown", None

    def scan_root(self) -> List[Tuple[Path, str, Path]]:
        """
        Scan project root and return list of (filepath, tier, destination).

        Returns:
            List of tuples: (file_path, tier, destination_path)
        """
        actions = []

        for item in self.project_root.iterdir():
            # Skip Tier 1 keep directories/files
            if item.name in self.TIER_1_KEEP:
                continue

            # Skip directories that are Tier 1
            if item.is_dir() and item.name in self.TIER_1_KEEP:
                continue

            # Skip .git directory
            if item.name.startswith(".git"):
                continue

            # Handle files
            if item.is_file():
                tier, dest = self.classify_file(item)
                if tier != "unknown" and dest is not None:
                    actions.append((item, tier, dest))
                elif tier == "tier_5":
                    actions.append((item, tier, None))

            # Handle directories (e.g., __pycache__)
            if item.is_dir():
                tier, _ = self.classify_file(item)
                if tier == "tier_5":
                    actions.append((item, tier, None))

        return actions

    def execute_actions(self, actions: List[Tuple[Path, str, Path]]) -> None:
        """Execute file operations (move/delete)."""

        for src, tier, dest in actions:
            try:
                # Compute hash before moving
                file_hash = self.compute_sha256(src) if src.is_file() else "N/A"

                if tier == "tier_5":
                    # Delete
                    if self.dry_run:
                        print(f"[DELETE] {src.name}")
                    else:
                        if src.is_dir():
                            shutil.rmtree(src)
                        else:
                            src.unlink()
                        print(f"[DELETED] {src.name}")

                else:
                    # Move
                    if self.dry_run:
                        print(f"[MOVE] {src.name} -> {dest.relative_to(self.project_root)}")
                    else:
                        # Create parent directory
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src), str(dest))
                        print(f"[MOVED] {src.name} -> {dest.relative_to(self.project_root)}")

                    # Record in manifest
                    self.manifest.append({
                        "name": src.name,
                        "original": str(src.relative_to(self.project_root)),
                        "archive": str(dest.relative_to(self.project_root)) if dest else None,
                        "sha256": file_hash,
                        "operation": "delete" if tier == "tier_5" else "move",
                        "timestamp": datetime.now().isoformat()
                    })

                    # Update stats
                    self.stats[tier] += 1
                    self.stats["total"] += 1

            except Exception as e:
                print(f"[ERROR] Failed to process {src.name}: {e}")

    def save_manifest(self) -> Path:
        """Save manifest to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_path = (self.project_root / "docs" / "archive" /
                        f"manifest_{timestamp}.json")

        manifest_data = {
            "timestamp": timestamp,
            "operation": "archive",
            "dry_run": self.dry_run,
            "statistics": self.stats,
            "files": self.manifest
        }

        if not self.dry_run:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            print(f"\n[MANIFEST] Saved to {manifest_path.relative_to(self.project_root)}")
        else:
            print(f"\n[DRY RUN] Would save manifest to {manifest_path.relative_to(self.project_root)}")

        return manifest_path

    def print_summary(self) -> None:
        """Print operation summary."""
        print("\n" + "="*60)
        print("OPERATION SUMMARY")
        print("="*60)
        print(f"Mode: {'DRY RUN (no changes made)' if self.dry_run else 'EXECUTE'}")
        print(f"\nStatistics:")
        print(f"  Reports archived:     {self.stats['tier_2']}")
        print(f"  Prompts archived:     {self.stats['tier_3']}")
        print(f"  Logs archived:        {self.stats['tier_4']}")
        print(f"  Cleanup items:        {self.stats['tier_5']}")
        print(f"  ─────────────────────────")
        print(f"  Total operations:     {self.stats['total']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Organize MT5-CRS HUB per Protocol v3.4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes (recommended first step)
  python3 scripts/maintenance/organize_hub_v3.4.py --dry-run

  # Execute archival
  python3 scripts/maintenance/organize_hub_v3.4.py --execute
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without executing (default: True)"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform file operations"
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("/opt/mt5-crs"),
        help="Project root directory (default: /opt/mt5-crs)"
    )

    args = parser.parse_args()

    # Check project root exists
    if not args.project_root.exists():
        print(f"[ERROR] Project root not found: {args.project_root}")
        return 1

    # Initialize organizer
    # Default is dry-run, unless --execute is specified
    dry_run = not args.execute
    organizer = FileOrganizer(args.project_root, dry_run=dry_run)

    print(f"\n{'='*60}")
    print(f"MT5-CRS HUB ORGANIZER (Protocol v3.4)")
    print(f"{'='*60}")
    print(f"Project Root: {args.project_root}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"{'='*60}\n")

    # Scan and classify
    print("[STEP 1] Scanning project root...")
    actions = organizer.scan_root()

    if not actions:
        print("\n[INFO] No files need archiving. HUB is already clean!")
        return 0

    print(f"[INFO] Found {len(actions)} items to process\n")

    # Execute actions
    print("[STEP 2] Executing file operations...")
    organizer.execute_actions(actions)

    # Save manifest
    print("\n[STEP 3] Saving manifest...")
    organizer.save_manifest()

    # Print summary
    organizer.print_summary()

    if dry_run:
        print("\n[INFO] Dry run complete. Use --execute to perform actual archival.")

    return 0


if __name__ == "__main__":
    exit(main())

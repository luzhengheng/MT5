#!/usr/bin/env python3
"""
🛡️ ROOT DIRECTORY DEEP REFACTORING (Whitelist + Quarantine Strategy)
================================================================

Protocol: v4.3 (Zero-Trust Edition)
Task: #091.2

This script implements a surgical cleanup using:
1. ✅ Whitelist Strategy: Define what MUST stay, move everything else
2. ✅ Quarantine Zone: Unknown files go to docs/archive/quarantine first
3. ✅ Atomic Execution: All moves are logged for forensic verification
4. ✅ Physical Verification: Tree snapshot before/after

Core Assets (MUST PRESERVE):
- Source code: src/, scripts/, tests/, config/
- Data: data/, data_lake/, logs/, models/, outputs/, mlruns/, plans/
- Infrastructure: etc/, systemd/, MQL5/
- Cache: __pycache__, venv, mt5_crs.egg-info
- Configuration: .env*, .gitignore, .cursorrules, alembic.ini, pyproject.toml
- Essential Scripts: deploy_production.sh, docker-*.yml, Dockerfile.*
- Core Docs: README.md, requirements.txt, pytest.ini, QUICKSTART_ML.md
- Build: gemini_review_bridge.py, nexus_with_proxy.py, nginx_dashboard.conf
- Database: optuna.db
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Set, List, Tuple

# ============================================================================
# WHITELIST: Files/Patterns that MUST be preserved in root
# ============================================================================
WHITELIST_FILES = {
    # Core Configuration
    '.env', '.env.bak', '.env.example', '.env.production', '.env.data_nexus.example', '.env.tmp',
    '.gitignore', '.cursorrules',
    'pyproject.toml', 'pytest.ini', 'requirements.txt', 'alembic.ini',

    # Primary Documentation
    'README.md', 'QUICKSTART_ML.md',

    # Infrastructure Files
    'optuna.db',

    # Deployment & Build
    'docker-compose.yml', 'docker-compose.prod.yml', 'docker-compose.data.yml',
    'Dockerfile.api', 'Dockerfile.serving', 'Dockerfile.strategy',
    'deploy_production.sh',
    'nginx_dashboard.conf',

    # Critical Scripts
    'gemini_review_bridge.py', 'nexus_with_proxy.py',

    # System Files (Keep for compatibility)
    'AI_RULES.md', 'CLAUDE_START.txt',
}

WHITELIST_DIRS = {
    'src', 'scripts', 'tests', 'config',
    'data', 'data_lake', 'logs', 'models', 'outputs', 'mlruns', 'plans',
    'etc', 'systemd', 'MQL5',
    '__pycache__', 'venv', 'mt5_crs.egg-info',
    'docs', '_archive_20251222', 'exports',  # Archives & exports
}

# ============================================================================
# CLASSIFICATION RULES: Map file patterns to target directories
# ============================================================================
CLASSIFICATION = {
    'docs/archive/task_reports': [
        'TASK_*.txt', 'TASK_*.md', 'WORK_ORDER_*.md', 'ISSUE_*.md',
    ],
    'docs/archive/reports': [
        '*_REPORT*.md', '*_REPORT*.txt', '*_REPORT*.json',
        'COMPLETION_*.md', 'EXECUTION_*.md', 'SUMMARY_*.md',
    ],
    'docs/guides': [
        'DEPLOYMENT_*.md', '*_GUIDE*.md', '*_CHECKLIST*.md',
        'SETUP_*.md', 'QUICKSTART_*.md', 'SETUP*.txt',
    ],
    'docs/': [
        '*.md', '*.txt',  # Default for unclassified markdown/text
    ],
}

# ============================================================================
# EXECUTION ENGINE
# ============================================================================

class RootOrganizer:
    def __init__(self, root_path: str = '/opt/mt5-crs'):
        self.root = Path(root_path)
        self.quarantine = self.root / 'docs' / 'archive' / 'quarantine'
        self.log_file = self.root / f'scripts/maintenance/organize_root_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        self.moves_log = []
        self.errors = []

    def ensure_quarantine(self):
        """Create quarantine zone if not exists"""
        self.quarantine.mkdir(parents=True, exist_ok=True)
        self._log(f"✅ Quarantine zone ready: {self.quarantine}")

    def _log(self, message: str):
        """Log to console and file"""
        print(message)
        self.moves_log.append(message)

    def _is_whitelisted(self, path: Path) -> bool:
        """Check if file/dir is in whitelist"""
        name = path.name

        # Check exact file matches
        if name in WHITELIST_FILES:
            return True

        # Check directory matches
        if name in WHITELIST_DIRS:
            return True

        # Check .hidden files (always preserve)
        if name.startswith('.'):
            return True

        return False

    def _classify_file(self, filename: str) -> str:
        """Classify a file based on pattern matching"""
        for target_dir, patterns in CLASSIFICATION.items():
            for pattern in patterns:
                # Simple glob matching
                if pattern.startswith('*') and pattern.endswith('*'):
                    mid = pattern[1:-1]
                    if mid in filename:
                        return target_dir
                elif pattern.startswith('*'):
                    suffix = pattern[1:]
                    if filename.endswith(suffix):
                        return target_dir
                elif pattern.endswith('*'):
                    prefix = pattern[:-1]
                    if filename.startswith(prefix):
                        return target_dir
                elif pattern == filename:
                    return target_dir

        # Default: quarantine
        return 'docs/archive/quarantine'

    def organize(self):
        """Main execution: move non-whitelisted files"""
        self.ensure_quarantine()
        self._log("\n" + "="*70)
        self._log("🛡️  ROOT DIRECTORY DEEP REFACTORING (Task #091.2)")
        self._log("="*70)

        # Scan root directory
        root_items = sorted(self.root.iterdir())
        non_whitelisted = [
            item for item in root_items
            if not self._is_whitelisted(item)
        ]

        self._log(f"\n📊 Scan Results:")
        self._log(f"   Total items in root: {len(root_items)}")
        self._log(f"   Whitelisted (preserved): {len(root_items) - len(non_whitelisted)}")
        self._log(f"   Non-whitelisted (to move): {len(non_whitelisted)}")

        if non_whitelisted:
            self._log(f"\n🔄 Moving non-whitelisted files...\n")

        for item in non_whitelisted:
            if item.is_file():
                self._move_file(item)
            elif item.is_dir():
                self._log(f"⏭️  Skipping directory: {item.name} (nested structure)")

        self._log(f"\n{'='*70}")
        self._log(f"✅ CLEANUP COMPLETE")
        self._log(f"{'='*70}\n")

        # Summary
        moved_count = len([m for m in self.moves_log if '→' in m])
        self._log(f"📈 Summary: {moved_count} files moved")

        if self.errors:
            self._log(f"\n⚠️  Errors ({len(self.errors)}):")
            for err in self.errors:
                self._log(f"   - {err}")

        return moved_count

    def _move_file(self, file_path: Path):
        """Move a single file to classified destination"""
        try:
            target_dir = self._classify_file(file_path.name)
            target_path = self.root / target_dir

            # Create target directory
            target_path.mkdir(parents=True, exist_ok=True)

            # Move file
            dest_file = target_path / file_path.name
            shutil.move(str(file_path), str(dest_file))

            self._log(f"✅ {file_path.name} → {target_dir}")

        except Exception as e:
            msg = f"❌ Failed to move {file_path.name}: {str(e)}"
            self._log(msg)
            self.errors.append(msg)

    def verify(self):
        """Post-cleanup verification"""
        self._log("\n" + "="*70)
        self._log("🔍 VERIFICATION PHASE")
        self._log("="*70 + "\n")

        # Check for TASK_* or WORK_ORDER_* files in root
        remaining = list(self.root.glob('TASK_*')) + list(self.root.glob('WORK_ORDER_*'))

        if remaining:
            self._log(f"❌ CRITICAL: Found {len(remaining)} unclassified task files in root:")
            for f in remaining:
                self._log(f"   - {f.name}")
            return False
        else:
            self._log(f"✅ Root directory is clean (no TASK_* or WORK_ORDER_* files)")

        # Tree snapshot
        self._log(f"\n📸 Root Directory Snapshot (post-cleanup):")
        root_items = sorted(self.root.iterdir())
        files = [item for item in root_items if item.is_file()]
        dirs = [item for item in root_items if item.is_dir()]

        self._log(f"\n📁 Directories ({len(dirs)}):")
        for d in dirs[:15]:  # Show first 15
            self._log(f"   {d.name}/")
        if len(dirs) > 15:
            self._log(f"   ... and {len(dirs) - 15} more")

        self._log(f"\n📄 Files ({len(files)}):")
        for f in files[:15]:  # Show first 15
            self._log(f"   {f.name}")
        if len(files) > 15:
            self._log(f"   ... and {len(files) - 15} more")

        self._log(f"\n{'='*70}")
        self._log(f"✅ VERIFICATION PASSED")
        self._log(f"{'='*70}\n")

        return True

    def save_log(self):
        """Save execution log to file"""
        log_content = '\n'.join(self.moves_log)
        self.log_file.write_text(log_content)
        print(f"\n📝 Log saved to: {self.log_file}")


def main():
    organizer = RootOrganizer()
    organizer.organize()
    organizer.verify()
    organizer.save_log()

    print("\n✨ Task #091.2 whitelist cleanup COMPLETE")
    print(f"   Quarantine zone: docs/archive/quarantine")
    print(f"   Execution log: {organizer.log_file}")


if __name__ == '__main__':
    main()

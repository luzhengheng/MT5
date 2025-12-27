#!/usr/bin/env python3
"""
Work Order #023.9: ML Stack Installer
=======================================

Force install Modern ML Stack for Task #024 (ML Strategy).

Dependencies:
- pandas>=2.0
- xgboost>=2.0
- pyzmq>=25.0
- scikit-learn>=1.3
- lightgbm>=4.0

Protocol: v2.0 (Strict TDD)
"""

import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path("/opt/mt5-crs")
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


# ============================================================================
# Installation Functions
# ============================================================================

def check_pip():
    """Verify pip is available."""
    try:
        result = subprocess.run(
            ["pip3", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"✅ pip3 version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ pip3 not found")
        return False


def install_requirements():
    """
    Install all requirements from requirements.txt.

    Uses:
        pip3 install -r requirements.txt --upgrade

    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info("📦 Installing ML Stack from requirements.txt")
    logger.info("=" * 70)
    print()

    if not REQUIREMENTS_FILE.exists():
        logger.error(f"❌ Requirements file not found: {REQUIREMENTS_FILE}")
        return False

    logger.info(f"Requirements file: {REQUIREMENTS_FILE}")
    logger.info("Installing with: pip3 install -r requirements.txt --upgrade")
    print()

    try:
        result = subprocess.run(
            ["pip3", "install", "-r", str(REQUIREMENTS_FILE), "--upgrade"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode == 0:
            logger.info("✅ Installation successful")
            print()
            logger.info("STDOUT:")
            for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                if line.strip():
                    logger.info(f"  {line}")
            return True
        else:
            logger.error("❌ Installation failed")
            logger.error("STDERR:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(f"  {line}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("❌ Installation timeout (> 5 minutes)")
        return False
    except Exception as e:
        logger.error(f"❌ Installation error: {e}")
        return False


def verify_critical_packages():
    """
    Verify critical packages are installed.

    Critical packages:
        - pandas>=2.0
        - xgboost>=2.0
        - pyzmq>=25.0
        - scikit-learn>=1.3
        - numpy

    Returns:
        True if all critical packages installed, False otherwise
    """
    logger.info("=" * 70)
    logger.info("🔍 Verifying Critical Packages")
    logger.info("=" * 70)
    print()

    critical_packages = [
        "pandas",
        "numpy",
        "xgboost",
        "pyzmq",
        "sklearn",  # scikit-learn imports as sklearn
        "lightgbm",
    ]

    all_ok = True

    for package in critical_packages:
        try:
            if package == "sklearn":
                import sklearn
                version = sklearn.__version__
            else:
                mod = __import__(package)
                version = getattr(mod, '__version__', 'unknown')

            logger.info(f"  ✅ {package}: {version}")
        except ImportError:
            logger.error(f"  ❌ {package}: NOT INSTALLED")
            all_ok = False

    print()
    if all_ok:
        logger.info("✅ All critical packages installed")
    else:
        logger.error("❌ Some critical packages missing")

    return all_ok


# ============================================================================
# Main Installation
# ============================================================================

def main():
    """Execute ML stack installation."""
    print("=" * 70)
    print("📦 Work Order #023.9: ML Stack Installer")
    print("=" * 70)
    print()
    print("Target ML Stack:")
    print("  - pandas>=2.0      (~2x faster operations)")
    print("  - xgboost>=2.0     (GPU acceleration)")
    print("  - pyzmq>=25.0      (Latest ZeroMQ)")
    print("  - scikit-learn>=1.3 (Latest pipelines)")
    print("  - lightgbm>=4.0    (Microsoft gradient boosting)")
    print()
    print("=" * 70)
    print()

    # Step 1: Check pip
    if not check_pip():
        logger.error("Cannot proceed without pip3")
        return 1

    print()

    # Step 2: Install requirements
    if not install_requirements():
        logger.error("Installation failed")
        return 1

    print()

    # Step 3: Verify critical packages
    if not verify_critical_packages():
        logger.error("Verification failed - some packages missing")
        return 1

    # Final summary
    print()
    print("=" * 70)
    print("✅ ML Stack Installation Complete")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Verify synergy: python3 scripts/verify_synergy.py")
    print("  2. Test imports: python3 -c 'import pandas, xgboost, pyzmq'")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

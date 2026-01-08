#!/usr/bin/env python3
"""
Task #067: Initialize Feast Feature Store
Protocol: v4.3 (Zero-Trust Edition)

Initializes the Feast Feature Store with secure credential handling.
Reads credentials from environment variables and applies feature definitions.

Usage:
    python3 scripts/init_feast.py

Environment Variables:
    POSTGRES_HOST: PostgreSQL host (default: localhost)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_USER: PostgreSQL user (default: trader)
    POSTGRES_PASSWORD: PostgreSQL password (REQUIRED - must be set securely)
    POSTGRES_DB: PostgreSQL database (default: mt5_crs)
    REDIS_HOST: Redis host (default: localhost)
    REDIS_PORT: Redis port (default: 6379)
    REDIS_DB: Redis database number (default: 0)
"""

import os
import sys
from pathlib import Path
import subprocess
import tempfile
import shutil

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def load_env_file():
    """Load environment variables from .env file using dotenv-like parsing."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"{CYAN}Loading environment from {env_file}...{RESET}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"{GREEN}✅ .env file loaded{RESET}")
        except ImportError:
            # Fallback: manual parsing
            print(f"{YELLOW}⚠️  python-dotenv not installed, using manual parsing...{RESET}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())


def get_credentials():
    """Get credentials from environment with proper defaults and validation."""
    creds = {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "trader"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "mt5_crs"),
        "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
        "REDIS_PORT": os.getenv("REDIS_PORT", "6379"),
        "REDIS_DB": os.getenv("REDIS_DB", "0"),
    }

    # Check that POSTGRES_PASSWORD is set
    if not creds["POSTGRES_PASSWORD"]:
        raise ValueError(
            f"\n{RED}❌ POSTGRES_PASSWORD environment variable is not set{RESET}\n"
            f"Please set it before initializing Feast:\n"
            f"  export POSTGRES_PASSWORD='<your-password>'\n"
            f"  python3 scripts/init_feast.py\n"
        )

    return creds


def verify_credentials(creds):
    """Verify that required credentials are available."""
    print(f"\n{CYAN}Verifying credentials...{RESET}")

    for key, value in creds.items():
        if key == "POSTGRES_PASSWORD":
            print(f"{GREEN}✅{RESET} {key}: {'*' * min(len(value), 8)}")
        else:
            print(f"{GREEN}✅{RESET} {key}: {value}")


def create_temporary_config(creds, feature_repo_path):
    """Create a temporary feature_store.yaml with credentials injected."""
    template_path = feature_repo_path / "feature_store.yaml"

    with open(template_path) as f:
        config = f.read()

    # Replace placeholders with actual values
    config = config.replace("CHANGE_ME_IN_ENVIRONMENT_VARIABLES", creds["POSTGRES_PASSWORD"])
    config = config.replace("localhost", creds["POSTGRES_HOST"], 1)  # First localhost is for host
    config = config.replace(":5432", f":{creds['POSTGRES_PORT']}")
    config = config.replace("mt5_crs", creds["POSTGRES_DB"], 1)  # First occurrence
    config = config.replace("trader", creds["POSTGRES_USER"], 1)
    config = config.replace("localhost:6379", f"{creds['REDIS_HOST']}:{creds['REDIS_PORT']}")
    config = config.replace(",db=0", f",db={creds['REDIS_DB']}")

    # Create temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".yaml", prefix="feature_store_")
    os.close(temp_fd)

    with open(temp_path, "w") as f:
        f.write(config)

    return temp_path


def init_feast(creds):
    """Initialize Feast Feature Store with properly injected credentials."""
    print(f"\n{CYAN}Initializing Feast Feature Store...{RESET}")

    feature_repo_path = Path(__file__).parent.parent / "src" / "feature_repo"

    try:
        # Create a temporary config with injected credentials
        temp_config = create_temporary_config(creds, feature_repo_path)
        print(f"{GREEN}✅{RESET} Created temporary config with credentials")

        # Backup original yaml
        orig_yaml = feature_repo_path / "feature_store.yaml"
        backup_yaml = feature_repo_path / "feature_store.yaml.bak"

        if orig_yaml.exists():
            shutil.copy(orig_yaml, backup_yaml)

        try:
            # Copy temp config to feature_store.yaml
            shutil.copy(temp_config, orig_yaml)

            # Run feast apply
            print(f"{CYAN}Running: feast apply{RESET}")
            result = subprocess.run(
                ["feast", "apply"],
                cwd=feature_repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"{GREEN}✅ Feast apply completed successfully{RESET}")
                if "Deploying" in result.stdout or "Deploying" in result.stderr:
                    print(f"{GREEN}✅ Feature views registered{RESET}")
                return True
            else:
                print(f"{RED}❌ Feast apply failed:{RESET}")
                print(result.stderr)
                return False
        finally:
            # Restore original yaml (without credentials)
            if backup_yaml.exists():
                shutil.move(backup_yaml, orig_yaml)
            # Clean up temp file
            os.unlink(temp_config)

    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    print(f"{CYAN}{'=' * 80}{RESET}")
    print(f"{CYAN}Feast Feature Store Initialization (Task #067){RESET}")
    print(f"{CYAN}Protocol: v4.3 (Zero-Trust Edition){RESET}")
    print(f"{CYAN}{'=' * 80}{RESET}")
    print()

    try:
        # Load environment
        load_env_file()

        # Get and verify credentials
        creds = get_credentials()
        verify_credentials(creds)

        # Initialize Feast
        if init_feast(creds):
            print()
            print(f"{CYAN}{'=' * 80}{RESET}")
            print(f"{GREEN}✅ FEAST FEATURE STORE INITIALIZED SUCCESSFULLY{RESET}")
            print(f"{CYAN}{'=' * 80}{RESET}")
            return 0
        else:
            print()
            print(f"{CYAN}{'=' * 80}{RESET}")
            print(f"{RED}❌ FEAST FEATURE STORE INITIALIZATION FAILED{RESET}")
            print(f"{CYAN}{'=' * 80}{RESET}")
            return 1

    except ValueError as e:
        print(f"\n{RED}{e}{RESET}")
        return 1
    except Exception as e:
        print(f"{RED}❌ Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

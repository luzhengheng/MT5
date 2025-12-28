#!/usr/bin/env python3
"""
INF Node Environment Pre-flight Check

Comprehensive audit of system resources, network connectivity, and dependencies
before executing heavy workloads like Forex data ingestion (Task #034/#035).

Exit codes:
    0: All checks passed - READY FOR EXECUTION
    1: One or more checks failed - DO NOT PROCEED
"""

import shutil
import os
import sys
import socket
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class EnvironmentAudit:
    """System environment audit for data ingestion workloads."""

    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0

    def print_header(self):
        """Print audit header."""
        print("=" * 80)
        print("🔍 INF NODE ENVIRONMENT PRE-FLIGHT CHECK")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Project Root: {PROJECT_ROOT}")
        print()

    def print_check(self, component, status, message=""):
        """Print individual check result."""
        icon = "✅" if status else "❌"
        status_str = "PASS" if status else "FAIL"
        print(f"{icon} [{component:<20}] {status_str:<6} {message}")

        if status:
            self.passed += 1
        else:
            self.failed += 1

        self.results[component] = {"status": status, "message": message}

    def check_disk_space(self, path="/", min_gb=10):
        """Check available disk space."""
        try:
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (1024**3)
            used_gb = used / (1024**3)
            total_gb = total / (1024**3)

            status = free_gb >= min_gb
            msg = f"Free: {free_gb:.1f}GB / Total: {total_gb:.1f}GB (Threshold: {min_gb}GB)"
            self.print_check("Disk Space", status, msg)
            return status
        except Exception as e:
            self.print_check("Disk Space", False, f"Error: {e}")
            return False

    def check_docker_daemon(self):
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            status = result.returncode == 0
            msg = "Daemon running" if status else "Daemon not available"
            self.print_check("Docker Daemon", status, msg)
            return status
        except FileNotFoundError:
            self.print_check("Docker Daemon", False, "Docker command not found")
            return False
        except Exception as e:
            self.print_check("Docker Daemon", False, f"Error: {e}")
            return False

    def check_docker_containers(self):
        """Check if required containers are running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                self.print_check(
                    "TimescaleDB Container",
                    False,
                    "docker-compose ps failed",
                )
                self.print_check("Redis Container", False, "docker-compose ps failed")
                return False

            # Parse docker-compose output
            containers = result.stdout.strip()
            db_running = "timescaledb" in containers and "running" in containers
            redis_running = "redis" in containers and "running" in containers

            self.print_check("TimescaleDB Container", db_running, "Status: running")
            self.print_check("Redis Container", redis_running, "Status: running")

            return db_running and redis_running
        except FileNotFoundError:
            self.print_check("TimescaleDB Container", False, "docker-compose not found")
            self.print_check("Redis Container", False, "docker-compose not found")
            return False
        except Exception as e:
            self.print_check("TimescaleDB Container", False, f"Error: {e}")
            self.print_check("Redis Container", False, f"Error: {e}")
            return False

    def check_database_connectivity(self):
        """Check PostgreSQL/TimescaleDB connectivity."""
        try:
            from src.data_nexus.database.connection import PostgresConnection

            conn = PostgresConnection()
            version = conn.get_version()

            if version and "PostgreSQL" in version:
                # Extract version numbers
                self.print_check("Database Connectivity", True, f"Connected - {version[:60]}...")
                return True
            else:
                self.print_check("Database Connectivity", False, "Invalid response from database")
                return False
        except Exception as e:
            self.print_check("Database Connectivity", False, f"Connection failed: {str(e)[:60]}")
            return False

    def check_redis_connectivity(self):
        """Check Redis connectivity."""
        try:
            from src.data_nexus.cache.redis_client import RedisClient

            client = RedisClient()
            if client.ping():
                self.print_check("Redis Connectivity", True, "Connected and responsive")
                return True
            else:
                self.print_check("Redis Connectivity", False, "Ping failed")
                return False
        except Exception as e:
            self.print_check("Redis Connectivity", False, f"Connection failed: {str(e)[:60]}")
            return False

    def check_network_connectivity(self, host, port=443, timeout=5, name="Service"):
        """Check network connectivity to external service."""
        try:
            socket.create_connection((host, port), timeout=timeout)
            self.print_check(f"Network - {name}", True, f"Connected to {host}:{port}")
            return True
        except socket.timeout:
            self.print_check(f"Network - {name}", False, f"Timeout connecting to {host}:{port}")
            return False
        except OSError as e:
            self.print_check(f"Network - {name}", False, f"Failed to reach {host}:{port}")
            return False
        except Exception as e:
            self.print_check(f"Network - {name}", False, f"Error: {str(e)[:60]}")
            return False

    def check_eodhd_api(self):
        """Check EODHD API connectivity."""
        return self.check_network_connectivity("eodhd.com", 443, 5, "EODHD API")

    def check_eodhd_websocket(self):
        """Check EODHD WebSocket connectivity."""
        return self.check_network_connectivity(
            "ws.eodhistoricaldata.com", 443, 5, "EODHD WebSocket"
        )

    def check_eodhd_api_key(self):
        """Check if EODHD API key is configured."""
        api_key = os.environ.get("EODHD_API_KEY")
        if api_key and len(api_key) > 10:
            # Mask the key for security
            masked = api_key[:10] + "..." + api_key[-4:]
            self.print_check("EODHD API Key", True, f"Configured: {masked}")
            return True
        else:
            self.print_check("EODHD API Key", False, "Not set or invalid")
            return False

    def check_python_dependencies(self):
        """Check if required Python packages are installed."""
        required = {
            "aiohttp": "Async HTTP client",
            "aiodns": "Async DNS resolver",
            "click": "CLI framework",
            "sqlalchemy": "ORM",
            "psycopg2": "PostgreSQL driver",
            "redis": "Redis client",
        }

        missing = []
        for package, description in required.items():
            try:
                __import__(package)
            except ImportError:
                missing.append(f"{package} ({description})")

        status = len(missing) == 0
        if status:
            self.print_check("Python Dependencies", True, f"All {len(required)} packages installed")
        else:
            self.print_check("Python Dependencies", False, f"Missing: {', '.join(missing)}")

        return status

    def check_alembic_migrations(self):
        """Check if Alembic is configured."""
        try:
            alembic_ini = PROJECT_ROOT / "alembic.ini"
            alembic_versions = PROJECT_ROOT / "alembic" / "versions"

            if alembic_ini.exists() and alembic_versions.exists():
                migration_count = len(list(alembic_versions.glob("*.py"))) - 1  # Exclude __pycache__
                self.print_check(
                    "Alembic Migrations", True, f"Configured with {migration_count} migration(s)"
                )
                return True
            else:
                self.print_check("Alembic Migrations", False, "alembic.ini or versions directory not found")
                return False
        except Exception as e:
            self.print_check("Alembic Migrations", False, f"Error: {e}")
            return False

    def check_ingestion_code(self):
        """Check if ingestion code is present."""
        try:
            ingestion_dir = PROJECT_ROOT / "src" / "data_nexus" / "ingestion"
            discovery = ingestion_dir / "asset_discovery.py"
            loader = ingestion_dir / "history_loader.py"
            cli = PROJECT_ROOT / "bin" / "run_ingestion.py"

            all_present = discovery.exists() and loader.exists() and cli.exists()
            msg = "All components present" if all_present else "Missing components"
            self.print_check("Ingestion Code", all_present, msg)
            return all_present
        except Exception as e:
            self.print_check("Ingestion Code", False, f"Error: {e}")
            return False

    def check_file_permissions(self):
        """Check if critical files are readable."""
        try:
            files = [
                PROJECT_ROOT / "requirements.txt",
                PROJECT_ROOT / "bin" / "run_ingestion.py",
                PROJECT_ROOT / "scripts" / "verify_schema.py",
            ]

            all_readable = all(f.is_file() and os.access(f, os.R_OK) for f in files)
            msg = "All critical files readable" if all_readable else "Some files not readable"
            self.print_check("File Permissions", all_readable, msg)
            return all_readable
        except Exception as e:
            self.print_check("File Permissions", False, f"Error: {e}")
            return False

    def print_summary(self):
        """Print audit summary."""
        print()
        print("=" * 80)
        print(f"📊 AUDIT SUMMARY: {self.passed} Passed, {self.failed} Failed")
        print("=" * 80)

        if self.failed == 0:
            print()
            print("🚀 ✅ SYSTEM READY FOR TAKEOFF")
            print()
            print("All environmental checks passed. You can proceed with:")
            print("  1. Task #034 (Forex Data Ingestion)")
            print("  2. Task #035 (Feature Engineering & ML)")
            print()
            return True
        else:
            print()
            print("⚠️  ❌ SYSTEM CHECKS FAILED - DO NOT PROCEED")
            print()
            print("Issues found during audit:")
            for component, result in self.results.items():
                if not result["status"]:
                    print(f"  • {component}: {result['message']}")
            print()
            return False

    def run_all_checks(self):
        """Run all audit checks."""
        self.print_header()

        print("🔍 INFRASTRUCTURE CHECKS")
        print("-" * 80)
        self.check_disk_space(str(PROJECT_ROOT), min_gb=10)
        self.check_docker_daemon()
        self.check_docker_containers()

        print()
        print("🔍 DATABASE & CACHE CHECKS")
        print("-" * 80)
        self.check_database_connectivity()
        self.check_redis_connectivity()

        print()
        print("🔍 NETWORK CONNECTIVITY CHECKS")
        print("-" * 80)
        self.check_eodhd_api()
        self.check_eodhd_websocket()
        self.check_eodhd_api_key()

        print()
        print("🔍 SOFTWARE & CODE CHECKS")
        print("-" * 80)
        self.check_python_dependencies()
        self.check_alembic_migrations()
        self.check_ingestion_code()
        self.check_file_permissions()

        print()
        return self.print_summary()


def main():
    """Execute environment audit."""
    audit = EnvironmentAudit()
    success = audit.run_all_checks()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

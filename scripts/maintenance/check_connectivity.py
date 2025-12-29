#!/usr/bin/env python3
"""
System Integrity Audit & Connectivity Check (Task #042.2)

Multi-layer verification:
1. Configuration Validation - Check all critical env vars
2. Service Connectivity - Test Redis, Database, MT5 Gateway
3. AI Bridge Integration - Verify OpenAI adapter setup
4. Report Summary - Generate status report with recommendations
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
load_dotenv(PROJECT_ROOT / ".env")

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class SystemIntegrityAudit:
    """Multi-layer system integrity verification."""

    def __init__(self):
        """Initialize audit with environment variables."""
        self.results = {
            "env_vars": {},
            "services": {},
            "ai_bridge": {},
            "issues": []
        }
        self.critical_vars = [
            "GEMINI_API_KEY",
            "GEMINI_BASE_URL",
            "GEMINI_MODEL",
            "GEMINI_PROVIDER",
            "REDIS_HOST",
            "REDIS_PORT",
            "DB_URL",
            "POSTGRES_USER",
            "POSTGRES_DB"
        ]

    def log(self, msg, level="INFO"):
        """Print formatted log message."""
        colors = {
            "SUCCESS": GREEN,
            "ERROR": RED,
            "WARN": YELLOW,
            "INFO": CYAN,
            "HEADER": BLUE
        }
        prefix = {
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARN": "⚠️",
            "INFO": "ℹ️",
            "HEADER": "═"
        }.get(level, "•")
        color = colors.get(level, RESET)
        print(f"{color}{prefix} {msg}{RESET}")

    def section(self, title):
        """Print section header."""
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{BLUE}{title}{RESET}")
        print(f"{BLUE}{'-' * 70}{RESET}")

    # ========================================================================
    # Layer 1: Configuration Validation
    # ========================================================================

    def check_env_variables(self) -> bool:
        """Check all critical environment variables."""
        self.section("1️⃣  CRITICAL ENV VARIABLES ({}/{})".format(
            len([v for v in self.critical_vars if os.getenv(v)]),
            len(self.critical_vars)
        ))

        all_present = True

        for var in self.critical_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "KEY" in var:
                    masked = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
                elif "PASSWORD" in var:
                    masked = "***" * 3
                else:
                    masked = value
                self.log(f"{var:25s}: {masked}", "SUCCESS")
                self.results["env_vars"][var] = "PRESENT"
            else:
                self.log(f"{var:25s}: MISSING", "ERROR")
                self.results["env_vars"][var] = "MISSING"
                self.results["issues"].append(f"Missing critical var: {var}")
                all_present = False

        return all_present

    # ========================================================================
    # Layer 2: Service Connectivity
    # ========================================================================

    def check_redis(self) -> bool:
        """Test Redis connectivity."""
        self.section("2️⃣  SERVICE CONNECTIVITY")
        print(f"\n{CYAN}Redis Status:{RESET}")

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))

        try:
            import redis
            r = redis.Redis(
                host=host,
                port=port,
                socket_connect_timeout=3,
                decode_responses=True
            )
            r.ping()
            self.log(f"Redis Connection: {host}:{port} - PING successful", "SUCCESS")
            self.results["services"]["redis"] = "CONNECTED"
            return True
        except ImportError:
            self.log("redis library not installed (optional)", "WARN")
            self.results["services"]["redis"] = "NOT_INSTALLED"
            return True  # Not critical
        except Exception as e:
            self.log(f"Redis Connection FAILED: {e}", "WARN")
            self.log(f"  Hint: Check if Redis is running at {host}:{port}", "INFO")
            self.results["services"]["redis"] = "FAILED"
            self.results["issues"].append(f"Redis connection failed: {e}")
            return False

    def check_database(self) -> bool:
        """Test Database connectivity."""
        print(f"\n{CYAN}Database Status:{RESET}")

        db_url = os.getenv("DB_URL")
        if not db_url:
            self.log("DB_URL not configured", "ERROR")
            self.results["services"]["database"] = "NOT_CONFIGURED"
            self.results["issues"].append("DB_URL missing")
            return False

        try:
            from sqlalchemy import create_engine, text

            # Mask the URL for logging
            masked_url = db_url.replace(os.getenv("POSTGRES_PASSWORD", ""), "****")
            self.log(f"Database URL: {masked_url}", "INFO")

            engine = create_engine(
                db_url,
                connect_args={"connect_timeout": 3},
                pool_pre_ping=True
            )

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            self.log("Database Connection: PING successful", "SUCCESS")
            self.results["services"]["database"] = "CONNECTED"

            # Check tables
            self._check_database_tables(engine)

            return True

        except ImportError:
            self.log("SQLAlchemy not installed", "ERROR")
            self.results["services"]["database"] = "NOT_INSTALLED"
            return False
        except Exception as e:
            self.log(f"Database Connection FAILED: {e}", "ERROR")
            self.log(f"  Hint: Check if PostgreSQL is running and credentials are correct", "INFO")
            self.results["services"]["database"] = "FAILED"
            self.results["issues"].append(f"Database connection failed: {e}")
            return False

    def _check_database_tables(self, engine):
        """Check if critical tables exist."""
        try:
            from sqlalchemy import text, inspect

            inspector = inspect(engine)
            tables = inspector.get_table_names()

            print(f"\n{CYAN}Database Tables:{RESET}")
            critical_tables = ["market_data", "assets"]
            for table in critical_tables:
                if table in tables:
                    self.log(f"  Table '{table}': EXISTS", "SUCCESS")
                else:
                    self.log(f"  Table '{table}': MISSING (will be created on first run)", "WARN")

        except Exception as e:
            self.log(f"Could not inspect tables: {e}", "WARN")

    def check_mt5_gateway(self) -> bool:
        """Check MT5 Gateway configuration."""
        print(f"\n{CYAN}MT5 Gateway Status:{RESET}")

        mt5_url = os.getenv("MT5_HTTP_URL")
        if mt5_url:
            self.log(f"MT5_HTTP_URL: {mt5_url}", "SUCCESS")
            self.results["services"]["mt5_gateway"] = "CONFIGURED"
            return True
        else:
            self.log("MT5_HTTP_URL: NOT CONFIGURED", "WARN")
            self.log("  Hint: MT5 integration requires MT5_HTTP_URL in .env", "INFO")
            self.log("  Typical values:", "INFO")
            self.log("    - Docker on Linux: 172.19.0.1:8000", "INFO")
            self.log("    - Docker on Mac: host.docker.internal:8000", "INFO")
            self.log("    - Native: 127.0.0.1:8000", "INFO")
            self.results["services"]["mt5_gateway"] = "NOT_CONFIGURED"
            return False  # Not critical but warn

    # ========================================================================
    # Layer 3: AI Bridge Integration
    # ========================================================================

    def check_ai_bridge(self) -> bool:
        """Verify AI bridge integration."""
        self.section("3️⃣  AI BRIDGE INTEGRATION")

        try:
            from scripts.utils.openai_audit_adapter import OpenAIAuditAdapter

            adapter = OpenAIAuditAdapter()

            # Check configuration
            print(f"\n{CYAN}Configuration:{RESET}")
            if adapter.api_key:
                masked = adapter.api_key[:10] + "..." + adapter.api_key[-5:]
                self.log(f"API Key: {masked}", "SUCCESS")
            else:
                self.log("API Key: MISSING", "ERROR")
                self.results["ai_bridge"]["api_key"] = "MISSING"
                return False

            if adapter.base_url:
                self.log(f"Base URL: {adapter.base_url}", "SUCCESS")
            else:
                self.log("Base URL: MISSING", "ERROR")
                self.results["ai_bridge"]["base_url"] = "MISSING"
                return False

            if adapter.model:
                self.log(f"Model: {adapter.model}", "SUCCESS")
            else:
                self.log("Model: MISSING", "ERROR")
                self.results["ai_bridge"]["model"] = "MISSING"
                return False

            if adapter.provider == "openai":
                self.log(f"Provider: {adapter.provider} ✓", "SUCCESS")
            else:
                self.log(f"Provider: {adapter.provider} (expected 'openai')", "WARN")

            # Check if configured
            print(f"\n{CYAN}Status:{RESET}")
            if adapter.is_configured():
                self.log("OpenAI Adapter: CONFIGURED AND READY", "SUCCESS")
                self.results["ai_bridge"]["status"] = "READY"
                return True
            else:
                self.log("OpenAI Adapter: NOT PROPERLY CONFIGURED", "ERROR")
                self.results["ai_bridge"]["status"] = "NOT_READY"
                self.results["issues"].append("AI bridge not properly configured")
                return False

        except ImportError as e:
            self.log(f"Cannot import AI adapter: {e}", "ERROR")
            self.results["ai_bridge"]["status"] = "IMPORT_FAILED"
            return False
        except Exception as e:
            self.log(f"AI bridge check failed: {e}", "ERROR")
            self.results["ai_bridge"]["status"] = "CHECK_FAILED"
            return False

    # ========================================================================
    # Summary Report
    # ========================================================================

    def print_summary(self):
        """Print audit summary report."""
        self.section("📊 OVERALL SYSTEM STATUS")

        # Count results
        total_vars = len(self.critical_vars)
        present_vars = len([v for v in self.critical_vars if os.getenv(v)])

        print(f"\n{CYAN}Configuration:{RESET}")
        self.log(f"Critical Variables: {present_vars}/{total_vars} ({100 * present_vars // total_vars}%)",
                 "SUCCESS" if present_vars == total_vars else "WARN")

        print(f"\n{CYAN}Services:{RESET}")
        db_status = self.results["services"].get("database", "UNKNOWN")
        redis_status = self.results["services"].get("redis", "UNKNOWN")

        db_level = "SUCCESS" if db_status == "CONNECTED" else "WARN"
        redis_level = "SUCCESS" if redis_status == "CONNECTED" else "WARN"

        self.log(f"Database: {db_status}", db_level)
        self.log(f"Redis: {redis_status}", redis_level)

        print(f"\n{CYAN}AI Integration:{RESET}")
        ai_status = self.results["ai_bridge"].get("status", "UNKNOWN")
        ai_level = "SUCCESS" if ai_status == "READY" else "ERROR"
        self.log(f"OpenAI Adapter: {ai_status}", ai_level)

        # Issues report
        if self.results["issues"]:
            print(f"\n{CYAN}Issues Found:{RESET}")
            for issue in self.results["issues"]:
                self.log(issue, "WARN")
        else:
            print(f"\n{GREEN}No critical issues found!{RESET}")

        # Verdict
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        if present_vars == total_vars and db_status == "CONNECTED" and ai_status == "READY":
            print(f"{GREEN}🎯 VERDICT: SYSTEM HEALTHY & READY{RESET}")
        elif present_vars >= 8 and ai_status == "READY":
            print(f"{YELLOW}🎯 VERDICT: SYSTEM OPERATIONAL (minor config needed){RESET}")
        else:
            print(f"{RED}🎯 VERDICT: SYSTEM NEEDS ATTENTION{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}")

    def run_audit(self) -> bool:
        """Execute full system audit."""
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{BLUE}🛡️  SYSTEM INTEGRITY AUDIT (Task #042.2){RESET}")
        print(f"{BLUE}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}")

        # Layer 1: Configuration
        config_ok = self.check_env_variables()

        # Layer 2: Services
        db_ok = self.check_database()
        redis_ok = self.check_redis()
        mt5_ok = self.check_mt5_gateway()

        # Layer 3: AI Bridge
        ai_ok = self.check_ai_bridge()

        # Summary
        self.print_summary()

        # Return overall status
        return config_ok and db_ok and ai_ok


def main():
    """Execute system integrity audit."""
    audit = SystemIntegrityAudit()
    success = audit.run_audit()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

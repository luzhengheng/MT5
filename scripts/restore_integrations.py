#!/usr/bin/env python3
"""
Integration Restoration & Validation Script (Task #042.3)

Multi-layer verification:
1. Configuration Validation - Check all integration env vars
2. Notion Connectivity - Test Notion API access
3. AI Bridge Verification - Verify OpenAI adapter ready
4. Summary Report - Generate restoration status

Usage:
    python3 scripts/restore_integrations.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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


class IntegrationRestoration:
    """Multi-layer integration restoration verification."""

    def __init__(self):
        """Initialize restoration with environment variables."""
        self.results = {
            "env_vars": {},
            "notion": {},
            "ai_bridge": {},
            "issues": []
        }
        self.critical_vars = [
            "NOTION_TOKEN",
            "NOTION_DB_ID",
            "NOTION_KNOWLEDGE_DB_ID",
            "NOTION_ISSUES_DB_ID",
            "GEMINI_API_KEY",
            "GEMINI_BASE_URL",
            "GEMINI_MODEL",
            "GEMINI_PROVIDER",
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
    # Layer 1: Integration Configuration Validation
    # ========================================================================

    def check_integration_variables(self) -> bool:
        """Check all critical integration environment variables."""
        self.section("1️⃣  INTEGRATION VARIABLES ({}/{})".format(
            len([v for v in self.critical_vars if os.getenv(v)]),
            len(self.critical_vars)
        ))

        all_present = True

        for var in self.critical_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "TOKEN" in var or "KEY" in var:
                    masked = value[:10] + "...{:0>4}".format(value[-4:]) if len(value) > 15 else "***"
                else:
                    masked = value
                self.log(f"{var:30s}: {masked}", "SUCCESS")
                self.results["env_vars"][var] = "PRESENT"
            else:
                self.log(f"{var:30s}: MISSING", "ERROR")
                self.results["env_vars"][var] = "MISSING"
                self.results["issues"].append(f"Missing integration var: {var}")
                all_present = False

        return all_present

    # ========================================================================
    # Layer 2: Notion Integration Validation
    # ========================================================================

    def check_notion_connectivity(self) -> bool:
        """Test Notion API connectivity."""
        self.section("2️⃣  NOTION INTEGRATION STATUS")

        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            self.log("NOTION_TOKEN: NOT CONFIGURED", "ERROR")
            self.results["issues"].append("Notion token missing")
            return False

        try:
            import requests

            headers = {
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": "2022-06-28"
            }

            # Test with a simple API call (search for databases)
            response = requests.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json={"filter": {"value": "database", "property": "object"}},
                timeout=5
            )

            if response.status_code == 200:
                self.log("Notion Connection: AUTHORIZED", "SUCCESS")
                databases = response.json().get("results", [])
                self.log(f"Notion Databases Found: {len(databases)}", "INFO")
                self.results["notion"]["status"] = "CONNECTED"

                # Verify critical database IDs are accessible
                db_ids = {
                    "NOTION_ISSUES_DB_ID": os.getenv("NOTION_ISSUES_DB_ID"),
                    "NOTION_KNOWLEDGE_DB_ID": os.getenv("NOTION_KNOWLEDGE_DB_ID"),
                }

                for db_name, db_id in db_ids.items():
                    if db_id:
                        db_response = requests.get(
                            f"https://api.notion.com/v1/databases/{db_id}",
                            headers=headers,
                            timeout=5
                        )
                        if db_response.status_code == 200:
                            self.log(f"{db_name}: ACCESSIBLE", "SUCCESS")
                        else:
                            self.log(f"{db_name}: NOT ACCESSIBLE ({db_response.status_code})", "WARN")

                return True
            elif response.status_code == 401:
                self.log("Notion Authentication: FAILED (Invalid token)", "ERROR")
                self.results["notion"]["status"] = "AUTH_FAILED"
                self.results["issues"].append("Notion token authentication failed")
                return False
            else:
                self.log(f"Notion Connection: FAILED ({response.status_code})", "WARN")
                self.log(f"  Response: {response.text[:200]}", "INFO")
                self.results["notion"]["status"] = "ERROR"
                return False

        except ImportError:
            self.log("requests library not installed", "ERROR")
            self.results["notion"]["status"] = "IMPORT_FAILED"
            return False
        except Exception as e:
            self.log(f"Notion Connection Test FAILED: {e}", "ERROR")
            self.results["notion"]["status"] = "FAILED"
            self.results["issues"].append(f"Notion connection failed: {e}")
            return False

    # ========================================================================
    # Layer 3: AI Bridge Verification
    # ========================================================================

    def check_ai_bridge(self) -> bool:
        """Verify AI bridge integration."""
        self.section("3️⃣  AI AUDIT BRIDGE STATUS")

        try:
            from scripts.utils.openai_audit_adapter import OpenAIAuditAdapter

            adapter = OpenAIAuditAdapter()

            # Check configuration
            print(f"\n{CYAN}Configuration:{RESET}")
            if adapter.api_key:
                masked = adapter.api_key[:10] + "...{:0>5}".format(adapter.api_key[-5:])
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
        """Print restoration summary report."""
        self.section("📊 INTEGRATION RESTORATION STATUS")

        # Count results
        total_vars = len(self.critical_vars)
        present_vars = len([v for v in self.critical_vars if os.getenv(v)])

        print(f"\n{CYAN}Configuration:{RESET}")
        self.log(f"Critical Variables: {present_vars}/{total_vars} ({100 * present_vars // total_vars}%)",
                 "SUCCESS" if present_vars == total_vars else "WARN")

        print(f"\n{CYAN}Integrations:{RESET}")
        notion_status = self.results["notion"].get("status", "UNKNOWN")
        notion_level = "SUCCESS" if notion_status == "CONNECTED" else "WARN"
        self.log(f"Notion Integration: {notion_status}", notion_level)

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
        if present_vars == total_vars and notion_status == "CONNECTED" and ai_status == "READY":
            print(f"{GREEN}🎯 VERDICT: ALL INTEGRATIONS RESTORED & READY{RESET}")
        elif present_vars >= 7 and ai_status == "READY":
            print(f"{YELLOW}🎯 VERDICT: RESTORATION PARTIAL (Notion config needs verification){RESET}")
        else:
            print(f"{RED}🎯 VERDICT: RESTORATION INCOMPLETE{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}")

    def run_restoration(self) -> bool:
        """Execute full integration restoration."""
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{BLUE}🔧 INTEGRATION RESTORATION (Task #042.3){RESET}")
        print(f"{BLUE}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}")

        # Layer 1: Configuration
        config_ok = self.check_integration_variables()

        # Layer 2: Notion
        notion_ok = self.check_notion_connectivity()

        # Layer 3: AI Bridge
        ai_ok = self.check_ai_bridge()

        # Summary
        self.print_summary()

        # Return overall status (Notion is optional, AI bridge is essential)
        return config_ok and ai_ok


def main():
    """Execute integration restoration."""
    restoration = IntegrationRestoration()
    success = restoration.run_restoration()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

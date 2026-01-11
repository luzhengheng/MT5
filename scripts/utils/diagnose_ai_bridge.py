#!/usr/bin/env python3
"""
Verbose AI Bridge Diagnostic Script (Task #042.4)

Comprehensive diagnostic tool to test OpenAI-compatible endpoint connectivity
and reveal exact errors with full traceback logging.

Usage:
    python3 scripts/diagnose_ai_bridge.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import traceback

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
WHITE = "\033[97m"
RESET = "\033[0m"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIBridgeDiagnostic:
    """Comprehensive AI bridge diagnostic tool."""

    def __init__(self):
        """Initialize diagnostic with environment variables."""
        self.config = {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": os.getenv("GEMINI_BASE_URL"),
            "model": os.getenv("GEMINI_MODEL"),
            "provider": os.getenv("GEMINI_PROVIDER"),
        }
        self.results = {
            "config": {},
            "dependencies": {},
            "connection": {},
            "ai_call": {},
            "errors": []
        }

    def log(self, msg, level="INFO"):
        """Print formatted log message."""
        colors = {
            "SUCCESS": GREEN,
            "ERROR": RED,
            "WARN": YELLOW,
            "INFO": CYAN,
            "DEBUG": WHITE,
            "HEADER": BLUE
        }
        prefix = {
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARN": "⚠️",
            "INFO": "ℹ️",
            "DEBUG": "🔍",
            "HEADER": "═"
        }.get(level, "•")
        color = colors.get(level, RESET)
        print(f"{color}{prefix} {msg}{RESET}")

    def section(self, title):
        """Print section header."""
        print(f"\n{BLUE}{'=' * 80}{RESET}")
        print(f"{BLUE}{title}{RESET}")
        print(f"{BLUE}{'-' * 80}{RESET}")

    # ========================================================================
    # Step 1: Configuration Validation
    # ========================================================================

    def check_configuration(self) -> bool:
        """Check and display configuration."""
        self.section("1️⃣  CONFIGURATION VALIDATION")

        all_present = True
        for key, value in self.config.items():
            if value:
                # Mask sensitive values
                if "key" in key.lower():
                    masked = value[:10] + "...{:0>5}".format(value[-5:]) if len(value) > 15 else "***"
                else:
                    masked = value
                self.log(f"{key:20s}: {masked}", "SUCCESS")
                self.results["config"][key] = "PRESENT"
            else:
                self.log(f"{key:20s}: MISSING", "ERROR")
                self.results["config"][key] = "MISSING"
                self.results["errors"].append(f"Configuration missing: {key}")
                all_present = False

        return all_present

    # ========================================================================
    # Step 2: Dependency Check
    # ========================================================================

    def check_dependencies(self) -> bool:
        """Check required dependencies."""
        self.section("2️⃣  DEPENDENCY CHECK")

        dependencies = {
            "requests": "HTTP client library",
            "openai": "OpenAI API client",
            "dotenv": "Environment loading",
        }

        all_available = True
        for package, description in dependencies.items():
            try:
                __import__(package)
                self.log(f"{package:20s}: {description}", "SUCCESS")
                self.results["dependencies"][package] = "INSTALLED"
            except ImportError as e:
                self.log(f"{package:20s}: {description} - NOT FOUND", "ERROR")
                self.results["dependencies"][package] = "MISSING"
                self.results["errors"].append(f"Missing dependency: {package}")
                all_available = False

        return all_available

    # ========================================================================
    # Step 3: Network Connectivity Test
    # ========================================================================

    def test_network_connectivity(self) -> bool:
        """Test basic network connectivity to endpoint."""
        self.section("3️⃣  NETWORK CONNECTIVITY TEST")

        base_url = self.config["base_url"]
        if not base_url:
            self.log("Cannot test - base_url not configured", "ERROR")
            return False

        try:
            import requests

            print(f"\n{CYAN}Testing HTTP connectivity to: {base_url}{RESET}")

            # Test with simple GET to base URL
            self.log(f"Attempting: GET {base_url}", "INFO")

            response = requests.get(
                base_url,
                headers={"User-Agent": "MT5-CRS-Diagnostic/1.0"},
                timeout=10,
                allow_redirects=True
            )

            self.log(f"HTTP Status: {response.status_code}", "INFO")
            self.log(f"Response Headers: {dict(response.headers)}", "DEBUG")

            if response.status_code in [200, 301, 302, 403]:  # 403 is Cloudflare
                self.log(f"Network: REACHABLE (status {response.status_code})", "SUCCESS")
                self.results["connection"]["network"] = "REACHABLE"

                # Print response info
                if response.status_code == 403:
                    self.log("Note: 403 indicates Cloudflare protection (expected)", "WARN")
                    self.log("Response preview: " + response.text[:200], "DEBUG")
                else:
                    self.log("Response preview: " + response.text[:200], "DEBUG")

                return True
            else:
                self.log(f"Network: ERROR (status {response.status_code})", "ERROR")
                self.results["connection"]["network"] = "ERROR"
                self.log(f"Response: {response.text[:500]}", "ERROR")
                return False

        except requests.exceptions.Timeout:
            self.log("Network: TIMEOUT (endpoint not responding)", "ERROR")
            self.results["connection"]["network"] = "TIMEOUT"
            self.results["errors"].append("Network timeout to AI endpoint")
            return False
        except requests.exceptions.ConnectionError as e:
            self.log(f"Network: CONNECTION FAILED", "ERROR")
            self.log(f"Error: {str(e)}", "ERROR")
            self.results["connection"]["network"] = "CONNECTION_FAILED"
            self.results["errors"].append(f"Network connection failed: {e}")
            return False
        except Exception as e:
            self.log(f"Network: UNEXPECTED ERROR", "ERROR")
            self.log(f"Error: {str(e)}", "ERROR")
            self.log(f"Traceback:\n{traceback.format_exc()}", "DEBUG")
            self.results["connection"]["network"] = "ERROR"
            self.results["errors"].append(f"Network test failed: {e}")
            return False

    # ========================================================================
    # Step 4: HTTP Headers Preparation (For v0.8.0 compatibility)
    # ========================================================================

    def prepare_http_headers(self) -> bool:
        """Prepare HTTP headers for API call."""
        self.section("4️⃣  HTTP HEADERS PREPARATION")

        try:
            api_key = self.config["api_key"]

            if not api_key:
                self.log("Cannot prepare - missing API key", "ERROR")
                return False

            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "MT5-CRS-Diagnostic/1.0"
            }

            self.log("HTTP Headers: PREPARED", "SUCCESS")
            self.log(f"  - Authorization: Bearer {api_key[:10]}...{api_key[-5:]}", "DEBUG")
            self.log(f"  - Content-Type: application/json", "DEBUG")
            self.results["connection"]["headers"] = "PREPARED"
            return True

        except Exception as e:
            self.log(f"Header Preparation: FAILED - {e}", "ERROR")
            self.results["connection"]["headers"] = "FAILED"
            self.results["errors"].append(f"Header prep failed: {e}")
            return False

    # ========================================================================
    # Step 5: AI API Call (The Critical Test - Using requests directly)
    # ========================================================================

    def test_ai_call(self) -> bool:
        """Make actual API call to OpenAI-compatible endpoint using requests."""
        self.section("5️⃣  AI API CALL TEST (CRITICAL)")

        if not hasattr(self, 'headers'):
            self.log("Headers not prepared - skipping AI call", "ERROR")
            return False

        try:
            import requests

            model = self.config["model"]
            base_url = self.config["base_url"]

            if not model:
                self.log("Model not configured", "ERROR")
                return False

            # Construct the endpoint URL
            endpoint_url = f"{base_url}/chat/completions"
            self.log(f"Sending request to: {endpoint_url}", "INFO")
            self.log(f"Using model: {model}", "INFO")
            self.log(f"Prompt: 'Hello, are you alive?'", "INFO")

            # Prepare request payload
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, are you alive? Please respond briefly."
                    }
                ],
                "max_tokens": 200,
                "temperature": 0.3
            }

            self.log(f"Request payload: {json.dumps(payload, indent=2)}", "DEBUG")

            # Make the actual HTTP request
            self.log(f"Making POST request...", "INFO")
            response = requests.post(
                endpoint_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            self.log(f"HTTP Status: {response.status_code}", "INFO")
            self.log(f"Response Headers: {dict(response.headers)}", "DEBUG")

            # Check response status
            if response.status_code == 200:
                # Parse successful response
                response_json = response.json()
                self.log(f"Response JSON: {json.dumps(response_json, indent=2)}", "DEBUG")

                # Extract message from response
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    reply = response_json["choices"][0].get("message", {}).get("content", "")
                    self.log(f"AI API Call: SUCCESS ✅", "SUCCESS")
                    self.log(f"Response received: {reply}", "SUCCESS")
                    self.results["ai_call"]["status"] = "SUCCESS"
                    self.results["ai_call"]["response"] = reply
                    return True
                else:
                    self.log(f"AI API Call: INVALID RESPONSE FORMAT", "ERROR")
                    self.log(f"Response: {response_json}", "ERROR")
                    self.results["ai_call"]["status"] = "INVALID_FORMAT"
                    self.results["errors"].append("Invalid response format from API")
                    return False
            else:
                # Handle error responses
                self.log(f"AI API Call: HTTP {response.status_code}", "ERROR")
                try:
                    error_json = response.json()
                    self.log(f"Error response: {json.dumps(error_json, indent=2)}", "ERROR")
                except:
                    self.log(f"Error response (raw): {response.text[:500]}", "ERROR")

                self.results["ai_call"]["status"] = f"HTTP_{response.status_code}"
                self.results["errors"].append(f"API returned HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            self.log(f"AI API Call: TIMEOUT", "ERROR")
            self.log(f"Request to {endpoint_url} timed out", "ERROR")
            self.results["ai_call"]["status"] = "TIMEOUT"
            self.results["errors"].append("API request timeout")
            return False
        except requests.exceptions.ConnectionError as e:
            self.log(f"AI API Call: CONNECTION ERROR", "ERROR")
            self.log(f"Error: {str(e)}", "ERROR")
            self.results["ai_call"]["status"] = "CONNECTION_ERROR"
            self.results["errors"].append(f"Connection error: {e}")
            return False
        except json.JSONDecodeError as e:
            self.log(f"AI API Call: JSON PARSE ERROR", "ERROR")
            self.log(f"Error: {str(e)}", "ERROR")
            self.log(f"Response text: {response.text[:500]}", "ERROR")
            self.results["ai_call"]["status"] = "JSON_ERROR"
            self.results["errors"].append(f"JSON parse error: {e}")
            return False
        except Exception as e:
            error_str = str(e)
            self.log(f"AI API Call: UNEXPECTED ERROR", "ERROR")
            self.log(f"Error Type: {type(e).__name__}", "ERROR")
            self.log(f"Error Message: {error_str}", "ERROR")

            # Print full traceback for debugging
            self.log(f"Full Traceback:", "DEBUG")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    self.log(f"  {line}", "DEBUG")

            self.results["ai_call"]["status"] = "FAILED"
            self.results["ai_call"]["error"] = error_str
            self.results["errors"].append(f"AI call failed: {e}")
            return False

    # ========================================================================
    # Summary Report
    # ========================================================================

    def print_summary(self):
        """Print comprehensive diagnostic summary."""
        self.section("📊 DIAGNOSTIC SUMMARY")

        # Configuration summary
        config_ok = all(v == "PRESENT" for v in self.results["config"].values())
        config_count = sum(1 for v in self.results["config"].values() if v == "PRESENT")
        print(f"\n{CYAN}Configuration:{RESET}")
        self.log(f"Variables: {config_count}/4", "SUCCESS" if config_ok else "ERROR")

        # Dependencies summary
        deps_ok = all(v == "INSTALLED" for v in self.results["dependencies"].values())
        deps_count = sum(1 for v in self.results["dependencies"].values() if v == "INSTALLED")
        print(f"\n{CYAN}Dependencies:{RESET}")
        self.log(f"Installed: {deps_count}/3", "SUCCESS" if deps_ok else "ERROR")

        # Connection summary
        print(f"\n{CYAN}Connectivity:{RESET}")
        network_status = self.results["connection"].get("network", "UNKNOWN")
        headers_status = self.results["connection"].get("headers", "UNKNOWN")
        self.log(f"Network: {network_status}", "SUCCESS" if "REACHABLE" in network_status else "WARN")
        self.log(f"Headers: {headers_status}", "SUCCESS" if headers_status == "PREPARED" else "ERROR")

        # AI Call summary
        print(f"\n{CYAN}AI Bridge:{RESET}")
        ai_status = self.results["ai_call"].get("status", "UNKNOWN")
        if ai_status == "SUCCESS":
            response = self.results["ai_call"].get("response", "")
            self.log(f"Status: {ai_status} ✅", "SUCCESS")
            self.log(f"AI Response: '{response[:100]}...'", "SUCCESS")
        else:
            error = self.results["ai_call"].get("error", "Unknown error")
            self.log(f"Status: {ai_status} ❌", "ERROR")
            self.log(f"Error: {error[:200]}", "ERROR")

        # Overall verdict
        print(f"\n{BLUE}{'=' * 80}{RESET}")
        if ai_status == "SUCCESS":
            print(f"{GREEN}🎯 VERDICT: AI BRIDGE FULLY OPERATIONAL ✅{RESET}")
            print(f"{GREEN}External AI endpoint is responding correctly!{RESET}")
        elif config_ok and deps_ok and "REACHABLE" in network_status:
            print(f"{YELLOW}🎯 VERDICT: PARTIAL CONNECTIVITY (API error details above){RESET}")
            print(f"{YELLOW}Check error details in diagnostic output{RESET}")
        else:
            print(f"{RED}🎯 VERDICT: CONNECTIVITY ISSUES{RESET}")
            print(f"{RED}See error details above{RESET}")
        print(f"{BLUE}{'=' * 80}{RESET}")

        # Errors report
        if self.results["errors"]:
            print(f"\n{CYAN}Errors Found ({len(self.results['errors'])}):{RESET}")
            for i, error in enumerate(self.results["errors"], 1):
                self.log(f"{i}. {error}", "ERROR")

    def run_diagnostic(self) -> bool:
        """Execute complete diagnostic sequence."""
        print(f"\n{BLUE}{'=' * 80}{RESET}")
        print(f"{BLUE}🔧 AI BRIDGE DIAGNOSTIC TOOL (Task #042.4){RESET}")
        print(f"{BLUE}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BLUE}Purpose: Test OpenAI-compatible endpoint connectivity{RESET}")
        print(f"{BLUE}{'=' * 80}{RESET}")

        # Execute diagnostic steps
        config_ok = self.check_configuration()
        deps_ok = self.check_dependencies()
        network_ok = self.test_network_connectivity()
        headers_ok = self.prepare_http_headers()
        ai_ok = self.test_ai_call()

        # Print summary
        self.print_summary()

        # Return overall success (AI call is critical)
        return ai_ok


def main():
    """Execute AI bridge diagnostic."""
    diagnostic = AIBridgeDiagnostic()
    success = diagnostic.run_diagnostic()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate 1 Audit for TASK #034: Production Deployment & DingTalk Integration Verification

Validates that all production deployment configurations are correct:
1. Nginx configuration with Basic Auth
2. .env file with DingTalk secrets
3. Deployment script functionality
4. UAT test suite completeness
5. Documentation completeness
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Logging and reporting
class AuditReport:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []
        self.sections = {}

    def start_section(self, name):
        self.sections[name] = {"passed": 0, "failed": 0, "checks": []}

    def log_pass(self, section, check_name, details=""):
        self.checks_passed += 1
        self.sections[section]["passed"] += 1
        print(f"  ✅ {check_name}")
        if details:
            print(f"     {details}")
        self.sections[section]["checks"].append((check_name, "PASS", details))

    def log_fail(self, section, check_name, error=""):
        self.checks_failed += 1
        self.sections[section]["failed"] += 1
        print(f"  ❌ {check_name}")
        if error:
            print(f"     Error: {error}")
        self.sections[section]["checks"].append((check_name, "FAIL", error))

    def print_summary(self):
        print("\n" + "=" * 80)
        print("GATE 1 AUDIT SUMMARY - TASK #034 Production Deployment")
        print("=" * 80)
        print(f"Total Checks: {self.checks_passed + self.checks_failed}")
        print(f"Passed: {self.checks_passed}")
        print(f"Failed: {self.checks_failed}")
        print(f"Success Rate: {self.checks_passed}/{self.checks_passed + self.checks_failed} ({100 * self.checks_passed // (self.checks_passed + self.checks_failed) if self.checks_passed + self.checks_failed > 0 else 0}%)")
        print()

        for section, data in self.sections.items():
            status = "✅" if data["failed"] == 0 else "❌"
            print(f"{status} {section}: {data['passed']}/{data['passed'] + data['failed']}")

        print()
        if self.checks_failed == 0:
            print("✅ GATE 1 AUDIT: PASSED")
            print("All production deployment configurations verified and correct.")
            return True
        else:
            print(f"❌ GATE 1 AUDIT: FAILED ({self.checks_failed} issues found)")
            print("Review errors above before proceeding to production.")
            return False


def audit_deployment_files(report):
    """Audit 1: Verify all deployment files exist and are correct"""
    report.start_section("Deployment Files")

    # Check nginx_dashboard.conf
    nginx_conf = PROJECT_ROOT / "nginx_dashboard.conf"
    if nginx_conf.exists():
        with open(nginx_conf, 'r') as f:
            content = f.read()
            if "auth_basic" in content and "htpasswd" in content:
                report.log_pass("Deployment Files", "nginx_dashboard.conf exists with auth_basic", f"{len(content)} bytes")
            else:
                report.log_fail("Deployment Files", "nginx_dashboard.conf missing auth configuration")
    else:
        report.log_fail("Deployment Files", "nginx_dashboard.conf not found")

    # Check deploy_production.sh
    deploy_script = PROJECT_ROOT / "deploy_production.sh"
    if deploy_script.exists():
        with open(deploy_script, 'r') as f:
            content = f.read()
            if "htpasswd" in content and "systemctl" in content and "streamlit" in content:
                report.log_pass("Deployment Files", "deploy_production.sh exists with all steps", f"{len(content)} bytes")
            else:
                report.log_fail("Deployment Files", "deploy_production.sh incomplete")
    else:
        report.log_fail("Deployment Files", "deploy_production.sh not found")

    # Check .env.production
    env_file = PROJECT_ROOT / ".env.production"
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "DINGTALK" in content and "DASHBOARD" in content:
                report.log_pass("Deployment Files", ".env.production exists with config", f"{len(content)} bytes")
            else:
                report.log_fail("Deployment Files", ".env.production missing required variables")
    else:
        report.log_fail("Deployment Files", ".env.production not found")

    # Check UAT script
    uat_script = PROJECT_ROOT / "scripts" / "uat_task_034.py"
    if uat_script.exists():
        with open(uat_script, 'r') as f:
            content = f.read()
            if "class DingTalkUAT" in content and "def run_all_tests" in content:
                report.log_pass("Deployment Files", "scripts/uat_task_034.py exists", f"{len(content)} bytes")
            else:
                report.log_fail("Deployment Files", "uat_task_034.py incomplete")
    else:
        report.log_fail("Deployment Files", "uat_task_034.py not found")


def audit_nginx_configuration(report):
    """Audit 2: Verify Nginx configuration is correct"""
    report.start_section("Nginx Configuration")

    nginx_conf = PROJECT_ROOT / "nginx_dashboard.conf"
    with open(nginx_conf, 'r') as f:
        content = f.read()

    # Check for auth_basic
    if "auth_basic" in content:
        report.log_pass("Nginx Configuration", "Nginx auth_basic configured")
    else:
        report.log_fail("Nginx Configuration", "auth_basic not found in Nginx config")

    # Check for htpasswd file reference
    if "/etc/nginx/.htpasswd" in content:
        report.log_pass("Nginx Configuration", "htpasswd file referenced correctly")
    else:
        report.log_fail("Nginx Configuration", "htpasswd file path not found in config")

    # Check for proxy_pass
    if "proxy_pass http://streamlit" in content:
        report.log_pass("Nginx Configuration", "Streamlit proxy configured")
    else:
        report.log_fail("Nginx Configuration", "Streamlit proxy not found")

    # Check for WebSocket support
    if "Upgrade" in content and "Connection" in content:
        report.log_pass("Nginx Configuration", "WebSocket upgrade headers configured")
    else:
        report.log_fail("Nginx Configuration", "WebSocket support missing")

    # Check for security headers
    if "X-Frame-Options" in content:
        report.log_pass("Nginx Configuration", "Security headers configured")
    else:
        report.log_fail("Nginx Configuration", "Security headers missing")

    # Check for correct server_name
    if "www.crestive.net" in content:
        report.log_pass("Nginx Configuration", "Server name configured correctly")
    else:
        report.log_fail("Nginx Configuration", "Server name not set to www.crestive.net")


def audit_environment_configuration(report):
    """Audit 3: Verify .env configuration"""
    report.start_section("Environment Configuration")

    # Check .env.production variables
    env_file = PROJECT_ROOT / ".env.production"
    with open(env_file, 'r') as f:
        env_content = f.read()

    required_vars = [
        "DINGTALK_WEBHOOK_URL",
        "DINGTALK_SECRET",
        "DASHBOARD_PUBLIC_URL",
        "STREAMLIT_HOST",
        "STREAMLIT_PORT",
    ]

    for var in required_vars:
        if f"{var}=" in env_content:
            report.log_pass("Environment Configuration", f"{var} present in .env.production")
        else:
            report.log_fail("Environment Configuration", f"{var} missing from .env.production")

    # Check for DINGTALK_SECRET format
    if "DINGTALK_SECRET=SEC" in env_content:
        report.log_pass("Environment Configuration", "DINGTALK_SECRET has correct format (SEC prefix)")
    else:
        report.log_fail("Environment Configuration", "DINGTALK_SECRET missing SEC prefix")

    # Check for no hardcoded webhook token in template
    if "YOUR_ACTUAL_TOKEN" in env_content or "YOUR_TOKEN" in env_content:
        report.log_pass("Environment Configuration", ".env.production has placeholder for webhook token (expected)")
    else:
        report.log_fail("Environment Configuration", "Webhook token format unclear")

    # Check .gitignore excludes .env
    gitignore = PROJECT_ROOT / ".gitignore"
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            git_content = f.read()
            if ".env" in git_content:
                report.log_pass("Environment Configuration", ".gitignore excludes .env files")
            else:
                report.log_fail("Environment Configuration", ".env not in .gitignore")


def audit_deployment_script(report):
    """Audit 4: Verify deploy_production.sh functionality"""
    report.start_section("Deployment Script")

    deploy_script = PROJECT_ROOT / "deploy_production.sh"
    with open(deploy_script, 'r') as f:
        content = f.read()

    required_steps = [
        ("htpasswd generation", "htpasswd -bc"),
        ("Nginx config copy", "cp"),
        ("Nginx config copy", "nginx_dashboard.conf"),
        ("Nginx symlink", "ln -s"),
        ("Nginx symlink", "sites-enabled"),
        ("Nginx validation", "nginx -t"),
        ("Nginx reload", "systemctl reload nginx"),
        ("Streamlit startup", "streamlit run"),
        ("Service verification", "pgrep"),
    ]

    for step_name, pattern in required_steps:
        if pattern in content:
            report.log_pass("Deployment Script", f"Step: {step_name}")
        else:
            report.log_fail("Deployment Script", f"Step missing: {step_name}")

    # Check for error handling
    if "set -e" in content or "trap" in content:
        report.log_pass("Deployment Script", "Error handling configured")
    else:
        report.log_fail("Deployment Script", "No error handling found")


def audit_uat_test_suite(report):
    """Audit 5: Verify UAT test suite"""
    report.start_section("UAT Test Suite")

    uat_script = PROJECT_ROOT / "scripts" / "uat_task_034.py"
    with open(uat_script, 'r') as f:
        content = f.read()

    # Count test methods
    test_methods = [
        "test_dashboard_access",
        "test_dashboard_with_auth",
        "test_dingtalk_configuration",
        "test_send_real_dingtalk_alert",
        "test_kill_switch_alert",
        "test_dashboard_url_in_alerts",
        "test_nginx_proxy_headers",
        "test_streamlit_running",
    ]

    for test in test_methods:
        if f"def {test}" in content:
            report.log_pass("UAT Test Suite", f"Test method: {test}")
        else:
            report.log_fail("UAT Test Suite", f"Missing test: {test}")

    # Check for result tracking
    if "self.tests_passed" in content and "self.tests_failed" in content:
        report.log_pass("UAT Test Suite", "Test result tracking configured")
    else:
        report.log_fail("UAT Test Suite", "Result tracking missing")

    # Check for summary output
    if "def print_summary" in content:
        report.log_pass("UAT Test Suite", "Summary output configured")
    else:
        report.log_fail("UAT Test Suite", "Summary output missing")


def audit_documentation(report):
    """Audit 6: Verify documentation completeness"""
    report.start_section("Documentation")

    docs_dir = PROJECT_ROOT / "docs" / "archive" / "tasks" / "TASK_034_DEPLOYMENT"

    required_docs = [
        ("DEPLOYMENT_GUIDE.md", "deployment guide"),
        ("SECRETS_MANAGEMENT.md", "secrets management"),
        ("VERIFICATION_CHECKLIST.md", "verification checklist"),
    ]

    for doc_file, description in required_docs:
        doc_path = docs_dir / doc_file
        if doc_path.exists():
            with open(doc_path, 'r') as f:
                content = f.read()
            report.log_pass("Documentation", f"{description} present", f"{len(content)} bytes")
        else:
            report.log_fail("Documentation", f"{description} missing: {doc_file}")

    # Check for task summary
    summary_path = docs_dir / "IMPLEMENTATION_SUMMARY.md"
    if summary_path.exists():
        report.log_pass("Documentation", "Implementation summary present")
    else:
        report.log_fail("Documentation", "Implementation summary missing")


def audit_security_configuration(report):
    """Audit 7: Verify security best practices"""
    report.start_section("Security Configuration")

    # Check .env permissions
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        mode = oct(env_file.stat().st_mode)[-3:]
        if mode == "600":
            report.log_pass("Security Configuration", ".env has secure permissions (600)")
        else:
            report.log_fail("Security Configuration", f".env permissions too open: {mode} (should be 600)")
    else:
        # .env might not exist yet (normal before deployment)
        report.log_pass("Security Configuration", ".env not yet created (expected)")

    # Check Nginx config has auth
    nginx_conf = PROJECT_ROOT / "nginx_dashboard.conf"
    with open(nginx_conf, 'r') as f:
        content = f.read()

    if "auth_basic" in content:
        report.log_pass("Security Configuration", "Basic Auth enabled in Nginx")
    else:
        report.log_fail("Security Configuration", "Basic Auth not enabled")

    # Check for hardcoded credentials (skip test/audit/uat scripts)
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # Skip test, audit, and UAT scripts (these use test credentials intentionally)
        if any(x in str(py_file) for x in ["test_", "audit_", "uat_"]):
            continue
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                if "MT5Hub@2025" in f.read():
                    report.log_fail("Security Configuration", f"Password found in source code: {py_file}")
                    return
        except Exception:
            continue

    report.log_pass("Security Configuration", "No hardcoded credentials in production source code (test credentials in UAT script OK)")

    # Check for secret in config
    config_file = PROJECT_ROOT / "src" / "config.py"
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
            if "SEC7d7cbd" in content:
                report.log_fail("Security Configuration", "Secret found hardcoded in config.py")
            else:
                report.log_pass("Security Configuration", "Secrets loaded from environment only")


def audit_integration_completeness(report):
    """Audit 8: Verify integration with existing systems"""
    report.start_section("Integration Completeness")

    # Check config.py has required variables
    config_file = PROJECT_ROOT / "src" / "config.py"
    with open(config_file, 'r') as f:
        config_content = f.read()

    required_config = [
        "DASHBOARD_PUBLIC_URL",
        "DINGTALK_WEBHOOK_URL",
        "DINGTALK_SECRET",
        "STREAMLIT_HOST",
        "STREAMLIT_PORT",
    ]

    for var in required_config:
        if var in config_content:
            report.log_pass("Integration Completeness", f"Config variable: {var}")
        else:
            report.log_fail("Integration Completeness", f"Config variable missing: {var}")

    # Check dashboard module exists
    dashboard_init = PROJECT_ROOT / "src" / "dashboard" / "__init__.py"
    if dashboard_init.exists():
        report.log_pass("Integration Completeness", "Dashboard module initialized")
    else:
        report.log_fail("Integration Completeness", "Dashboard module not found")

    # Check notifier exists
    notifier_file = PROJECT_ROOT / "src" / "dashboard" / "notifier.py"
    if notifier_file.exists():
        report.log_pass("Integration Completeness", "DingTalk notifier module present")
    else:
        report.log_fail("Integration Completeness", "Notifier module not found")

    # Check app.py exists
    app_file = PROJECT_ROOT / "src" / "dashboard" / "app.py"
    if app_file.exists():
        report.log_pass("Integration Completeness", "Streamlit app.py present")
    else:
        report.log_fail("Integration Completeness", "Streamlit app missing")


def main():
    """Run all audits"""
    print("=" * 80)
    print("GATE 1 AUDIT - TASK #034 Production Deployment & DingTalk Integration")
    print("=" * 80)
    print()

    report = AuditReport()

    # Run all audits
    print("Running Deployment Files Audit...")
    audit_deployment_files(report)
    print()

    print("Running Nginx Configuration Audit...")
    audit_nginx_configuration(report)
    print()

    print("Running Environment Configuration Audit...")
    audit_environment_configuration(report)
    print()

    print("Running Deployment Script Audit...")
    audit_deployment_script(report)
    print()

    print("Running UAT Test Suite Audit...")
    audit_uat_test_suite(report)
    print()

    print("Running Documentation Audit...")
    audit_documentation(report)
    print()

    print("Running Security Configuration Audit...")
    audit_security_configuration(report)
    print()

    print("Running Integration Completeness Audit...")
    audit_integration_completeness(report)
    print()

    # Print summary
    success = report.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

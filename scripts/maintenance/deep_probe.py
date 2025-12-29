#!/usr/bin/env python3
"""
Deep Infrastructure Probe

Task #040.9: Infrastructure Integrity & Identity Check

Performs comprehensive diagnostic of:
1. Server identity (hostname, IPs, OS)
2. Network interfaces
3. Database connectivity (brute-force all credential combinations)
4. Service health (PostgreSQL, Redis)
5. Virtual environment status

Usage:
    python3 scripts/maintenance/deep_probe.py
"""

import os
import platform
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def print_header():
    """Print diagnostic report header."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "DEEP INFRASTRUCTURE PROBE".center(78) + "║")
    print("║" + f"Task #040.9 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()


def verify_server_identity():
    """Comprehensive server identity check."""
    print("=" * 80)
    print("🖥️  SERVER IDENTITY")
    print("=" * 80)
    print()

    # Basic info
    hostname = platform.node()
    fqdn = socket.getfqdn()

    print(f"Hostname:          {hostname}")
    print(f"FQDN:              {fqdn}")
    print(f"Operating System:  {platform.system()} {platform.release()}")
    print(f"Processor:         {platform.processor() or 'Unknown'}")
    print(f"Python Version:    {platform.python_version()}")
    print()

    # IP addresses
    print("IP Addresses:")
    print("-" * 80)

    try:
        # Get primary IP
        primary_ip = socket.gethostbyname(hostname)
        print(f"  Primary (via hostname): {primary_ip}")
    except:
        print(f"  Primary: Unable to resolve")

    # Get all addresses
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        seen_ips = set()

        for addr_info in addr_infos:
            ip = addr_info[4][0]
            if ip not in seen_ips:
                family = "IPv4" if addr_info[0] == socket.AF_INET else "IPv6"
                print(f"  {family}: {ip}")
                seen_ips.add(ip)

    except Exception as e:
        print(f"  Error getting addresses: {e}")

    print()

    # Localhost
    print("Loopback:")
    print("-" * 80)
    print(f"  IPv4: 127.0.0.1")
    print(f"  IPv6: ::1")
    print()

    return hostname, primary_ip


def check_service_ports():
    """Check if critical services are listening."""
    print("=" * 80)
    print("🔌 SERVICE CONNECTIVITY")
    print("=" * 80)
    print()

    services = [
        ("PostgreSQL", "localhost", 5432),
        ("Redis", "localhost", 6379),
    ]

    results = {}

    for service_name, host, port in services:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"✅ {service_name:15} → {host}:{port} (LISTENING)")
                results[service_name] = True
            else:
                print(f"❌ {service_name:15} → {host}:{port} (NOT REACHABLE)")
                results[service_name] = False

        except Exception as e:
            print(f"❌ {service_name:15} → {host}:{port} (ERROR: {e})")
            results[service_name] = False

    print()
    return results


def test_database_connectivity():
    """Brute-force test all database connection combinations."""
    print("=" * 80)
    print("🗄️  DATABASE CONNECTIVITY MATRIX")
    print("=" * 80)
    print()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    hostname = platform.node()
    primary_ip = socket.gethostbyname(hostname)

    # Credential combinations to test
    credentials = [
        ("localhost", 5432, "postgres", ""),
        ("localhost", 5432, "postgres", "password"),
        ("localhost", 5432, "trader", "password"),
        ("localhost", 5432, "trader", "mt5crs_dev_2025"),
        ("127.0.0.1", 5432, "trader", "password"),
        ("127.0.0.1", 5432, "trader", "mt5crs_dev_2025"),
        (hostname, 5432, "trader", "mt5crs_dev_2025"),
        (primary_ip, 5432, "trader", "mt5crs_dev_2025"),
    ]

    working_connections = []

    print(f"Testing {len(credentials)} connection combinations...")
    print()

    for host, port, user, password in credentials:
        try:
            from sqlalchemy import create_engine, text

            # Build connection string
            if password:
                conn_string = f"postgresql://{user}:{password}@{host}:{port}/mt5_crs"
                display_conn = f"postgresql://{user}:***@{host}:{port}/mt5_crs"
            else:
                conn_string = f"postgresql://{user}@{host}:{port}/mt5_crs"
                display_conn = conn_string

            engine = create_engine(
                conn_string,
                connect_args={"connect_timeout": 3}
            )

            with engine.connect() as conn:
                # Test query
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]

                # Check for TimescaleDB
                try:
                    result = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"))
                    ts_version = result.fetchone()
                    if ts_version:
                        ts_info = f"TimescaleDB {ts_version[0]}"
                    else:
                        ts_info = "TimescaleDB NOT installed"
                except:
                    ts_info = "Unable to check TimescaleDB"

                # Get table counts
                try:
                    result = conn.execute(text("SELECT count(*) FROM market_data"))
                    market_count = result.fetchone()[0]

                    result = conn.execute(text("SELECT count(*) FROM assets"))
                    assets_count = result.fetchone()[0]

                    counts_info = f"market_data: {market_count}, assets: {assets_count}"
                except:
                    counts_info = "Unable to query tables"

                print(f"✅ SUCCESS: {user}@{host}:{port}")
                print(f"   Connection: {display_conn}")
                print(f"   PostgreSQL: {version[:60]}...")
                print(f"   {ts_info}")
                print(f"   Tables: {counts_info}")
                print()

                working_connections.append({
                    "host": host,
                    "port": port,
                    "user": user,
                    "conn_string": conn_string,
                    "version": version,
                    "timescaledb": ts_info,
                    "counts": counts_info
                })

        except Exception as e:
            print(f"❌ FAILED: {user}@{host}:{port}")
            print(f"   Error: {str(e)[:100]}")
            print()

    if not working_connections:
        print("⚠️  WARNING: No database connections succeeded!")
        print()
        print("💡 Possible fixes:")
        print("   1. Start PostgreSQL: docker-compose up -d postgres")
        print("   2. Check credentials in .env file")
        print("   3. Verify PostgreSQL is accepting connections")
        print()

    return working_connections


def check_venv_health():
    """Check virtual environment status."""
    print("=" * 80)
    print("🐍 VIRTUAL ENVIRONMENT STATUS")
    print("=" * 80)
    print()

    venv_path = PROJECT_ROOT / "venv"

    if not venv_path.exists():
        print("❌ venv/ directory NOT FOUND")
        print()
        return False

    print(f"✅ venv/ directory exists: {venv_path}")
    print()

    # Check structure
    print("Structure Check:")
    print("-" * 80)

    components = {
        "bin": "Executables",
        "lib": "Python packages",
        "pyvenv.cfg": "Configuration",
    }

    all_ok = True
    for component, description in components.items():
        comp_path = venv_path / component
        if comp_path.exists():
            print(f"  ✅ {component:15} → {description}")
        else:
            print(f"  ❌ {component:15} → MISSING ({description})")
            all_ok = False

    print()

    # Check activate script
    activate_path = venv_path / "bin" / "activate"
    if activate_path.exists():
        print(f"✅ Activation script: {activate_path}")
    else:
        print(f"❌ Activation script NOT FOUND")
        all_ok = False

    print()

    # Check pip
    try:
        result = subprocess.run(
            [str(venv_path / "bin" / "pip"), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ pip version: {result.stdout.strip()}")
        else:
            print(f"❌ pip not working")
            all_ok = False
    except Exception as e:
        print(f"❌ pip check failed: {e}")
        all_ok = False

    print()

    return all_ok


def check_root_pollution():
    """Check for orphaned venv files in project root."""
    print("=" * 80)
    print("📁 PROJECT ROOT CLEANLINESS")
    print("=" * 80)
    print()

    suspects = ["bin", "lib", "lib64", "include", "pyvenv.cfg"]
    found_suspects = []

    for suspect in suspects:
        suspect_path = PROJECT_ROOT / suspect
        if suspect_path.exists():
            # Check if it's the venv or a project directory
            if suspect == "bin":
                # bin/ could be legitimate project scripts
                # Check if it contains Python venv executables
                if (suspect_path / "activate").exists():
                    found_suspects.append((suspect, "Orphaned venv component"))
                else:
                    print(f"  ℹ️  {suspect:15} → Project directory (not venv)")
            else:
                found_suspects.append((suspect, "Orphaned venv component"))

    if found_suspects:
        print("⚠️  Potential orphaned venv files found:")
        print()
        for suspect, reason in found_suspects:
            print(f"  ⚠️  {suspect:15} → {reason}")
        print()
        print("💡 Run fix_environment.py to clean up")
        print()
        return False
    else:
        print("✅ Project root is clean (no orphaned venv files)")
        print()
        return True


def generate_summary(hostname, primary_ip, services, db_connections, venv_ok, root_clean):
    """Generate final summary."""
    print("=" * 80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print()

    print("Server Identity:")
    print(f"  Hostname: {hostname}")
    print(f"  Primary IP: {primary_ip}")
    print()

    print("Services:")
    for service, status in services.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {service}")
    print()

    print("Database:")
    if db_connections:
        print(f"  ✅ {len(db_connections)} working connection(s)")
        print(f"  Recommended: {db_connections[0]['user']}@{db_connections[0]['host']}:{db_connections[0]['port']}")
    else:
        print(f"  ❌ No working database connections")
    print()

    print("Environment:")
    print(f"  {'✅' if venv_ok else '❌'} Virtual environment healthy")
    print(f"  {'✅' if root_clean else '⚠️ '} Project root clean")
    print()

    # Overall status
    all_good = services.get("PostgreSQL", False) and venv_ok and root_clean

    if all_good:
        print("🎉 OVERALL STATUS: ✅ HEALTHY")
    else:
        print("⚠️  OVERALL STATUS: NEEDS ATTENTION")
        print()
        print("Recommended actions:")
        if not services.get("PostgreSQL"):
            print("  • Start PostgreSQL: docker-compose up -d postgres")
        if not venv_ok:
            print("  • Fix venv: python3 scripts/maintenance/fix_environment.py")
        if not root_clean:
            print("  • Clean root: python3 scripts/maintenance/fix_environment.py")

    print()


def main():
    """Main diagnostic flow."""
    print_header()

    # Server identity
    hostname, primary_ip = verify_server_identity()

    # Service connectivity
    services = check_service_ports()

    # Database connectivity
    db_connections = test_database_connectivity()

    # Venv health
    venv_ok = check_venv_health()

    # Root pollution
    root_clean = check_root_pollution()

    # Summary
    generate_summary(hostname, primary_ip, services, db_connections, venv_ok, root_clean)

    # Return success if all critical checks pass
    if services.get("PostgreSQL") and venv_ok:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

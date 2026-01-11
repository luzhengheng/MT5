#!/usr/bin/env python3
"""
Test External Audit Connection (Task #042.1)

Verifies:
1. .env is properly configured
2. openai library is installed
3. OpenAI-compatible endpoint is reachable
4. Credentials are valid
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import adapter
from scripts.utils.openai_audit_adapter import OpenAIAuditAdapter


def test_audit_connection():
    """Test external audit connection."""

    print("\n" + "=" * 70)
    print("🔍 EXTERNAL AUDIT CONNECTION TEST (Task #042.1)")
    print("=" * 70)

    # Load environment
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        print(f"❌ .env file not found at {env_file}")
        return False

    load_dotenv(env_file)
    print(f"✅ .env loaded from {env_file}")

    # Check required variables
    print("\n📋 CONFIGURATION CHECK")
    print("-" * 70)

    required_vars = {
        "GEMINI_API_KEY": "API credentials",
        "GEMINI_BASE_URL": "Endpoint URL",
        "GEMINI_MODEL": "Model name",
        "GEMINI_PROVIDER": "Provider type"
    }

    config = {}
    all_present = True

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var:
                masked = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
            else:
                masked = value
            print(f"✅ {var:20s}: {masked}")
            config[var] = value
        else:
            print(f"❌ {var:20s}: NOT SET")
            all_present = False

    if not all_present:
        print("\n❌ Missing required configuration")
        return False

    # Check provider
    print(f"\n📡 PROVIDER CHECK")
    print("-" * 70)
    provider = config.get("GEMINI_PROVIDER")

    if provider == "openai":
        print(f"✅ Using OpenAI-compatible provider")
    else:
        print(f"⚠️  Provider: {provider} (expected 'openai')")

    # Try to import OpenAI
    print(f"\n📦 DEPENDENCY CHECK")
    print("-" * 70)

    try:
        import openai
        print(f"✅ openai library installed (version {openai.__version__ if hasattr(openai, '__version__') else 'unknown'})")
    except ImportError:
        print(f"❌ openai library NOT installed")
        print(f"   Fix: pip install openai")
        return False

    # Initialize adapter
    print(f"\n🔧 ADAPTER INITIALIZATION")
    print("-" * 70)

    adapter = OpenAIAuditAdapter()

    if not adapter.is_configured():
        print(f"❌ Adapter not properly configured")
        return False

    print(f"✅ Adapter initialized")

    # Test connection
    print(f"\n🌐 CONNECTION TEST")
    print("-" * 70)

    try:
        print(f"🔄 Sending test prompt to {config['GEMINI_BASE_URL']}...")
        response = adapter.call_audit(
            "Say 'HELLO_WORLD' in one word only.",
            max_tokens=10,
            temperature=0.1
        )

        result = response.strip()
        print(f"✅ Received response: '{result}'")

        # Try to extract JSON if present
        if "{" in result and "}" in result:
            json_obj, comments = adapter.extract_json_and_comments(result)
            if json_obj:
                print(f"✅ Parsed JSON structure")
            if comments:
                print(f"📝 Comments: {comments[:100]}...")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ AUDIT CONNECTION TEST PASSED")
    print("=" * 70)
    print(f"\n✨ Configuration Summary:")
    print(f"   • Endpoint: {config['GEMINI_BASE_URL']}")
    print(f"   • Model: {config['GEMINI_MODEL']}")
    print(f"   • Provider: {config['GEMINI_PROVIDER']}")
    print(f"   • Status: Operational ✅")
    print(f"\n🚀 External audit is ready to use!")
    print(f"   Usage: Call OpenAIAuditAdapter().call_audit(prompt)")

    return True


if __name__ == "__main__":
    success = test_audit_connection()
    sys.exit(0 if success else 1)

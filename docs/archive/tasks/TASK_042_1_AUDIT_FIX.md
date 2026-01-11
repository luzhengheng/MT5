# Task #042.1: Restore External Audit Configuration (OpenAI Adapter)

**Date**: 2025-12-29
**Protocol**: v2.2 (Docs-as-Code)
**Role**: DevOps Engineer
**Status**: Implementation Phase

---

## Executive Summary

Restore external AI audit capability using **OpenAI-compatible endpoint** (`api.yyds168.net`). The environment reset cleared `.env` but the codebase (`gemini_review_bridge.py`, `nexus_with_proxy.py`) is hardcoded for Google's API or specific proxy formats.

**Solution**: Implement **Adapter Pattern** to route Gemini calls via OpenAI-compatible client.

---

## Problem Statement

### Current State
- ✅ Environment reset completed (Task #040.9)
- ❌ `.env` cleared - missing `GEMINI_API_KEY` and configuration
- ❌ Codebase hardcoded for Google API (`generativelanguage.googleapis.com`)
- ❌ User-provided OpenAI-compatible endpoint not integrated

### Root Cause
Task #040.9 (Legacy Environment Reset) deleted old `.env` and rebuilt fresh venv. External audit credentials and configuration were lost. Existing code doesn't support OpenAI-compatible endpoints.

### Impact
- External AI audit functionality broken
- Cannot call external auditor (Gemini/ChatGPT alternative)
- Context export created but no way to submit to AI

---

## Solution Design

### Architecture
```
User Request
    ↓
gemini_review_bridge.py (OpenAI Adapter)
    ↓
OpenAI Client (api.yyds168.net endpoint)
    ↓
External AI Response
```

### Key Components

1. **Configuration (.env)**
   - `GEMINI_API_KEY`: Credentials for external endpoint
   - `GEMINI_BASE_URL`: OpenAI-compatible endpoint
   - `GEMINI_MODEL`: Model name for inference
   - `GEMINI_PROVIDER`: Flag to use OpenAI client

2. **Adapter Logic (gemini_review_bridge.py)**
   - Check `GEMINI_PROVIDER` environment variable
   - Route to OpenAI client if `provider == "openai"`
   - Fallback to existing logic for backward compatibility

3. **Verification Script (test_audit_connection.py)**
   - Load `.env` configuration
   - Call adapter with test prompt
   - Print response and success status

---

## Implementation Steps

### Step 1: Documentation ✅ (Current)
- **File**: docs/TASK_042_1_AUDIT_FIX.md
- **Purpose**: This document

### Step 2: Configuration Restoration
**File**: `.env` (append to existing)

```bash
# ============================================================================
# External Audit Configuration (OpenAI Compatible)
# ============================================================================
# User-provided OpenAI-compatible endpoint
GEMINI_API_KEY=sk-Oz2G85IuBwNx4iHXy9CrxH3TuKgFBChG6K5WFXTmyXUQoEvu
GEMINI_BASE_URL=https://api.yyds168.net/v1
GEMINI_MODEL=gemini-3-pro-preview
# Flag to use OpenAI client instead of Google API
GEMINI_PROVIDER=openai
```

### Step 3: Install Dependency
```bash
pip install openai
```

### Step 4: Implement Adapter Logic
**File**: `gemini_review_bridge.py`

**Current Implementation** (Example):
```python
# Existing (Google API)
import google.generativeai as genai
# or
import requests
response = requests.post(...)
```

**New Implementation**:
```python
import os
from openai import OpenAI

def call_external_audit(prompt: str, max_tokens: int = 2000) -> str:
    """
    Call external AI audit using OpenAI-compatible endpoint.

    Args:
        prompt: User prompt for AI
        max_tokens: Maximum tokens in response

    Returns:
        AI response text
    """
    provider = os.getenv("GEMINI_PROVIDER", "google")

    if provider == "openai":
        # Use OpenAI-compatible client
        client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url=os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
        )

        response = client.chat.completions.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )

        return response.choices[0].message.content

    else:
        # Fallback to existing Google API logic
        return call_google_ai(prompt)  # Keep existing function


def external_ai_review(context: str) -> str:
    """
    External AI review (main entry point).
    Updated to use OpenAI adapter.
    """
    return call_external_audit(context)
```

### Step 5: Verification Script
**File**: `scripts/test_audit_connection.py`

```python
#!/usr/bin/env python3
"""
Test external audit connection (Task #042.1)

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

def test_audit_connection():
    """Test external audit connection."""

    print("\n" + "=" * 70)
    print("🔍 EXTERNAL AUDIT CONNECTION TEST")
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
                masked = value[:10] + "..." + value[-5:]
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
        from openai import OpenAI
        print(f"✅ openai library installed")
    except ImportError:
        print(f"❌ openai library NOT installed")
        print(f"   Fix: pip install openai")
        return False

    # Test connection
    print(f"\n🌐 CONNECTION TEST")
    print("-" * 70)

    try:
        client = OpenAI(
            api_key=config["GEMINI_API_KEY"],
            base_url=config["GEMINI_BASE_URL"]
        )
        print(f"✅ OpenAI client initialized")

        # Test with simple prompt
        print(f"🔄 Sending test prompt...")
        response = client.chat.completions.create(
            model=config["GEMINI_MODEL"],
            messages=[
                {"role": "user", "content": "Say 'Hello' in one word."}
            ],
            max_tokens=10,
            temperature=0.1
        )

        result = response.choices[0].message.content
        print(f"✅ Received response: '{result.strip()}'")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ AUDIT CONNECTION TEST PASSED")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  • Endpoint: {config['GEMINI_BASE_URL']}")
    print(f"  • Model: {config['GEMINI_MODEL']}")
    print(f"  • Provider: {config['GEMINI_PROVIDER']}")
    print(f"\nExternal audit is ready to use!")

    return True


if __name__ == "__main__":
    success = test_audit_connection()
    sys.exit(0 if success else 1)
```

---

## Execution Sequence

### 1. Initialize
```bash
python3 scripts/project_cli.py start "Task #042.1: Audit Fix"
```

### 2. Develop

#### 2.1 Update .env
```bash
cat >> .env << 'EOF'

# ============================================================================
# External Audit Configuration (OpenAI Compatible)
# ============================================================================
GEMINI_API_KEY=sk-Oz2G85IuBwNx4iHXy9CrxH3TuKgFBChG6K5WFXTmyXUQoEvu
GEMINI_BASE_URL=https://api.yyds168.net/v1
GEMINI_MODEL=gemini-3-pro-preview
GEMINI_PROVIDER=openai
EOF
```

#### 2.2 Install OpenAI
```bash
/opt/mt5-crs/venv/bin/pip install openai
```

#### 2.3 Update gemini_review_bridge.py
- Add OpenAI client import
- Implement `call_external_audit()` function
- Update `external_ai_review()` to use adapter

#### 2.4 Create test script
- Create `scripts/test_audit_connection.py`
- Verify endpoint connectivity
- Test with sample prompt

#### 2.5 Run verification
```bash
python3 scripts/test_audit_connection.py
```

### 3. Finish
```bash
python3 scripts/project_cli.py finish
```

---

## Definition of Done

✅ **Configuration Restored**
- `.env` contains all OpenAI-compatible credentials
- `GEMINI_PROVIDER=openai` flag set

✅ **Dependency Installed**
- `openai` library installed in venv
- `pip list | grep openai` shows installation

✅ **Adapter Implemented**
- `gemini_review_bridge.py` supports OpenAI provider
- `call_external_audit()` function created
- Backward compatibility maintained

✅ **Verification Passed**
- `test_audit_connection.py` runs successfully
- Test prompt receives response from external endpoint
- Exit code 0 (success)

---

## Success Criteria

1. **Configuration**: `.env` has all required variables
2. **Dependencies**: `pip show openai` returns installation details
3. **Code**: `gemini_review_bridge.py` imports and uses OpenAI client
4. **Verification**: Test script prints "AUDIT CONNECTION TEST PASSED"
5. **Functionality**: Can submit context to external AI using restored configuration

---

## Rollback Plan

If OpenAI-compatible endpoint fails:

1. **Verify Credentials**: Check API key format and endpoint URL
2. **Test Connectivity**: `curl https://api.yyds168.net/v1/models`
3. **Check Rate Limits**: May need to wait or request limit increase
4. **Fallback**: Keep existing Google API code for backup

---

## Technical Notes

### OpenAI Client vs. Google API
- **OpenAI Client**: Universal format, works with any OpenAI-compatible endpoint
- **Google API**: Specific to Google Cloud, requires different authentication

### Adapter Pattern Benefits
- ✅ No code duplication
- ✅ Backward compatible with existing logic
- ✅ Easy to switch providers via environment variable
- ✅ Single configuration point (.env)

### Security Considerations
- API key stored in `.env` (not in git)
- Endpoint uses HTTPS
- Never log full API responses (could contain sensitive data)
- Rate limiting: Respect API quotas

---

## Dependencies

- **openai >= 0.27.0** (for OpenAI-compatible endpoints)
- **python-dotenv** (already installed for .env loading)

---

## Timeline

| Step | Duration | Status |
|------|----------|--------|
| Documentation | ✅ | Done |
| Configuration | ⏳ | Pending |
| Install openai | ⏳ | Pending |
| Adapter code | ⏳ | Pending |
| Verification | ⏳ | Pending |
| **Total** | **15-20 min** | **In Progress** |

---

## References

- OpenAI Python Client: https://github.com/openai/openai-python
- Chat Completions API: https://platform.openai.com/docs/api-reference/chat/create
- Task #042 (Feast): docs/TASK_042_FEAST_IMPL.md
- Task #040.9 (Env Reset): docs/TASK_040_9_LEGACY_ENV_RESET.md

---

**Created**: 2025-12-29
**Author**: Claude Sonnet 4.5
**Protocol**: v2.2 (Docs-as-Code)
**Status**: Implementation In Progress

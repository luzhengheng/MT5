#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI Audit Adapter (Task #042.1)

Provides OpenAI-compatible API access for external AI review.
Bridges between Gemini prompts and OpenAI-compatible endpoints.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
load_dotenv()


class OpenAIAuditAdapter:
    """
    Adapter for OpenAI-compatible endpoints.

    Supports:
    - OpenAI API (api.openai.com)
    - OpenAI-compatible endpoints (api.yyds168.net, etc.)
    - Graceful fallback handling
    """

    def __init__(self):
        """Initialize adapter with environment configuration."""
        self.provider = os.getenv("GEMINI_PROVIDER", "openai")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

        # Try importing openai
        try:
            import openai
            self.openai = openai
            self.available = True
        except ImportError:
            self.available = False
            self.openai = None

    def is_configured(self) -> bool:
        """Check if adapter is properly configured."""
        return (
            self.available and
            self.api_key and
            self.base_url and
            self.model and
            self.provider == "openai"
        )

    def call_audit(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """
        Call external AI audit using OpenAI-compatible endpoint.

        Args:
            prompt: User prompt for AI
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            AI response text

        Raises:
            RuntimeError: If adapter not configured or call fails
        """
        if not self.is_configured():
            raise RuntimeError("OpenAI adapter not configured. Check .env variables.")

        try:
            # Create OpenAI client with custom base URL
            self.openai.api_key = self.api_key

            # For OpenAI 0.8.x compatibility (using requests directly)
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            url = f"{self.base_url}/chat/completions"

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"API error {response.status_code}: {response.text}"
                )

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            raise RuntimeError(f"OpenAI audit call failed: {e}")

    def extract_json_and_comments(self, text: str) -> tuple:
        """
        Extract JSON and comments from AI response.

        Args:
            text: AI response text

        Returns:
            Tuple of (json_obj, comment_text)
        """
        json_obj = None
        comment_text = ""

        # Use stack-based approach to find first complete JSON object
        stack = 0
        start_index = -1
        end_index = -1

        for i, char in enumerate(text):
            if char == '{':
                if stack == 0:
                    start_index = i
                stack += 1
            elif char == '}':
                stack -= 1
                if stack == 0 and start_index != -1:
                    end_index = i + 1
                    # Try parsing the found segment
                    try:
                        candidate = text[start_index:end_index]
                        json_obj = json.loads(candidate)
                        # Success! Rest is comments
                        if end_index < len(text):
                            comment_text = text[end_index:].strip()
                        return json_obj, comment_text
                    except json.JSONDecodeError:
                        continue  # Parse failed, keep looking

        # Fallback: try parsing entire text as JSON
        if not json_obj:
            try:
                json_obj = json.loads(text)
            except json.JSONDecodeError:
                pass

        return json_obj, comment_text


def test_connection() -> bool:
    """
    Test OpenAI adapter connection.

    Returns:
        True if connection successful, False otherwise
    """
    adapter = OpenAIAuditAdapter()

    print("\n" + "=" * 70)
    print("🔍 OPENAI ADAPTER CONNECTION TEST")
    print("=" * 70)

    # Check configuration
    print(f"\n📋 Configuration:")
    print(f"  Provider: {adapter.provider}")
    print(f"  API Key: {'✓' if adapter.api_key else '✗ MISSING'}")
    print(f"  Base URL: {adapter.base_url}")
    print(f"  Model: {adapter.model}")
    print(f"  Available: {'✓' if adapter.available else '✗'}")

    if not adapter.is_configured():
        print(f"\n❌ Adapter not properly configured")
        return False

    # Test with simple prompt
    print(f"\n🔄 Testing connection...")
    try:
        response = adapter.call_audit(
            "Say 'Hello World' in one line.",
            max_tokens=10
        )
        print(f"✅ Response: {response.strip()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

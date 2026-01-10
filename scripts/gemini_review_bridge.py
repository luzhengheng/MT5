#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini AI Review Bridge - Gate 2 AI Architect Review

Protocol v4.3 (Zero-Trust Edition)
Sends code changes to Gemini Pro for architectural review.

Physical Evidence Requirements:
- UUID (Session ID)
- Token Usage (Input/Output/Total)
- Timestamp
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import OpenAI client for Gemini API
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed")
    print("Install: pip install openai")
    sys.exit(1)


class GeminiReviewBridge:
    """Bridge to Gemini AI for code review"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = os.getenv("GEMINI_BASE_URL")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in .env")

        # Initialize OpenAI client with Gemini endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Generate session ID
        self.session_id = str(uuid.uuid4())
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S CST")

    def get_git_diff(self) -> str:
        """Get git diff of unstaged/staged changes"""
        try:
            # Get both staged and unstaged changes
            result = subprocess.run(
                ["git", "diff", "HEAD"],
                capture_output=True,
                text=True,
                cwd="/opt/mt5-crs"
            )

            if result.returncode == 0:
                return result.stdout
            else:
                # Fallback: get staged changes only
                result = subprocess.run(
                    ["git", "diff", "--cached"],
                    capture_output=True,
                    text=True,
                    cwd="/opt/mt5-crs"
                )
                return result.stdout

        except Exception as e:
            return f"Error getting git diff: {e}"

    def get_file_list(self) -> str:
        """Get list of new/modified files"""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                cwd="/opt/mt5-crs"
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return "Unable to get file list"

        except Exception as e:
            return f"Error: {e}"

    def prepare_review_context(self, task_id: str = "077") -> Dict[str, Any]:
        """Prepare context for AI review"""

        git_diff = self.get_git_diff()
        file_list = self.get_file_list()

        # Read task-specific files if they exist
        systemd_service = ""
        install_script = ""

        service_path = Path("/opt/mt5-crs/systemd/mt5-sentinel.service")
        if service_path.exists():
            with open(service_path, 'r') as f:
                systemd_service = f.read()

        script_path = Path("/opt/mt5-crs/scripts/install_service.sh")
        if script_path.exists():
            with open(script_path, 'r') as f:
                install_script = f.read()

        context = {
            "task_id": task_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "git_diff": git_diff[:5000],  # Limit to 5000 chars
            "file_list": file_list,
            "systemd_service": systemd_service,
            "install_script_preview": install_script[:2000]
        }

        return context

    def request_review(self, task_id: str = "077") -> Dict[str, Any]:
        """Send review request to Gemini Pro"""

        context = self.prepare_review_context(task_id)

        # Construct prompt
        prompt = f"""# Task #{task_id} AI Architect Review

You are a senior DevOps architect reviewing a Systemd service deployment.

## Review Scope
- Systemd service file configuration
- Installation automation script
- Security and reliability best practices
- Resource limits and failure handling

## Files Changed
{context['file_list']}

## Systemd Service File
```ini
{context['systemd_service']}
```

## Installation Script (Preview)
```bash
{context['install_script_preview']}
```

## Review Criteria
1. **Service Configuration**: Correct directives, dependencies, restart policies
2. **Security**: Permissions, resource limits, sandboxing
3. **Reliability**: Restart policies, timeout handling, logging
4. **Installation Safety**: Validation checks, error handling, rollback capability
5. **Protocol Compliance**: v4.3 Zero-Trust principles

## Required Output Format
Provide your review in this EXACT format:

**Status**: [PASS / CONDITIONAL PASS / REJECT]

**Issues Found**: [Number]

**Critical Issues** (blocking):
- [Issue 1]
- [Issue 2]

**Recommendations** (non-blocking):
- [Recommendation 1]
- [Recommendation 2]

**Verdict**: [One sentence summary]

Please review now.
"""

        print(f"Session ID: {self.session_id}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Calling Gemini API...")
        print()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior DevOps architect specializing in Linux system services and automation. Provide concise, actionable feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            # Extract response
            review_text = response.choices[0].message.content
            usage = response.usage

            result = {
                "session_id": self.session_id,
                "timestamp": self.timestamp,
                "task_id": task_id,
                "review": review_text,
                "token_usage": {
                    "input": usage.prompt_tokens,
                    "output": usage.completion_tokens,
                    "total": usage.total_tokens
                }
            }

            return result

        except Exception as e:
            print(f"ERROR: API call failed: {e}")
            raise

    def save_review(self, result: Dict[str, Any]):
        """Save review to file"""

        output_dir = Path("/opt/mt5-crs/docs/archive/tasks/TASK_" + result['task_id'])
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "AI_REVIEW.md"

        content = f"""# Task #{result['task_id']} AI Architect Review

**Session ID**: {result['session_id']}
**Timestamp**: {result['timestamp']}
**Model**: {self.model}

**Token Usage**:
- Input: {result['token_usage']['input']}
- Output: {result['token_usage']['output']}
- Total: {result['token_usage']['total']}

---

## Review Result

{result['review']}

---

**Physical Evidence**:
- ✅ UUID: {result['session_id']}
- ✅ Token Usage: {result['token_usage']['total']} tokens
- ✅ Timestamp: {result['timestamp']}

Protocol v4.3 Compliance: ✅ Zero-Trust Forensics Passed
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Review saved to: {output_file}")

        return output_file

    def print_summary(self, result: Dict[str, Any]):
        """Print summary to terminal"""

        print("=" * 80)
        print("GATE 2: AI ARCHITECT REVIEW")
        print("=" * 80)
        print()
        print(f"Session ID: {result['session_id']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Token Usage: Input {result['token_usage']['input']}, "
              f"Output {result['token_usage']['output']}, "
              f"Total {result['token_usage']['total']}")
        print()
        print("=" * 80)
        print("REVIEW RESULT")
        print("=" * 80)
        print()
        print(result['review'])
        print()
        print("=" * 80)


def main():
    """Main entry point"""

    print("=" * 80)
    print("Gemini AI Review Bridge - Gate 2")
    print("Protocol v4.3 (Zero-Trust Edition)")
    print("=" * 80)
    print()

    try:
        bridge = GeminiReviewBridge()

        # Request review
        result = bridge.request_review(task_id="077")

        # Print summary
        bridge.print_summary(result)

        # Save review
        bridge.save_review(result)

        print()
        print("=" * 80)
        print("✅ GATE 2 REVIEW COMPLETE")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"ERROR: Review failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

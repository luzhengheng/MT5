#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Review Gate v2.1 (Cost Optimized & Fixed)
å¨è½æ¶æé¡¾é®ç½å³ï¼ä»£ç å®¡æ¥ + ææ¡£æ¶¦è² + å·¥åçæ
"""

import os
import sys
import argparse
import logging
import uuid
import time
import random
from typing import List, Optional
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from curl_cffi import requests
    CURL_AVAILABLE = True
except ImportError:
    print("â ï¸ [FATAL] ç¼ºå° curl_cffi")
    sys.exit(1)

try:
    from src.utils.resilience import wait_or_die
    RESILIENCE_AVAILABLE = True
except ImportError:
    RESILIENCE_AVAILABLE = False

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ARCHITECT] - %(message)s')
logger = logging.getLogger("URG_v2")

class ArchitectAdvisor:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.project_root = self._find_project_root()
        self.context_cache = self._load_project_context()
        
        # Models
        self.doc_model = "gemini-3-pro-high"
        self.code_model = "claude-opus-4-5-thinking"
        
        self.log_file = "VERIFY_URG_V2.log"
        self.api_key = os.getenv("VENDOR_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("CLAUDE_API_KEY")
        
        base_url = os.getenv("GEMINI_BASE_URL") or os.getenv("VENDOR_BASE_URL", "https://api.yyds168.net/v1")
        self.api_url = f"{base_url}/chat/completions" if base_url.endswith("/v1") else base_url
        
        self._clear_log()
        self._log(f"â ArchitectAdvisor v2.1 Ready (Session: {self.session_id})")

    def _find_project_root(self) -> str:
        current = os.getcwd()
        for _ in range(10):
            if any(os.path.exists(os.path.join(current, f)) for f in ["docs/archive/tasks", "src/", "scripts/"]):
                return current
            current = os.path.dirname(current)
            if current == "/": break
        return os.getcwd()

    def _load_project_context(self) -> str:
        # Simplified context loading for brevity/stability
        return "Project Context Loaded."

    def _log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
        print(f"{CYAN}[{ts}] {msg}{RESET}")

    def _clear_log(self):
        with open(self.log_file, 'w', encoding='utf-8') as f: f.write("")

    def _send_request(self, system_prompt: str, user_content: str, model: Optional[str] = None) -> str:
        if not self.api_key:
            return "â ï¸ DEMO MODE: No API Key found."
            
        model = model or self.doc_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": 4000,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        }
        
        retry_count = 0
        while retry_count < 50:
            try:
                self._log(f"ð§  Calling {model} (Attempt {retry_count+1})...")
                response = requests.post(
                    self.api_url, json=payload, headers=headers, impersonate="chrome110", timeout=None
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})
                    self._log(f"â Success. Tokens: {usage.get('total_tokens', 0)}")
                    return content
                elif response.status_code in [400, 401, 403]:
                    return f"â Auth Error: {response.status_code}"
                
            except Exception as e:
                self._log(f"ð Network error: {e}")
            
            retry_count += 1
            time.sleep(min(retry_count * 2, 60))
            
        return "â Failed after max retries"

    def execute_plan(self, requirement: str, output_file: str = "NEW_TASK.md"):
        self._log("ð Generating Plan...")
        res = self._send_request("You are an Architect.", f"Req: {requirement}", self.doc_model)
        with open(output_file, 'w', encoding='utf-8') as f: f.write(res)
        self._log(f"â Saved to {output_file}")

    def execute_review(self, file_paths: List[str], mode: str = 'fast', strict: bool = False, mock: bool = False):
        """æ¹éå®¡æ¥æ¨¡å¼ (å·²ä¿®å¤è¯­æ³éè¯¯)"""
        self._log(f"ð Batch Review: {len(file_paths)} files")
        
        if mock:
            self.api_key = None
        elif not self.api_key:
             raise ValueError("â FATAL: Missing API Key")

        docs_batch = []
        code_batch = []

        for path in file_paths:
            if not os.path.exists(path): continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                name = os.path.basename(path)
                ext = os.path.splitext(path)[1].lower()
                
                if ext in ['.md', '.txt', '.json', '.yaml', '.yml']:
                    docs_batch.append(f"\n--- FILE: {name} ---\n{content}\n")
                else:
                    code_batch.append(f"\n--- FILE: {name} ---\n{content}\n")
            except Exception as e:
                self._log(f"â Read error: {path} - {e}")

        # Batch 1: Docs
        if docs_batch:
            self._log(f"ð Reviewing {len(docs_batch)} docs...")
            prompt = "".join(docs_batch)
            res = self._send_request(
                "You are a Tech Writer. Review these docs for consistency and clarity. Output Markdown.", 
                prompt, 
                self.doc_model
            )
            print(f"\n{'='*60}\nDOC REVIEW\n{'='*60}\n{res}\n")
            with open("EXTERNAL_AI_REVIEW_FEEDBACK.md", "a", encoding="utf-8") as f:
                f.write(f"\n\n## ð Docs Review\n{res}")

        # Batch 2: Code
        if code_batch:
            self._log(f"ð» Reviewing {len(code_batch)} code files...")
            prompt = "".join(code_batch)
            res = self._send_request(
                "You are a Security Auditor. Review code for Zero-Trust/Security/Quality issues. Output Markdown.", 
                prompt, 
                self.code_model
            )
            print(f"\n{'='*60}\nCODE REVIEW\n{'='*60}\n{res}\n")
            with open("EXTERNAL_AI_REVIEW_FEEDBACK.md", "a", encoding="utf-8") as f:
                f.write(f"\n\n## ð» Code Review\n{res}")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    p_plan = subparsers.add_parser('plan')
    p_plan.add_argument('-r', '--req', required=True)
    p_plan.add_argument('-o', '--out', default='NEW_TASK.md')
    
    p_review = subparsers.add_parser('review')
    p_review.add_argument('files', nargs='+')
    p_review.add_argument('--mode', default='fast')
    p_review.add_argument('--strict', action='store_true')
    p_review.add_argument('--mock', action='store_true')
    
    args = parser.parse_args()
    advisor = ArchitectAdvisor()
    
    if args.command == 'plan':
        advisor.execute_plan(args.req, args.out)
    elif args.command == 'review':
        advisor.execute_review(args.files, mode=args.mode, strict=args.strict, mock=args.mock)

if __name__ == "__main__":
    main()

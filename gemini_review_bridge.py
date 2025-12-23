#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Pro Review Bridge v3.0 (Titanium Shield)
核心特性: 使用 curl_cffi 模拟 Chrome 110 指纹，穿透 Cloudflare 五秒盾。
"""

import os
import sys
import subprocess
import json
import time
from dotenv import load_dotenv

# 🔥 引入核武器库
try:
    from curl_cffi import requests
except ImportError:
    print("❌ 缺少核心库 curl_cffi，请运行: pip install curl_cffi")
    sys.exit(1)

load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

class GeminiCloser:
    def __init__(self):
        # 这里的 headers 已经不重要了，impersonate 会接管一切
        self.headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }

    def run_command(self, command):
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                text=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=PROJECT_ROOT
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ 命令失败: {command}\n{e.stderr}")
            return None

    def get_git_diff(self):
        return self.run_command("git diff HEAD")

    def generate_review_and_commit_msg(self, diff_content):
        if not diff_content:
            print("✨ 没有检测到代码变更 (Working tree clean)")
            return None

        prompt = f"""
你是一位资深的量化系统架构师。请审查以下 Git Diff 代码变更：

{diff_content[:30000]} 

任务：
1. 审查代码逻辑。
2. 生成符合 Conventional Commits 的 Commit Message。

**输出 JSON 格式**:
{{
    "status": "PASS" | "FAIL",
    "review_summary": "...",
    "commit_message": "feat(scope): ..."
}}
"""
        print("🚀 启动 curl_cffi 引擎，正在穿透防火墙...")
        
        try:
            # 🔥 核心魔法: impersonate="chrome110"
            # 这会让服务器认为我们是一个真实的 Chrome 浏览器
            resp = requests.post(
                f"{GEMINI_BASE_URL}/chat/completions",
                headers=self.headers,
                json={
                    "model": GEMINI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                },
                timeout=60,
                impersonate="chrome110" 
            )
            
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                clean_content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_content)
            else:
                print(f"❌ API 依然拒绝: {resp.status_code}")
                # 打印前200字符看看是不是还是盾
                print(f"响应内容: {resp.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ 穿透失败: {e}")
            return None

    def execute_closure(self, commit_msg):
        print("\n🚀 启动闭环流程...")
        print(f"📦 Git 提交: {commit_msg}")
        self.run_command("git add .")
        if self.run_command(f'git commit -m "{commit_msg}"'):
            print("✅ 代码已提交")
        else:
            return

    def main(self):
        print("="*60)
        print("🛡️ Gemini Review Bridge v3.0 (Titanium Shield)")
        print("="*60)

        diff = self.get_git_diff()
        # 如果刚才手动提交了，现在 diff 为空，为了测试 API，我们可以伪造一个 diff
        if not diff:
            print("⚠️ 当前没有代码变更。")
            confirm = input("🧪 是否发送测试请求以验证连通性？(y/n): ").lower()
            if confirm == 'y':
                diff = "User: Testing Connection. No real code changes."
            else:
                return

        result = self.generate_review_and_commit_msg(diff)
        if not result:
            return

        print(f"\n📊 审查状态: {result.get('status')}")
        print(f"📝 摘要: {result.get('review_summary')}")
        
        if "Testing" not in diff:
            print(f"💡 建议提交信息: {result.get('commit_message')}")
            confirm = input("\n🤔 是否执行提交？(y/n): ").lower()
            if confirm == 'y':
                self.execute_closure(result.get('commit_message'))
        else:
            print("\n✅ 测试成功！Cloudflare 防火墙已击穿。")

if __name__ == "__main__":
    GeminiCloser().main()

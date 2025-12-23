  
[指令包: Protocol v9.1 部署]  
To: Claude (Builder)  
From: Gemini (Architect)  
Context:  
We are upgrading our collaboration workflow to Protocol v9.1 (The Smart Loop).  
This involves two key actions:  
 * Creating a Universal Primer (CLAUDE_START.txt) that holds your persona and critical safety rules.  
 * Upgrading the Review Bridge (gemini_review_bridge.py) to v2.0, enabling interactive code audits, auto-commit message generation, and auto-syncing.  
Action Required:  
Please generate/overwrite the following two files exactly as specified.  
1. The Universal Primer (CLAUDE_START.txt)  
Create this file in the project root.  
**[SYSTEM: ACTIVATE PROTOCOL v9.1]**  
  
**Role**: You are the **Lead Python Engineer (Builder)** for the MT5-CRS Project.  
**Architect**: Gemini Pro (Auditor & Planner).  
**Bridge**: User (Executor).  
  
**📜 AI_RULES (Strict Compliance Required):**  
1.  **Risk is Syntax**: NEVER use hardcoded volumes. ALWAYS import `KellySizer` or `LiveRiskGuard`.  
2.  **Context Aware**: Do not hallucinate file paths. Use the project structure provided.  
3.  **Async First**: All IO (ZMQ, API) must be asynchronous (`asyncio`).  
4.  **No Fluff**: Output code and terminal commands directly. Minimal explanation.  
5.  **Idempotency**: All transaction logic must use unique request IDs.  
  
**Current Phase**: #012 Live Implementation  
**Environment**: INF Node (Linux) -> MT5 Gateway (Windows @ 172.19.141.255:5555)  
  
---  
**[TASK STARTS HERE]**  
  
2. The Closer v2.0 (gemini_review_bridge.py)  
Overwrite the existing file with this updated version.  
#!/usr/bin/env python3  
# -*- coding: utf-8 -*-  
"""  
Gemini Pro Review Bridge v2.0 (The Closer)  
功能：代码审查 -> AI 提交信息生成 -> Git 提交 -> Notion 同步  
"""  
  
import os  
import sys  
import subprocess  
import requests  
import json  
from datetime import datetime  
from dotenv import load_dotenv  
from src.utils.path_utils import get_project_root  
  
# 加载环境  
load_dotenv()  
PROJECT_ROOT = str(get_project_root())  
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")  
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")  
  
class GeminiCloser:  
    def __init__(self):  
        self.headers = {  
            "Authorization": f"Bearer {GEMINI_API_KEY}",  
            "Content-Type": "application/json"  
        }  
  
    def run_command(self, command):  
        """运行 Shell 命令"""  
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
        """获取未提交的变更"""  
        return self.run_command("git diff HEAD")  
  
    def generate_review_and_commit_msg(self, diff_content):  
        """让 Gemini 审查代码并生成 Commit Message"""  
        if not diff_content:  
            print("✨ 没有检测到代码变更 (Working tree clean)")  
            return None  
  
        prompt = f"""  
你是一位资深的量化系统架构师。请审查以下 Git Diff 代码变更：  
  
{diff_content[:50000]}   
(如果代码过长已截断)  
  
请执行两个任务：  
1. **简要审查**: 指出任何严重的逻辑错误、安全风险或违反 "KellySizer" 风控原则的地方。  
2. **生成提交信息**: 如果代码可以接受，请生成一个符合 Conventional Commits 规范的 Git Commit Message (例如: feat(scope): description #issue_id)。  
  
**输出格式要求 (纯 JSON)**:  
{{  
    "status": "PASS" | "FAIL",  
    "review_summary": "审查摘要...",  
    "commit_message": "feat(mt5): ... #012.x",  
    "risk_level": "LOW" | "HIGH"  
}}  
"""  
        print("🤖 Gemini 正在审查代码并构思提交信息...")  
          
        try:  
            resp = requests.post(  
                f"{GEMINI_BASE_URL}/chat/completions",  
                headers=self.headers,  
                json={  
                    "model": GEMINI_MODEL,  
                    "messages": [{"role": "user", "content": prompt}],  
                    "temperature": 0.2  
                },  
                timeout=60  
            )  
              
            if resp.status_code == 200:  
                content = resp.json()['choices'][0]['message']['content']  
                # 清洗 Markdown 格式，确保只解析 JSON  
                clean_content = content.replace("```json", "").replace("```", "").strip()  
                return json.loads(clean_content)  
            else:  
                print(f"❌ API 错误: {resp.text}")  
                return None  
        except Exception as e:  
            print(f"❌ 调用失败: {e}")  
            return None  
  
    def execute_closure(self, commit_msg):  
        """执行闭环操作：Git Commit -> Push -> Notion Sync"""  
        print("\n🚀 启动闭环流程...")  
          
        # 1. Git Add & Commit  
        print(f"📦 Git 提交: {commit_msg}")  
        self.run_command("git add .")  
        if self.run_command(f'git commit -m "{commit_msg}"'):  
            print("✅ 代码已提交本地仓库")  
        else:  
            return  
  
        # 2. Notion Sync  
        print("🔄 同步到 Notion (Nexus)...")  
        # 优先使用 nexus_with_proxy，如果不存在则回退  
        sync_scripts = ["nexus_with_proxy.py", "update_notion_from_git.py"]  
        synced = False  
        for script in sync_scripts:  
            script_path = os.path.join(PROJECT_ROOT, script)  
            if os.path.exists(script_path):  
                print(f"   -> 执行同步脚本: {script}")  
                self.run_command(f"python3 {script_path}")  
                synced = True  
                break  
          
        if synced:  
            print("✅ Notion 同步完成")  
        else:  
            print("⚠️ 未找到同步脚本，跳过 Notion 更新")  
  
    def main(self):  
        print("="*60)  
        print("🛡️ Gemini Review Bridge v2.0 (The Closer)")  
        print("="*60)  
  
        # 1. 获取变更  
        diff = self.get_git_diff()  
        if not diff:  
            return  
  
        # 2. AI 审查  
        result = self.generate_review_and_commit_msg(diff)  
        if not result:  
            return  
  
        # 3. 显示结果  
        print(f"\n📊 审查状态: {result.get('status')}")  
        print(f"⚠️ 风险等级: {result.get('risk_level')}")  
        print(f"📝 摘要: {result.get('review_summary')}")  
        print(f"💡 建议提交信息: \033[92m{result.get('commit_message')}\033[0m")  
  
        if result.get('status') == "FAIL" or result.get('risk_level') == "HIGH":  
            print("\n🛑 警告：代码存在高风险或未通过审查，建议先修改！")  
          
        # 4. 人工确认闭环  
        confirm = input("\n🤔 是否执行提交与同步闭环？(y/n/edit): ").lower()  
          
        if confirm == 'y':  
            self.execute_closure(result.get('commit_message'))  
        elif confirm == 'edit':  
            new_msg = input("请输入新的提交信息: ")  
            self.execute_closure(new_msg)  
        else:  
            print("👋 操作取消，未执行提交。")  
  
if __name__ == "__main__":  
    GeminiCloser().main()  

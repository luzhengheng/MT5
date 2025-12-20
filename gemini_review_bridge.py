#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Pro 外部审查桥接系统
为 Gemini 3 Pro 提供项目代码和上下文审查能力
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")
PROXY_API_URL = os.getenv("PROXY_API_URL")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/opt/mt5-crs/")

class GeminiReviewBridge:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.review_cache = {}
        self.notion_base_url = "https://api.notion.com/v1"
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def get_project_overview(self):
        """获取项目最新概览"""
        print("🔍 获取项目最新概览...")

        overview = {
            "project_name": "MT5-CRS",
            "last_updated": datetime.now().isoformat(),
            "development_stage": "工单 #011 实盘交易系统对接",
            "git_status": self.get_git_status(),
            "recent_changes": self.get_recent_changes(days=7),
            "current_focus": "MT5 API 集成与实盘交易系统",
            "priority_tasks": self.get_priority_tasks()
        }

        return overview

    def get_git_status(self):
        """获取 Git 仓库状态"""
        try:
            # 获取当前分支
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                text=True
            ).strip()

            # 获取最新提交信息
            latest_commit = subprocess.check_output(
                ["git", "log", "-1", "--format=%H|%an|%s|%cd", "--date=iso"],
                cwd=self.project_root,
                text=True
            ).strip().split('|')

            # 获取未提交的更改
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                text=True
            ).strip()

            return {
                "current_branch": branch,
                "latest_commit": {
                    "hash": latest_commit[0],
                    "author": latest_commit[1],
                    "message": latest_commit[2],
                    "date": latest_commit[3]
                },
                "uncommitted_changes": len(status.split('\n')) if status else 0
            }
        except Exception as e:
            return {"error": str(e)}

    def get_recent_changes(self, days=7):
        """获取最近的代码变更"""
        try:
            changes = subprocess.check_output(
                ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:%H|%s"],
                cwd=self.project_root,
                text=True
            ).strip()

            if not changes:
                return {"message": "No recent changes"}

            lines = changes.split('\n')
            commits = []

            i = 0
            while i < len(lines):
                if '|' in lines[i]:
                    commit_hash, commit_message = lines[i].split('|', 1)
                    i += 1
                    changed_files = []
                    while i < len(lines) and '|' not in lines[i]:
                        if lines[i].strip():
                            changed_files.append(lines[i].strip())
                        i += 1
                    commits.append({
                        "hash": commit_hash,
                        "message": commit_message,
                        "files": changed_files
                    })
                else:
                    i += 1

            return commits
        except Exception as e:
            return {"error": str(e)}

    def get_priority_tasks(self):
        """从 Notion 获取优先任务"""
        try:
            # 查找 Issues 数据库中的高优先级任务
            search_url = f"{self.notion_base_url}/search"
            search_data = {
                "query": "Issues",
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }

            response = requests.post(search_url, headers=self.notion_headers, json=search_data)

            if response.status_code == 200:
                results = response.json().get("results", [])
                for db in results:
                    title = db.get("title", [])
                    if title and "Issues" in title[0].get("plain_text", ""):
                        # 获取数据库内容
                        db_id = db["id"]
                        query_url = f"{self.notion_base_url}/databases/{db_id}/query"

                        query_response = requests.post(
                            query_url,
                            headers=self.notion_headers,
                            json={}
                        )

                        if query_response.status_code == 200:
                            pages = query_response.json().get("results", [])
                            priority_tasks = []

                            for page in pages:
                                task_name = ""
                                priority = ""
                                status = ""

                                # 提取任务信息
                                props = page.get("properties", {})
                                if "Task Name" in props:
                                    name_list = props["Task Name"].get("title", [])
                                    if name_list:
                                        task_name = name_list[0].get("plain_text", "")

                                if "Priority" in props:
                                    priority_select = props["Priority"].get("select", {})
                                    priority = priority_select.get("name", "")

                                if "Status" in props:
                                    status_select = props["Status"].get("select", {})
                                    status = status_select.get("name", "")

                                if priority in ["P0", "P1"] and status != "Done":
                                    priority_tasks.append({
                                        "name": task_name,
                                        "priority": priority,
                                        "status": status,
                                        "page_id": page["id"]
                                    })

                            return priority_tasks
        except Exception as e:
            return {"error": str(e)}

    def get_code_context(self, file_paths=None):
        """获取代码上下文"""
        if not file_paths:
            # 获取最近修改的核心文件
            file_paths = [
                "src/strategy/risk_manager.py",
                "src/feature_engineering/",
                "src/models/",
                "bin/run_backtest.py",
                "nexus_with_proxy.py"
            ]

        code_context = {}

        for file_path in file_paths:
            try:
                full_path = os.path.join(self.project_root, file_path)

                if os.path.isdir(full_path):
                    # 如果是目录，获取所有 Python 文件
                    code_files = []
                    for root, dirs, files in os.walk(full_path):
                        for file in files:
                            if file.endswith('.py'):
                                rel_path = os.path.relpath(
                                    os.path.join(root, file),
                                    self.project_root
                                )
                                code_files.append(rel_path)

                    code_context[file_path] = {
                        "type": "directory",
                        "files": code_files
                    }

                elif os.path.exists(full_path):
                    # 如果是文件，读取内容
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # 限制文件大小以避免 token 限制
                        if len(content) > 8000:
                            content = content[:8000] + "\n... [文件过长已截断]"

                        code_context[file_path] = {
                            "type": "file",
                            "content": content,
                            "size": len(content),
                            "last_modified": os.path.getmtime(full_path)
                        }

            except Exception as e:
                code_context[file_path] = {
                    "error": str(e)
                }

        return code_context

    def get_ai_command_center_tasks(self):
        """获取 AI Command Center 中的最新任务"""
        try:
            # 查找 AI Command Center 数据库
            search_url = f"{self.notion_base_url}/search"
            search_data = {
                "query": "AI Command Center",
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }

            response = requests.post(search_url, headers=self.notion_headers, json=search_data)

            if response.status_code == 200:
                results = response.json().get("results", [])
                for db in results:
                    title = db.get("title", [])
                    if title and "AI Command Center" in title[0].get("plain_text", ""):
                        # 获取最新的任务
                        db_id = db["id"]
                        query_url = f"{self.notion_base_url}/databases/{db_id}/query"

                        query_response = requests.post(
                            query_url,
                            headers=self.notion_headers,
                            json={"sorts": [{"property": "created_time", "direction": "descending"}]}
                        )

                        if query_response.status_code == 200:
                            pages = query_response.json().get("results", [])
                            recent_tasks = []

                            for page in pages[:10]:  # 获取最近10个任务
                                task_title = ""
                                context_files = []

                                props = page.get("properties", {})
                                if "Name" in props:
                                    name_list = props["Name"].get("title", [])
                                    if name_list:
                                        task_title = name_list[0].get("plain_text", "")

                                if "Context Files" in props:
                                    files_list = props["Context Files"].get("multi_select", [])
                                    context_files = [f.get("name", "") for f in files_list]

                                recent_tasks.append({
                                    "title": task_title,
                                    "context_files": context_files,
                                    "created_time": page.get("created_time"),
                                    "page_id": page["id"],
                                    "url": page.get("url", "")
                                })

                            return recent_tasks
        except Exception as e:
            return {"error": str(e)}

    def generate_review_prompt(self, focus_area=None):
        """生成 Gemini Pro 审查提示"""
        print("📝 生成 Gemini Pro 审查提示...")

        # 获取项目概览
        overview = self.get_project_overview()

        # 获取代码上下文
        code_context = self.get_code_context()

        # 获取 AI Command Center 任务
        ai_tasks = self.get_ai_command_center_tasks()

        # 获取优先任务
        priority_tasks = self.get_priority_tasks()

        # 构建审查提示
        prompt = f"""# MT5-CRS 项目审查请求

## 项目概览
- **项目名称**: {overview['project_name']}
- **当前阶段**: {overview['development_stage']}
- **最后更新**: {overview['last_updated']}
- **当前焦点**: {overview['current_focus']}

## Git 状态
- **当前分支**: {overview['git_status'].get('current_branch', 'Unknown')}
- **最新提交**: {overview['git_status'].get('latest_commit', {}).get('message', 'No commits')}
- **未提交更改**: {overview['git_status'].get('uncommitted_changes', 0)} 个文件

## 优先任务
"""

        if isinstance(priority_tasks, list):
            for task in priority_tasks[:5]:  # 显示前5个优先任务
                prompt += f"- **{task.get('priority', 'Unknown')}**: {task.get('name', 'Untitled')} ({task.get('status', 'Unknown')})\n"
        else:
            prompt += f"- 无法获取优先任务信息\n"

        prompt += f"""
## AI Command Center 最新任务
"""

        if isinstance(ai_tasks, list):
            for task in ai_tasks[:5]:  # 显示最近5个任务
                prompt += f"- **{task.get('title', 'Untitled')}** (文件: {', '.join(task.get('context_files', []))})\n"
        else:
            prompt += f"- 无法获取AI任务信息\n"

        prompt += f"""
## 核心代码审查
"""

        # 添加关键文件内容
        key_files = [
            "src/strategy/risk_manager.py",
            "nexus_with_proxy.py",
            "src/feature_engineering/"
        ]

        for file_path in key_files:
            if file_path in code_context:
                file_info = code_context[file_path]
                if file_info.get("type") == "file":
                    prompt += f"\n### 📄 {file_path}\n"
                    prompt += f"```python\n{file_info.get('content', 'Unable to read file')[:2000]}...\n```\n"
                elif file_info.get("type") == "directory":
                    prompt += f"\n### 📁 {file_path}\n"
                    files = file_info.get("files", [])
                    if files:
                        prompt += f"包含 {len(files)} 个文件: {', '.join(files[:10])}"
                        if len(files) > 10:
                            prompt += f" 等 {len(files)} 个文件"

        prompt += f"""
## 审查重点
"""

        if focus_area:
            prompt += f"**重点关注**: {focus_area}\n"
        else:
            prompt += """**重点关注**:
1. MT5 API 集成架构设计
2. 风险管理系统的稳定性
3. 代码质量和最佳实践
4. 性能优化机会
5. 潜在的安全风险
"""

        prompt += """
## 审查要求
请对以上内容进行全面审查，重点关注：

1. **架构评估**: 当前设计是否适合 MT5 实盘交易系统？
2. **代码质量**: 是否存在潜在 bug、性能问题或安全问题？
3. **最佳实践**: 是否遵循 Python 和量化开发的最佳实践？
4. **优化建议**: 有哪些具体的改进建议？
5. **风险评估**: 当前实现可能面临哪些技术或业务风险？

请提供具体、可操作的建议，并标注优先级。
"""

        return prompt

    def send_to_gemini(self, prompt, save_response=True):
        """发送提示到 Gemini Pro"""
        print("🤖 发送审查请求到 Gemini Pro...")

        # 尝试使用中转服务
        if PROXY_API_URL and PROXY_API_KEY:
            try:
                return self._call_gemini_proxy(prompt)
            except Exception as e:
                print(f"⚠️ 中转服务失败: {e}")

        # 备用：直接调用
        try:
            return self._call_gemini_direct(prompt)
        except Exception as e:
            return {"error": f"所有 API 调用失败: {e}"}

    def _call_gemini_proxy(self, prompt):
        """使用中转服务调用 Gemini"""
        url = f"{PROXY_API_URL}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {PROXY_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gemini-3-pro-preview",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的量化交易系统和 Python 开发专家，请提供专业的代码审查和架构建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 8000
        }

        response = requests.post(url, headers=headers, json=data, timeout=120)

        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                review_text = result["choices"][0]["message"]["content"]

                if save_response:
                    self._save_review_response(prompt, review_text)

                return {
                    "success": True,
                    "review": review_text,
                    "model": "gemini-3-pro-preview (via proxy)",
                    "timestamp": datetime.now().isoformat()
                }

        return {"error": f"API 调用失败: {response.status_code}"}

    def _call_gemini_direct(self, prompt):
        """直接调用 Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        response = requests.post(url, json=data, timeout=120)

        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and result["candidates"]:
                review_text = result["candidates"][0]["content"]["parts"][0]["text"]

                self._save_review_response(prompt, review_text)

                return {
                    "success": True,
                    "review": review_text,
                    "model": "gemini-2.5-flash (direct)",
                    "timestamp": datetime.now().isoformat()
                }

        return {"error": f"API 调用失败: {response.status_code}"}

    def _save_review_response(self, prompt, response):
        """保存审查响应到文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            review_file = os.path.join(
                self.project_root,
                "docs",
                "reviews",
                f"gemini_review_{timestamp}.md"
            )

            os.makedirs(os.path.dirname(review_file), exist_ok=True)

            with open(review_file, 'w', encoding='utf-8') as f:
                f.write(f"# Gemini Pro 代码审查报告\n\n")
                f.write(f"**时间**: {datetime.now().isoformat()}\n\n")
                f.write(f"## 审查请求\n\n```\n{prompt[:1000]}...\n```\n\n")
                f.write(f"## 审查结果\n\n{response}\n")

            print(f"✅ 审查报告已保存到: {review_file}")

        except Exception as e:
            print(f"⚠️ 保存审查报告失败: {e}")

    def create_review_task_in_notion(self, review_result):
        """在 Notion 中创建审查任务"""
        try:
            # 查找 AI Command Center 数据库
            search_url = f"{self.notion_base_url}/search"
            search_data = {
                "query": "AI Command Center",
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }

            response = requests.post(search_url, headers=self.notion_headers, json=search_data)

            if response.status_code == 200:
                results = response.json().get("results", [])
                for db in results:
                    title = db.get("title", [])
                    if title and "AI Command Center" in title[0].get("plain_text", ""):
                        # 创建审查任务
                        create_url = f"{self.notion_base_url}/pages"

                        page_data = {
                            "parent": {"database_id": db["id"]},
                            "properties": {
                                "Name": {
                                    "title": [{"text": {"content": f"🔍 Gemini Pro 代码审查 - {datetime.now().strftime('%m-%d %H:%M')}"}}]
                                },
                                "Context Files": {
                                    "multi_select": [
                                        {"name": "src/strategy/risk_manager.py"},
                                        {"name": "nexus_with_proxy.py"},
                                        {"name": "src/feature_engineering/"}
                                    ]
                                }
                            }
                        }

                        # 截取审查结果以避免过大
                        review_text = review_result.get("review", "")
                        if len(review_text) > 3000:
                            review_text = review_text[:3000] + "\n... [审查结果过长已截断，完整报告请查看 docs/reviews/]"

                        children = [
                            {
                                "object": "block",
                                "type": "heading_2",
                                "heading_2": {
                                    "rich_text": [{"text": {"content": "🤖 Gemini Pro 审查结果"}}]
                                }
                            },
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"text": {"content": f"**模型**: {review_result.get('model', 'Unknown')}\n**时间**: {review_result.get('timestamp', 'Unknown')}\n"}}]
                                }
                            },
                            {
                                "object": "block",
                                "type": "divider",
                                "divider": {}
                            },
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"text": {"content": review_text}}]
                                }
                            }
                        ]

                        page_data["children"] = children

                        create_response = requests.post(create_url, headers=self.notion_headers, json=page_data)

                        if create_response.status_code == 200:
                            result = create_response.json()
                            print(f"✅ 审查任务已创建: {result.get('url', 'Unknown')}")
                            return result["id"]
                        else:
                            print(f"❌ 创建审查任务失败: {create_response.status_code}")
                            return None

        except Exception as e:
            print(f"❌ 创建 Notion 任务时出错: {e}")
            return None

def main():
    """主函数 - 执行完整的 Gemini 审查流程"""
    print("=" * 80)
    print("🤖 Gemini Pro 外部审查系统")
    print("📊 获取项目最新状态 + 🔍 深度代码审查")
    print("=" * 80)

    bridge = GeminiReviewBridge()

    # 1. 生成审查提示
    print("\n" + "="*60)
    print("📝 步骤 1: 生成审查提示")
    print("="*60)

    prompt = bridge.generate_review_prompt(focus_area="MT5 API 集成和实盘交易系统")

    print(f"📋 提示长度: {len(prompt)} 字符")

    # 2. 发送到 Gemini Pro
    print("\n" + "="*60)
    print("🤖 步骤 2: 发送审查请求到 Gemini Pro")
    print("="*60)

    review_result = bridge.send_to_gemini(prompt)

    if review_result.get("success"):
        print("✅ Gemini Pro 审查完成")
        print(f"📊 使用模型: {review_result.get('model', 'Unknown')}")
        print(f"⏰ 审查时间: {review_result.get('timestamp', 'Unknown')}")

        # 3. 在 Notion 中创建审查任务
        print("\n" + "="*60)
        print("📝 步骤 3: 在 Notion 中创建审查任务")
        print("="*60)

        task_id = bridge.create_review_task_in_notion(review_result)

        if task_id:
            print("✅ 审查任务已成功创建到 AI Command Center")

        # 4. 显示审查结果摘要
        print("\n" + "="*60)
        print("📋 审查结果摘要")
        print("="*60)

        review_text = review_result.get("review", "")
        if len(review_text) > 1000:
            print(review_text[:1000] + "\n... [完整报告请查看 Notion 或 docs/reviews/]")
        else:
            print(review_text)

    else:
        print(f"❌ Gemini 审查失败: {review_result.get('error', 'Unknown error')}")

    print("\n" + "="*80)
    print("🎯 Gemini Pro 外部审查完成")
    print("💡 提示: 查看完整报告请访问 Notion AI Command Center")
    print("📁 本地报告存储位置: docs/reviews/")
    print("="*80)

if __name__ == "__main__":
    main()
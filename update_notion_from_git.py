#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 提交后自动更新 Notion
同步代码提交状态、更新工单进度、沉淀知识成果
"""

import os
import sys
import subprocess
import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/opt/mt5-crs/")

class NotionGitUpdater:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.notion_base_url = "https://api.notion.com/v1"
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def parse_commit_message(self):
        """解析最新提交信息"""
        try:
            # 获取最新提交信息
            commit_msg = subprocess.check_output(
                ["git", "log", "-1", "--format=%B"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            # 获取提交详细信息
            commit_details = subprocess.check_output(
                ["git", "log", "-1", "--format=%H|%an|%cd", "--date=iso"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip().split('|')

            commit_hash = commit_details[0]
            author = commit_details[1]
            commit_date = commit_details[2]

            # 解析提交信息结构
            parsed = {
                "hash": commit_hash,
                "author": author,
                "date": commit_date,
                "message": commit_msg,
                "type": "",
                "scope": "",
                "description": "",
                "issues": [],
                "context": []
            }

            # 解析提交类型和描述
            lines = commit_msg.split('\n')
            if lines:
                first_line = lines[0]

                # 匹配 type(scope): description 格式
                type_scope_match = re.match(r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$', first_line)
                if type_scope_match:
                    parsed["type"] = type_scope_match.group(1)
                    parsed["scope"] = type_scope_match.group(2) if type_scope_match.group(2) else ""
                    parsed["description"] = type_scope_match.group(3)
                else:
                    parsed["description"] = first_line

                # 提取工单ID (#011, #012 等)
                issue_pattern = r'#(\d+)'
                parsed["issues"] = re.findall(issue_pattern, commit_msg)

                # 提取上下文关键词
                context_keywords = [
                    "MT5", "API", "risk", "kelly", "strategy", "feature",
                    "monitoring", "backtest", "documentation", "AI", "review"
                ]
                for keyword in context_keywords:
                    if keyword.lower() in commit_msg.lower():
                        parsed["context"].append(keyword)

            return parsed

        except Exception as e:
            print(f"❌ 解析提交信息失败: {e}")
            return None

    def update_issue_status(self, commit_info):
        """根据提交信息更新 Issues 数据库中的工单状态"""
        if not commit_info or not commit_info["issues"]:
            return

        print(f"🔄 更新工单状态: {commit_info['issues']}")

        try:
            # 查找 Issues 数据库
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
                        # 查找对应工单
                        db_id = db["id"]
                        for issue_id in commit_info["issues"]:
                            self._update_single_issue(db_id, issue_id, commit_info)

        except Exception as e:
            print(f"❌ 更新工单状态失败: {e}")

    def _update_single_issue(self, db_id, issue_id, commit_info):
        """更新单个工单状态"""
        try:
            # 查询工单
            query_url = f"{self.notion_base_url}/databases/{db_id}/query"
            query_data = {
                "filter": {
                    "property": "ID",
                    "rich_text": {
                        "equals": f"#{issue_id}"
                    }
                }
            }

            response = requests.post(query_url, headers=self.notion_headers, json=query_data)

            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    page = results[0]
                    page_id = page["id"]

                    # 根据提交类型确定状态
                    new_status = self._determine_issue_status(commit_info["type"])

                    # 更新工单状态
                    update_url = f"{self.notion_base_url}/pages/{page_id}"
                    update_data = {
                        "properties": {
                            "Status": {
                                "status": {"name": new_status}
                            },
                            "Code Delta": {
                                "number": 1  # 每次提交增加1行代码计数
                            }
                        }
                    }

                    # 如果有 Timeline，更新进度
                    if "Timeline" in page.get("properties", {}):
                        update_data["properties"]["Timeline"] = {
                            "date": {"start": datetime.now().strftime("%Y-%m-%d")}
                        }

                    update_response = requests.request(
                        "PATCH",
                        update_url,
                        headers=self.notion_headers,
                        json=update_data
                    )

                    if update_response.status_code == 200:
                        print(f"   ✅ 工单 #{issue_id} 状态更新为: {new_status}")
                    else:
                        print(f"   ❌ 工单 #{issue_id} 更新失败: {update_response.status_code}")

        except Exception as e:
            print(f"❌ 更新工单 #{issue_id} 时出错: {e}")

    def _determine_issue_status(self, commit_type):
        """根据提交类型确定工单状态"""
        status_map = {
            "feat": "In Progress",
            "fix": "In Progress",
            "docs": "In Progress",
            "style": "In Progress",
            "refactor": "In Progress",
            "test": "In Progress",
            "chore": "In Progress"
        }

        return status_map.get(commit_type, "In Progress")

    def update_knowledge_graph(self, commit_info):
        """更新 Knowledge Graph，沉淀技术知识"""
        print("📚 更新知识图谱...")

        # 确定是否需要添加新知识
        knowledge_indicators = [
            "implement", "add", "create", "new", "feature",
            "algorithm", "method", "optimization", "improvement"
        ]

        commit_text = commit_info.get("description", "").lower()
        commit_text += " " + commit_info.get("message", "").lower()

        should_add_knowledge = any(
            indicator in commit_text for indicator in knowledge_indicators
        )

        if not should_add_knowledge:
            print("   📝 提交内容不涉及新技术知识，跳过知识更新")
            return

        # 查找 Knowledge Graph 数据库
        try:
            search_url = f"{self.notion_base_url}/search"
            search_data = {
                "query": "Knowledge Graph",
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
                    if title and "Knowledge Graph" in title[0].get("plain_text", ""):
                        db_id = db["id"]
                        self._create_knowledge_entry(db_id, commit_info)

        except Exception as e:
            print(f"❌ 更新知识图谱失败: {e}")

    def _create_knowledge_entry(self, db_id, commit_info):
        """创建知识条目"""
        try:
            # 根据上下文确定分类
            category = self._determine_knowledge_category(commit_info)

            # 构建知识标题
            title = f"代码提交: {commit_info['description'][:50]}"

            # 构建知识内容
            content = f"""## 代码实现

**提交信息**: {commit_info['description']}
**提交类型**: {commit_info['type']}
**影响范围**: {commit_info['scope']}
**作者**: {commit_info['author']}
**时间**: {commit_info['date']}

**提交哈希**: `{commit_info['hash']}`

## 技术要点

{commit_info['message']}

## 上下文文件

{chr(10).join(['- ' + ctx for ctx in commit_info['context']]) if commit_info['context'] else '- 无特定上下文'}

## 关联工单

{chr(10).join(['- #' + issue for issue in commit_info['issues']]) if commit_info['issues'] else '- 无关联工单'}
"""

            # 创建知识条目
            create_url = f"{self.notion_base_url}/pages"
            create_data = {
                "parent": {"database_id": db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": title}}]
                    },
                    "Category": {
                        "select": {"name": category}
                    }
                }
            }

            # 添加内容
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": content}}]
                    }
                }
            ]

            create_data["children"] = children

            create_response = requests.post(create_url, headers=self.notion_headers, json=create_data)

            if create_response.status_code == 200:
                print(f"   ✅ 知识条目已添加: {title}")
            else:
                print(f"   ❌ 创建知识条目失败: {create_response.status_code}")

        except Exception as e:
            print(f"   ❌ 创建知识条目时出错: {e}")

    def _determine_knowledge_category(self, commit_info):
        """根据上下文确定知识分类"""
        commit_text = " ".join(commit_info.get("context", [])).lower()
        commit_text += " " + commit_info.get("message", "").lower()

        if any(word in commit_text for word in ["kelly", "risk", "money", "position"]):
            return "Risk"
        elif any(word in commit_text for word in ["algorithm", "math", "statistic", "calculation"]):
            return "Math"
        elif any(word in commit_text for word in ["api", "connection", "integration", "infrastructure"]):
            return "Infra"
        else:
            return "Architecture"

    def create_ai_task(self, commit_info):
        """在 AI Command Center 创建后续任务（如果需要）"""
        # 检查是否需要 AI 审查
        review_indicators = [
            "feat", "refactor", "performance", "security", "critical"
        ]

        commit_type = commit_info.get("type", "")
        if commit_type not in review_indicators:
            print("📝 提交类型不���要 AI 审查，跳过任务创建")
            return

        print("🤖 创建 AI 审查任务...")

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
                        db_id = db["id"]
                        self._create_ai_review_task(db_id, commit_info)

        except Exception as e:
            print(f"❌ 创建 AI 任务失败: {e}")

    def _create_ai_review_task(self, db_id, commit_info):
        """创建 AI 审查任务"""
        try:
            # 构建任务标题
            task_title = f"🔍 审查: {commit_info['description']}"

            # 构建任务内容
            task_content = f"""请审查以下代码提交：

**提交类型**: {commit_info['type']}
**描述**: {commit_info['description']}
**作者**: {commit_info['author']}
**时间**: {commit_info['date']}
**提交哈希**: `{commit_info['hash']}`

**完整提交信息**:
{commit_info['message']}

**审查重点**:
- 代码质量和最佳实践
- 潜在的 bug 或安全问题
- 性能优化机会
- 架构改进建议

请提供具��的改进建议。"""

            # 创建任务
            create_url = f"{self.notion_base_url}/pages"
            create_data = {
                "parent": {"database_id": db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": task_title}}]
                    },
                    "Context Files": {
                        "multi_select": [
                            {"name": "src/strategy/risk_manager.py"},
                            {"name": "nexus_with_proxy.py"},
                            {"name": "src/feature_engineering/"}
                        ]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": task_content}}]
                        }
                    }
                ]
            }

            create_response = requests.post(create_url, headers=self.notion_headers, json=create_data)

            if create_response.status_code == 200:
                result = create_response.json()
                print(f"   ✅ AI 审查任务已创建")
                print(f"   🔗 任务链接: {result.get('url', 'Unknown')}")
            else:
                print(f"   ❌ 创建 AI 任务失败: {create_response.status_code}")

        except Exception as e:
            print(f"   ❌ 创建 AI 任务时出错: {e}")

    def main(self, hook_type="post-commit"):
        """主函数"""
        print(f"🔄 Git Hook: {hook_type} - 更新 Notion")
        print(f"⏰ 时间: {datetime.now().isoformat()}")

        # 解析提交信息
        commit_info = self.parse_commit_message()
        if not commit_info:
            print("❌ 无法解析提交信息，跳过 Notion 更新")
            return

        print(f"📝 解析到提交信息:")
        print(f"   类型: {commit_info['type']}")
        print(f"   范围: {commit_info['scope']}")
        print(f"   描述: {commit_info['description']}")
        print(f"   工单: {commit_info['issues']}")
        print(f"   上下文: {commit_info['context']}")

        # 更新工单状态
        if commit_info["issues"]:
            self.update_issue_status(commit_info)

        # 更新知识图谱
        self.update_knowledge_graph(commit_info)

        # 创建 AI 审查任务（如果需要）
        if hook_type == "post-commit":
            self.create_ai_task(commit_info)

        print("✅ Notion 更新完成")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        hook_type = sys.argv[1]
    else:
        hook_type = "post-commit"

    updater = NotionGitUpdater()
    updater.main(hook_type)

if __name__ == "__main__":
    main()
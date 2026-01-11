#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的 Notion-Git 自动同步脚本 v2.0
解决属性名、查询条件、数据库 Schema 的所有兼容性问题
"""

import os
import sys
import subprocess
import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from src.utils.path_utils import get_project_root

load_dotenv()

# ========== 环境配置 ==========
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")
PROJECT_ROOT = str(get_project_root())

# ========== Notion API 配置 ==========
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ========== 数据库 Schema 映射 ==========
# 根据实际 Notion 数据库定义这些属性
# Fixed in Task #012.00: Changed "名称" to "标题" (actual field name)
NOTION_SCHEMA = {
    "title_field": "标题",        # 工单标题属性名（title 类型）
    "status_field": "状态",       # 工单状态属性名（status 类型）
    "date_field": "日期",         # 工单日期属性名（date 类型）
}

# ========== 状态映射 ==========
COMMIT_STATUS_MAP = {
    "feat": "进行中",      # 新功能
    "fix": "进行中",       # bug 修复
    "docs": "进行中",      # 文档
    "refactor": "进行中",  # 重构
    "test": "进行中",      # 测试
    "chore": "进行中",     # 杂务
    "perf": "进行中",      # 性能
    "style": "进行中",     # 样式
}

class NotionSyncV2:
    """改进版 Notion 同步引擎 v2.0"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.db_id = NOTION_ISSUES_DB_ID

    def parse_commit_message(self):
        """解析最新提交信息"""
        try:
            commit_msg = subprocess.check_output(
                ["git", "log", "-1", "--format=%B"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            commit_details = subprocess.check_output(
                ["git", "log", "-1", "--format=%H|%an|%cd", "--date=iso"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip().split('|')

            # 解析提交信息
            lines = commit_msg.split('\n')
            first_line = lines[0] if lines else ""

            # 提取 type(scope): description 格式
            type_scope_match = re.match(r'^(\w+)(?:\(([^)]+)\))?:\s*(.+)$', first_line)
            commit_type = type_scope_match.group(1) if type_scope_match else "chore"

            # 提取工单 ID (#011, #012 等)
            issue_pattern = r'#(\d+(?:\.\d+)?)'
            issues = re.findall(issue_pattern, commit_msg)

            return {
                "hash": commit_details[0][:8],
                "author": commit_details[1],
                "date": commit_details[2],
                "type": commit_type,
                "description": first_line,
                "message": commit_msg,
                "issues": list(set(issues))  # 去重
            }

        except Exception as e:
            print(f"❌ 解析提交信息失败: {e}")
            return None

    def get_notion_db_properties(self):
        """获取 Notion 数据库的实际属性"""
        try:
            url = f"{NOTION_API_URL}/databases/{self.db_id}"
            response = requests.get(url, headers=NOTION_HEADERS)

            if response.status_code == 200:
                db = response.json()
                properties = {}

                for prop_name, prop_data in db.get("properties", {}).items():
                    properties[prop_name] = {
                        "type": prop_data.get("type"),
                        "id": prop_data.get("id")
                    }

                return properties
            else:
                print(f"❌ 获取数据库属性失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ 获取数据库属性失败: {e}")
            return None

    def find_issue_page(self, issue_id):
        """查找工单页面（使用 title 字段查询）"""
        try:
            query_url = f"{NOTION_API_URL}/databases/{self.db_id}/query"

            # 使用正确的属性名和过滤器类型
            query_data = {
                "filter": {
                    "property": NOTION_SCHEMA["title_field"],
                    "title": {
                        "contains": f"#{issue_id}"
                    }
                }
            }

            response = requests.post(query_url, headers=NOTION_HEADERS, json=query_data)

            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    return results[0]
            else:
                print(f"⚠️  查询工单 #{issue_id} 失败: {response.status_code}")

        except Exception as e:
            print(f"⚠️ 查询工单 #{issue_id} 时出错: {e}")

        return None

    def update_issue_status(self, page_id, new_status):
        """更新工单状态"""
        try:
            update_url = f"{NOTION_API_URL}/pages/{page_id}"

            # 使用正确的属性名
            update_data = {
                "properties": {
                    NOTION_SCHEMA["status_field"]: {
                        "status": {
                            "name": new_status
                        }
                    }
                }
            }

            response = requests.patch(update_url, headers=NOTION_HEADERS, json=update_data)

            if response.status_code == 200:
                return True
            else:
                print(f"⚠️ 更新工单状态失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"⚠️ 更新工单状态时出错: {e}")
            return False

    def sync(self):
        """执行同步"""
        print("\n" + "=" * 70)
        print("🔄 Notion-Git 自动同步 v2.0")
        print("=" * 70)

        # 1. 解析提交信息
        commit_info = self.parse_commit_message()
        if not commit_info or not commit_info["issues"]:
            print("📝 解析提交信息")
            print("   ⚠️ 没有发现工单号，跳过同步")
            return

        print(f"📝 解析提交信息")
        print(f"   ✅ 提交类型: {commit_info['type']}")
        print(f"   ✅ 工单号: {', '.join([f'#{i}' for i in commit_info['issues']])}")

        # 2. 确定目标状态
        new_status = COMMIT_STATUS_MAP.get(commit_info["type"], "进行中")
        print(f"📊 确定目标状态: {new_status}")

        # 3. 更新每个工单
        print(f"🔄 更新工单状态")
        success_count = 0

        for issue_id in commit_info["issues"]:
            # 查找工单页面
            page = self.find_issue_page(issue_id)
            if not page:
                print(f"   ⚠️ 工单 #{issue_id}: 未找到")
                continue

            # 获取工单信息
            title = page.get("properties", {}).get(NOTION_SCHEMA["title_field"], {}).get("title", [])
            title_text = title[0].get("plain_text", "Unknown") if title else "Unknown"
            page_id = page["id"]

            # 更新状态
            if self.update_issue_status(page_id, new_status):
                print(f"   ✅ 工单 #{issue_id}: {title_text}")
                print(f"      状态: {new_status}")
                success_count += 1
            else:
                print(f"   ❌ 工单 #{issue_id}: 更新失败")

        # 4. 总结
        print("\n" + "=" * 70)
        if success_count > 0:
            print(f"✅ 同步完成: {success_count}/{len(commit_info['issues'])} 个工单已更新")
        else:
            print("⚠️ 同步完成: 没有工单被更新")
        print("=" * 70 + "\n")

        return success_count > 0


def main():
    """主函数"""
    if not NOTION_TOKEN or not NOTION_ISSUES_DB_ID:
        print("❌ 缺少 NOTION_TOKEN 或 NOTION_ISSUES_DB_ID 环境变量")
        sys.exit(1)

    sync = NotionSyncV2()
    sync.sync()


if __name__ == "__main__":
    main()

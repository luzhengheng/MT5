#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建演示测试任务
在 Notion 中创建一个示例页面来测试系统功能
"""

import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DB_ID")

def create_demo_task():
    """创建演示任务"""
    print("🚀 创建演示测试任务...")

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    demo_task = {
        "parent": {
            "type": "database_id",
            "database_id": DATABASE_ID
        },
        "properties": {
            "名称": {
                "title": [
                    {
                        "text": {
                            "content": "🧪 测试：分析风险管理模块的代码质量"
                        }
                    }
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "💬 这是一个测试任务，请系统自动分析风险管理相关的代码质量并提供优化建议。"
                            }
                        }
                    ]
                }
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=demo_task
        )

        if response.status_code == 200:
            page_info = response.json()
            page_url = page_info.get("url", "")
            print(f"✅ 演示任务创建成功！")
            print(f"🔗 页面链接: {page_url}")
            print("\n📝 任务详情:")
            print("标题: 🧪 测试：分析风险管理模块的代码质量")
            print("状态: 已创建，等待 nexus_simple.py 处理")
            print("\n⏱️ 系统将在30秒内检测到新页面���开始处理...")

            return True
        else:
            print(f"❌ 创建失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 创建任务时出错: {e}")
        return False

if __name__ == "__main__":
    if create_demo_task():
        print("\n🎯 现在可以:")
        print("1. 查看 Notion 页面中的任务创建情况")
        print("2. 监控 nexus_simple.py 的输出日志")
        print("3. 等待 Gemini 的回复自动添加到页面")
        print("\n按 Ctrl+C 停止监控")
    else:
        print("\n请检查配置后重试")
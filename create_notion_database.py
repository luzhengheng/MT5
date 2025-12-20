#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动创建 Notion 数据库
创建 🧠 AI Command Center 数据库并配置必需的字段
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    """获取 Notion API 请求头"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def create_ai_command_center_database():
    """创建 AI Command Center 数据库"""
    print("🚀 正在创建 🧠 AI Command Center 数据库...")

    # 数据库配置
    database_config = {
        "parent": {
            "type": "page_id",
            "page_id": "02081235e2fa4bffa6200b6df6c9660b"  # 使用默认工作空间根页面
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "🧠 AI Command Center"
                }
            }
        ],
        "properties": {
            "Topic": {
                "title": {}
            },
            "Status": {
                "status": {}
            },
            "Context Files": {
                "multi_select": {
                    "options": [
                        {"name": "src/", "color": "gray"},
                        {"name": "docs/", "color": "brown"},
                        {"name": "config/", "color": "orange"},
                        {"name": "bin/", "color": "yellow"},
                        {"name": "tests/", "color": "green"},
                        {"name": "*.py", "color": "blue"},
                        {"name": "*.md", "color": "purple"},
                        {"name": "*.yaml", "color": "pink"}
                    ]
                }
            },
            "Prompt": {
                "rich_text": {}
            },
            "Created Time": {
                "created_time": {}
            },
            "Last Edited Time": {
                "last_edited_time": {}
            }
        },
        "icon": {
            "type": "emoji",
            "emoji": "🧠"
        }
    }

    try:
        # 创建数据库
        response = requests.post(
            f"{NOTION_BASE_URL}/databases",
            headers=notion_headers(),
            json=database_config
        )

        if response.status_code == 200:
            database_info = response.json()
            database_id = database_info["id"]
            database_url = database_info["url"]

            print(f"✅ 数据库创建成功！")
            print(f"🔑 数据库 ID: {database_id}")
            print(f"🔗 数据库链接: {database_url}")

            return database_id, database_url
        else:
            print(f"❌ 创建数据库失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None, None

    except Exception as e:
        print(f"❌ 创建数据库时出错: {e}")
        return None, None

def add_sample_entries(database_id):
    """添加示例条目到数据库"""
    print(f"\n📝 正在添加示例条目...")

    sample_entries = [
        {
            "Topic": "分析风险管理模块的代码质量",
            "Status": "Ready to Send",
            "Context Files": ["src/strategy/risk_manager.py"],
            "Prompt": "请分析这段代码的质量，包括错误处理、性能优化建议"
        },
        {
            "Topic": "机器学习模型特征工程优化建议",
            "Status": "Draft",
            "Context Files": ["src/feature_engineering/", "docs/ML_GUIDE.md"],
            "Prompt": "基于现有特征工程代码，提供优化建议"
        },
        {
            "Topic": "如何优化回测系统性能？",
            "Status": "Draft",
            "Context Files": ["src/reporting/", "bin/run_backtest.py"],
            "Prompt": "识别性能瓶颈并提供优化方案"
        }
    ]

    for i, entry in enumerate(sample_entries):
        try:
            page_data = {
                "parent": {
                    "type": "database_id",
                    "database_id": database_id
                },
                "properties": {
                    "Topic": {
                        "title": [
                            {
                                "text": {
                                    "content": entry["Topic"]
                                }
                            }
                        ]
                    },
                    "Status": {
                        "status": {
                            "name": entry["Status"]
                        }
                    },
                    "Context Files": {
                        "multi_select": [
                            {"name": file} for file in entry["Context Files"]
                        ]
                    }
                }
            }

            # 如果有 Prompt，添加到页面内容中
            if entry.get("Prompt"):
                page_data["children"] = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"💬 {entry['Prompt']}"
                                    }
                                }
                            ]
                        }
                    }
                ]

            response = requests.post(
                f"{NOTION_BASE_URL}/pages",
                headers=notion_headers(),
                json=page_data
            )

            if response.status_code == 200:
                print(f"✅ 示例条目 {i+1} 创建成功: {entry['Topic']}")
            else:
                print(f"❌ 示例条目 {i+1} 创建失败: {response.status_code}")

        except Exception as e:
            print(f"❌ 创建示例条目 {i+1} 时出错: {e}")

def update_env_file(database_id):
    """更新 .env 文件中的数据库 ID"""
    print(f"\n📝 更新 .env 文件...")

    try:
        # 读取当前 .env 文件
        with open('/opt/mt5-crs/.env', 'r') as f:
            content = f.read()

        # 替换 NOTION_DB_ID 行
        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            if line.startswith('NOTION_DB_ID='):
                updated_lines.append(f'NOTION_DB_ID={database_id}')
            else:
                updated_lines.append(line)

        # 写回文件
        with open('/opt/mt5-crs/.env', 'w') as f:
            f.write('\n'.join(updated_lines))

        print(f"✅ .env 文件已更新，NOTION_DB_ID = {database_id}")

    except Exception as e:
        print(f"❌ 更新 .env 文件失败: {e}")

def main():
    """主函数"""
    print("="*60)
    print("🏗️ Notion 数据库自动创建器")
    print("="*60)

    # 检查 token
    if not NOTION_TOKEN:
        print("❌ 未找到 NOTION_TOKEN，请检查 .env 文件")
        return

    # 创建数据库
    database_id, database_url = create_ai_command_center_database()

    if database_id:
        # 添加示例条目
        add_sample_entries(database_id)

        # 更新 .env 文件
        update_env_file(database_id)

        print(f"\n🎉 数据库设置完成！")
        print(f"📊 数据库名称: 🧠 AI Command Center")
        print(f"🔑 数据库 ID: {database_id}")
        print(f"🔗 访问链接: {database_url}")

        print(f"\n🚀 下一步:")
        print(f"1. 访问数据库链接确认创建成功")
        print(f"2. 运行 nexus_bridge.py 开始监控")
        print(f"python3 nexus_bridge.py")

    else:
        print(f"\n❌ 数据库创建失败")
        print(f"请检查:")
        print(f"1. Notion Integration 权限")
        print(f"2. 网络连接")
        print(f"3. API Token 是否正确")

if __name__ == "__main__":
    main()
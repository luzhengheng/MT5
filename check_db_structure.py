#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Notion 数据库结构
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def check_database(db_id: str, db_name: str):
    """检查数据库结构"""
    try:
        url = f"{NOTION_BASE_URL}/databases/{db_id}"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            db_info = response.json()
            print(f"\n📊 {db_name} 数据库结构:")
            print(f"   ID: {db_id}")
            print("   字段:")

            properties = db_info.get("properties", {})
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "unknown")
                print(f"   - {prop_name}: {prop_type}")

                if prop_type == "select" and "select" in prop_info:
                    options = prop_info["select"].get("options", [])
                    if options:
                        option_names = [opt.get("name", "") for opt in options]
                        print(f"     选项: {', '.join(option_names)}")

                elif prop_type == "status" and "status" in prop_info:
                    options = prop_info["status"].get("options", [])
                    if options:
                        option_names = [opt.get("name", "") for opt in options]
                        print(f"     选项: {', '.join(option_names)}")

        else:
            print(f"❌ 无法访问 {db_name}: {response.status_code}")

    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

def main():
    print("=" * 60)
    print("🔍 检查 Notion 数据库结构")
    print("=" * 60)

    databases = [
        ("2cfc8858-2b4e-817e-a4a5-fe17be413d64", "🧠 AI Command Center"),
        ("2cfc8858-2b4e-816b-9a15-d85908bf4a21", "📋 Issues"),
        ("2cfc8858-2b4e-811d-83be-d3bd3957adea", "💡 Knowledge Graph"),
        ("2cfc8858-2b4e-8160-8466-cc6e3fb527e9", "📚 Documentation")
    ]

    for db_id, db_name in databases:
        check_database(db_id, db_name)

if __name__ == "__main__":
    main()
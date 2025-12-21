#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 MT5-CRS Nexus 数据库结构
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

def main():
    print("=" * 60)
    print("🔍 检查 MT5-CRS Nexus 数据库结构")
    print("=" * 60)

    # MT5-CRS Nexus 数据库 ID
    nexus_db_id = "2cfc8858-2b4e-801b-b15b-d96893b7ba09"

    try:
        url = f"{NOTION_BASE_URL}/databases/{nexus_db_id}"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            db_info = response.json()
            print(f"✅ 数���库信息:")
            print(f"   标题: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            print(f"   ID: {db_info.get('id', 'Unknown')}")
            print(f"   URL: {db_info.get('url', 'Unknown')}")
            print(f"   字段数量: {len(db_info.get('properties', {}))}")

            print(f"\n📊 字段详情:")
            properties = db_info.get("properties", {})
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "unknown")
                print(f"   - {prop_name}: {prop_type}")

                # 显示具体选项（如果有）
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

                elif prop_type == "multi_select" and "multi_select" in prop_info:
                    options = prop_info["multi_select"].get("options", [])
                    if options:
                        option_names = [opt.get("name", "") for opt in options]
                        print(f"     选项: {', '.join(option_names)}")

        else:
            print(f"❌ 无法访问数据库: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")

if __name__ == "__main__":
    main()
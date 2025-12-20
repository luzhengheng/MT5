#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定位 MT5-CRS Nexus 页面和数据库
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

def locate_nexus_pages():
    """定位所有相关的页面和数据库"""
    print("🔍 搜索 MT5-CRS Nexus 主页面...")

    # 搜索主页面
    search_url = f"{NOTION_BASE_URL}/search"
    search_data = {
        "query": "MT5-CRS Nexus",
        "filter": {
            "property": "object",
            "value": "page"
        }
    }

    response = requests.post(search_url, headers=notion_headers(), json=search_data)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            for page in results:
                title = page.get("properties", {}).get("title", {}).get("title", [])
                if title:
                    page_title = title[0].get("plain_text", "Untitled")
                    page_id = page["id"]
                    url = page.get("url", "")
                    print(f"\n✅ 找到主页面:")
                    print(f"   标题: {page_title}")
                    print(f"   ID: {page_id}")
                    print(f"   URL: {url}")

                    # 检查页面的子块（查看数据库）
                    children_url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"
                    children_response = requests.get(children_url, headers=notion_headers())

                    if children_response.status_code == 200:
                        children = children_response.json().get("results", [])
                        print(f"   子元素数量: {len(children)}")

                        for child in children:
                            if child.get("type") == "child_database":
                                db_id = child.get("id")
                                print(f"   📊 发现数据库: {db_id}")
        else:
            print("❌ 未找到 MT5-CRS Nexus 主页面")
    else:
        print(f"❌ 搜索失败: {response.status_code}")

def list_all_databases():
    """列出所有数据库"""
    print("\n🗃️ 查看所有数据库...")

    search_url = f"{NOTION_BASE_URL}/search"
    search_data = {
        "filter": {
            "property": "object",
            "value": "database"
        }
    }

    response = requests.post(search_url, headers=notion_headers(), json=search_data)

    if response.status_code == 200:
        results = response.json().get("results", [])
        print(f"\n找到 {len(results)} 个数据库:")

        for db in results:
            title = db.get("title", [])
            if title:
                db_title = title[0].get("plain_text", "Untitled")
                db_id = db["id"]
                url = db.get("url", "")
                print(f"\n   📊 {db_title}")
                print(f"      ID: {db_id}")
                print(f"      URL: {url}")
    else:
        print(f"❌ 获取数据库列表失败: {response.status_code}")

def get_page_url_from_id(page_id: str):
    """根据 ID 获取页面 URL"""
    try:
        url = f"{NOTION_BASE_URL}/pages/{page_id}"
        response = requests.get(url, headers=notion_headers())

        if response.status_code == 200:
            page_data = response.json()
            return page_data.get("url", "")
        return None
    except:
        return None

def main():
    print("=" * 60)
    print("📍 定位 MT5-CRS Nexus 页面")
    print("=" * 60)

    # 定位主页面
    locate_nexus_pages()

    # 列出所有数据库
    list_all_databases()

    print("\n" + "=" * 60)
    print("🔗 直接访问链接:")
    print("=" * 60)

    # 提供直接链接
    databases = [
        ("🧠 AI Command Center", "2cfc8858-2b4e-817e-a4a5-fe17be413d64"),
        ("📋 Issues", "2cfc8858-2b4e-816b-9a15-d85908bf4a21"),
        ("💡 Knowledge Graph", "2cfc8858-2b4e-811d-83be-d3bd3957adea"),
        ("📚 Documentation", "2cfc8858-2b4e-8160-8466-cc6e3fb527e9")
    ]

    for name, db_id in databases:
        print(f"\n{name}:")
        print(f"   https://www.notion.so/{db_id.replace('-', '')}")

if __name__ == "__main__":
    main()
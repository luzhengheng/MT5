#!/usr/bin/env python3
"""检查 Notion 数据库的属性结构"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DB_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
resp = requests.get(url, headers=headers)

if resp.status_code == 200:
    db_info = resp.json()
    print("📊 Notion 数据库属性列表:")
    print(json.dumps(list(db_info.get("properties", {}).keys()), indent=2, ensure_ascii=False))
else:
    print(f"❌ 错误: {resp.status_code}")
    print(resp.text)

import os
import sys
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

# --- 配置区域 ---
TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 映射表：命令行参数 -> 中文选项
STATUS_MAP = {
    "TODO": "未开始",
    "IN_PROGRESS": "进行中",
    "DONE": "完成"
}

TYPE_MAP = {
    "Core": "核心",
    "Bug": "缺陷",
    "Infra": "运维",
    "Feature": "功能"
}

def create_issue(title, priority, issue_type_key, status_key):
    url = "https://api.notion.com/v1/pages"
    
    # 转换值为中文
    status_val = STATUS_MAP.get(status_key, "未开始")
    type_val = TYPE_MAP.get(issue_type_key, "核心")
    
    print(f"📝 正在创建: {title}")
    print(f"   - 状态: {status_val} (Status)")
    print(f"   - 类型: {type_val} (Select)")
    print(f"   - 优先级: {priority} (Select)")

    payload = {
        "parent": {"database_id": DB_ID},
        "properties": {
            "标题": {
                "title": [{"text": {"content": title}}]
            },
            "状态": {
                "status": {"name": status_val}  # 关键修复：使用 status 类型
            },
            "优先级": {
                "select": {"name": priority}
            },
            "类型": {
                "select": {"name": type_val}
            }
        }
    }

    try:
        resp = requests.post(url, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        print(f"✅ SUCCESS: Created '{title}'")
        print(f"🔗 URL: {data['url']}")
    except requests.exceptions.HTTPError as e:
        print(f"❌ FAILED: {e}")
        print(f"⚠️  错误详情: {resp.text}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("title", help="工单标题")
    parser.add_argument("--prio", choices=["P0", "P1", "P2", "P3"], default="P2")
    parser.add_argument("--type", choices=["Core", "Bug", "Infra", "Feature"], default="Core")
    parser.add_argument("--status", choices=["TODO", "IN_PROGRESS", "DONE"], default="TODO")
    
    args = parser.parse_args()
    create_issue(args.title, args.prio, args.type, args.status)

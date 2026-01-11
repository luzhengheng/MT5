import os, requests, json
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB_ID")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"}

print(f"🕵️  正在侦测数据库 Schema (ID: ...{DB_ID[-4:]}) ...")
response = requests.get(f"https://api.notion.com/v1/databases/{DB_ID}", headers=HEADERS)

if response.status_code != 200:
    print(f"❌ 失败: {response.text}")
else:
    props = response.json().get("properties", {})
    print("\n✅ 侦测到的真实列名 (Keys):")
    print("--------------------------------")
    for name, prop in props.items():
        print(f"🔹 {name} \t(类型: {prop['type']})")
    print("--------------------------------")

import os, requests, json
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB_ID")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"}

print(f"🕵️  正在读取数据库选项配置 (ID: ...{DB_ID[-4:]}) ...")
response = requests.get(f"https://api.notion.com/v1/databases/{DB_ID}", headers=HEADERS)
data = response.json()

if "properties" not in data:
    print(f"❌ 错误: {data}")
else:
    status_prop = data["properties"].get("状态", {})
    print("\n✅ '状态' (Status) 列的允许值:")
    if status_prop.get("status"):
        for opt in status_prop["status"]["options"]:
            print(f"   - {opt['name']}")
        for grp in status_prop["status"].get("groups", []):
             for opt in grp.get("options", []):
                print(f"   - {opt['name']}")
    else:
        print("   ❌ 未找到状态配置，请检查列名是否为'状态'")

    print("\n✅ '优先级' (Select) 列的允许值:")
    prio_prop = data["properties"].get("优先级", {})
    if prio_prop.get("select"):
        for opt in prio_prop["select"]["options"]:
            print(f"   - {opt['name']}")
    else:
        print("   ⚠️  目前为空 (脚本运行后会自动创建)")

    print("\n✅ '类型' (Select) 列的允许值:")
    type_prop = data["properties"].get("类型", {})
    if type_prop.get("select"):
        for opt in type_prop["select"]["options"]:
            print(f"   - {opt['name']}")
    else:
        print("   ⚠️  目前为空 (脚本运行后会自动创建)")

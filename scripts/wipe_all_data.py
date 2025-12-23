import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("NOTION_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def wipe_db(db_id, name):
    if not db_id:
        print(f"⚠️ 跳过 {name}: ID 未在 .env 中找到")
        return
        
    print(f"🧹 正在清空: {name}...")
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    
    # 循环分页删除，直到删完
    while True:
        response = requests.post(url, headers=HEADERS, json={"page_size": 100})
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            print(f"   ✨ {name} 已经是空的了")
            break
            
        print(f"   🔎 发现 {len(results)} 条数据，正在删除...")
        for page in results:
            # 将 archived 设为 True 等同于删除
            requests.patch(
                f"https://api.notion.com/v1/pages/{page['id']}", 
                headers=HEADERS, 
                json={"archived": True}
            )
            
        if not data.get("has_more"):
            break
            
    print(f"✅ {name} 清空完毕!")

if __name__ == "__main__":
    wipe_db(os.getenv("NOTION_DB_ID"), "工单库 (Issues)")
    wipe_db(os.getenv("NOTION_WIKI_DB_ID"), "知识库 (Nexus)")

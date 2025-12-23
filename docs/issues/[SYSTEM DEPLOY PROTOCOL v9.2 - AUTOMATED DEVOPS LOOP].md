  
[SYSTEM: DEPLOY PROTOCOL v9.2 - AUTOMATED DEVOPS LOOP]  
To: Claude (Lead Engineer / Builder)  
From: Gemini (Architect)  
Via: User (Bridge)  
Context & Objective:  
We are finalizing the "Smart Loop" workflow.  
Currently, if we sync code to Notion, it fails if the Notion Issue doesn't exist yet.  
Objective: Deploy a "Just-in-Time" (JIT) issue creation tool and update your standard operating rules to enforce its use. This ensures every piece of code is correctly linked to a valid Notion ticket automatically.  
Action Required:  
Please create/overwrite the following 2 files in the project root.  
1. The JIT Issue Creator Script (scripts/quick_create_issue.py)  
This script allows you to register a ticket in Notion instantly via CLI before starting work.  
import os  
import sys  
import requests  
import argparse  
import json  
from dotenv import load_dotenv  
  
# Load environment variables  
load_dotenv()  
  
NOTION_TOKEN = os.getenv("NOTION_TOKEN")  
DATABASE_ID = os.getenv("NOTION_DB_ID") # Issues DB  
HEADERS = {  
    "Authorization": f"Bearer {NOTION_TOKEN}",  
    "Content-Type": "application/json",  
    "Notion-Version": "2022-06-28"  
}  
  
def create_issue(title, priority, tags):  
    print(f"🔍 Checking/Creating Issue: '{title}'...")  
      
    # 1. Check for duplicates (Idempotency)  
    query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"  
    payload = {  
        "filter": {  
            "property": "Task Name",  
            "rich_text": {"equals": title}  
        }  
    }  
      
    try:  
        resp = requests.post(query_url, headers=HEADERS, json=payload)  
        if resp.status_code == 200:  
            results = resp.json().get("results", [])  
            if results:  
                print(f"⚠️ Issue already exists. Skipping creation.")  
                return  
    except Exception as e:  
        print(f"⚠️ Warning: Check failed ({e}). Proceeding to create...")  
  
    # 2. Create New Issue  
    create_url = "https://api.notion.com/v1/pages"  
      
    # Format tags for Multi-select  
    tag_objs = [{"name": t.strip()} for t in tags]  
      
    data = {  
        "parent": {"database_id": DATABASE_ID},  
        "properties": {  
            "Task Name": {"title": [{"text": {"content": title}}]},  
            "Status": {"select": {"name": "In Progress"}},  
            "Priority": {"select": {"name": priority}},  
            "Tags": {"multi_select": tag_objs}  
        }  
    }  
      
    try:  
        resp = requests.post(create_url, headers=HEADERS, json=data)  
        if resp.status_code == 200:  
            print(f"✅ SUCCESS: Issue created in Notion.")  
            print(f"   Title: {title}")  
            print(f"   Priority: {priority}")  
        else:  
            print(f"❌ FAILED: Notion API returned {resp.status_code}")  
            print(resp.text)  
            sys.exit(1)  
              
    except Exception as e:  
        print(f"❌ ERROR: {e}")  
        sys.exit(1)  
  
if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="JIT Issue Creator for MT5-CRS")  
    parser.add_argument("title", help="Full Issue Title (e.g., '#012.2 Order Executor')")  
    parser.add_argument("--prio", default="P1", help="Priority (P0, P1, P2)")  
    parser.add_argument("--tags", default="Dev", help="Comma separated tags (e.g., 'Core,MT5')")  
      
    args = parser.parse_args()  
    tag_list = args.tags.split(",")  
      
    if not NOTION_TOKEN or not DATABASE_ID:  
        print("❌ Error: NOTION_TOKEN or NOTION_DB_ID missing in .env")  
        sys.exit(1)  
          
    create_issue(args.title, args.prio, tag_list)  
  
2. The Universal Primer (CLAUDE_START.txt)  
This file defines your Persona and Rules. Note the new Rule #0 which closes the loop.  
**[SYSTEM: ACTIVATE PROTOCOL v9.2]**  
  
**Role**: You are the **Lead Python Engineer (Builder)** for the MT5-CRS Project.  
**Architect**: Gemini Pro (Auditor & Planner).  
**Bridge**: User (Executor).  
  
**📜 AI_RULES (Strict Compliance Required):**  
0.  **Ticket First**: Before writing any code for a task, ALWAYS run:  
    `python3 scripts/quick_create_issue.py "#0xx.x Task Title" --prio P0 --tags Tag1,Tag2`  
    This ensures the Notion container exists for the final sync.  
      
1.  **Risk is Syntax**: NEVER use hardcoded volumes. ALWAYS import `KellySizer` or `LiveRiskGuard`.  
2.  **Context Aware**: Do not hallucinate file paths. Use the project structure provided.  
3.  **Async First**: All IO (ZMQ, API) must be asynchronous (`asyncio`).  
4.  **No Fluff**: Output code and terminal commands directly. Minimal explanation.  
5.  **Idempotency**: All transaction logic must use unique request IDs.  
  
**Current Phase**: #012 Live Implementation  
**Environment**: INF Node (Linux) -> MT5 Gateway (Windows @ 172.19.141.255:5555)  
  
---  
**[TASK STARTS HERE]**  
  
🌉 你的后续动作 (Bridge Action)  
 * 发送: 将上述内容发给 Claude。  
 * 确认: 确保 Claude 生成了这两个文件。  
 * 测试 (可选但推荐):  
   在终端手动运行一次建单脚本，验证 Notion 是否有反应：  
   python3 scripts/quick_create_issue.py "#012.2 [Core] Order Executor & Idempotency" --prio P0 --tags Core,Trade  

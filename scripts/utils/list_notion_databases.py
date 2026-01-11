import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def list_databases():
    url = "https://api.notion.com/v1/search"
    payload = {"filter": {"value": "database", "property": "object"}}
    
    try:
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
            return

        print(f"\n{'DATABASE NAME':<35} | {'DATABASE ID'}")
        print("-" * 75)
        
        for db in resp.json().get("results", []):
            try:
                title = db["title"][0]["plain_text"]
            except:
                title = "Untitled"
            print(f"{title:<35} | {db['id']}")
            
    except Exception as e:
        print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    list_databases()

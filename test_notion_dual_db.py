#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Notion 双数据库连接
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
KNOWLEDGE_DB_ID = os.getenv("NOTION_KNOWLEDGE_DB_ID", "2cfc8858-2b4e-801b-b15b-d96893b7ba09")
ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

def test_database(db_id, db_name):
    """测试数据库连接"""
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    print(f"\n{'='*60}")
    print(f"📊 测试: {db_name}")
    print(f"🆔 ID: {db_id}")
    print(f"{'='*60}")

    if not db_id:
        print("❌ 数据库 ID 未配置")
        print("💡 请在 .env 文件中配置此数据库 ID")
        return False

    # 获取数据库信息
    response = requests.get(
        f"https://api.notion.com/v1/databases/{db_id}",
        headers=headers
    )

    if response.status_code == 200:
        db = response.json()
        title = db.get("title", [{}])[0].get("plain_text", "N/A")
        print(f"✅ 连接成功")
        print(f"📝 数据库名称: {title}")

        # 获取属性列表
        properties = db.get("properties", {})
        print(f"📋 属性列表 ({len(properties)} 个):")
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "N/A")
            print(f"   - {prop_name}: {prop_type}")

        # 查询内容
        query_response = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=headers,
            json={"page_size": 3}
        )

        if query_response.status_code == 200:
            pages = query_response.json().get("results", [])
            print(f"\n📄 数据库内容 (前3条，共 {len(pages)} 条显示):")
            for i, page in enumerate(pages, 1):
                # 尝试获取标题
                props = page.get("properties", {})
                title_text = "N/A"
                for key in ["任务名称", "Name", "名称", "Title", "title"]:
                    if key in props:
                        title_data = props[key]
                        if title_data.get("type") == "title":
                            title_list = title_data.get("title", [])
                            if title_list:
                                title_text = title_list[0].get("plain_text", "N/A")
                                break

                last_edited = page.get("last_edited_time", "N/A")
                print(f"   {i}. {title_text}")
                print(f"      最后编辑: {last_edited}")

        return True
    else:
        print(f"❌ 连接失败: {response.status_code}")
        print(f"错误: {response.text}")
        return False

def main():
    print("="*60)
    print("🤖 MT5-CRS Notion 双数据库连接测试")
    print("="*60)

    # 测试知识库
    knowledge_ok = test_database(KNOWLEDGE_DB_ID, "MT5-CRS Nexus 知识库")

    # 测试 Issues
    issues_ok = test_database(ISSUES_DB_ID, "MT5-CRS Issues")

    # 总结
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    print(f"知识库: {'✅ 正常' if knowledge_ok else '❌ 失败'}")
    print(f"Issues: {'✅ 正常' if issues_ok else '❌ 失败'}")

    if knowledge_ok and issues_ok:
        print("\n🎉 双数据库配置完成！Git Hook 可以正常工作。")
    elif knowledge_ok and not issues_ok:
        print("\n⚠️  知识库正常，但 Issues 数据库未配置")
        print("💡 请按照 NOTION_SETUP_GUIDE.md 创建 Issues 数据库")
    else:
        print("\n❌ 配置存在问题，请检查 .env 文件和 Notion 集成权限")

    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将完整工单内容添加到 Notion Issue 页面
"""

import os
import sys
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

def get_issue_page_id(issue_id: str):
    """获取 Notion 中对应工单的页面 ID"""

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # 查询数据库找到对应的页面
    query_url = f"https://api.notion.com/v1/databases/{NOTION_ISSUES_DB_ID}/query"
    query_data = {
        "filter": {
            "property": "名称",
            "title": {
                "contains": issue_id
            }
        }
    }

    response = requests.post(query_url, headers=headers, json=query_data)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[0]["id"]

    return None

def add_content_blocks_to_page(page_id: str, blocks: list):
    """向 Notion 页面添加内容块"""

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    data = {
        "children": blocks
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        return True
    else:
        print(f"❌ 添加内容失败: {response.status_code}")
        print(f"   错误: {response.text}")
        return False

def create_text_block(text: str, is_heading: str = None):
    """创建文本块"""
    block_type = "paragraph"
    properties = {}

    if is_heading == "h1":
        block_type = "heading_1"
    elif is_heading == "h2":
        block_type = "heading_2"
    elif is_heading == "h3":
        block_type = "heading_3"

    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": text
                    }
                }
            ]
        }
    }

def create_code_block(code: str, language: str = "python"):
    """创建代码块"""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": code
                    }
                }
            ],
            "language": language
        }
    }

def parse_and_create_blocks(markdown_content: str):
    """解析 Markdown 内容并创建对应的 Notion 块"""
    blocks = []
    lines = markdown_content.split('\n')

    # Notion 支持的语言列表
    supported_languages = {
        "python", "javascript", "java", "c", "c++", "c#", "go", "rust",
        "typescript", "ruby", "php", "swift", "kotlin", "scala", "r",
        "shell", "bash", "powershell", "sql", "html", "css", "json",
        "yaml", "xml", "markdown", "plain text", "text"
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # 跳过空行
        if not line.strip():
            i += 1
            continue

        # 标题处理
        if line.startswith('### '):
            blocks.append(create_text_block(line[4:].strip(), "h3"))
        elif line.startswith('## '):
            blocks.append(create_text_block(line[3:].strip(), "h2"))
        elif line.startswith('# '):
            blocks.append(create_text_block(line[2:].strip(), "h1"))
        # 代码块处理
        elif line.startswith('```'):
            code_lines = []
            i += 1

            # 获取语言标识
            language = "python"  # 默认
            if i < len(lines):
                first_line = lines[i].strip().lower()

                # 检查是否是代码块结束
                if not first_line.startswith('```'):
                    # 检查是否是支持的语言
                    if first_line in supported_languages:
                        language = first_line
                        i += 1
                    elif first_line.startswith('bash') or first_line.startswith('sh'):
                        language = "bash"
                        i += 1
                    elif first_line.startswith('text'):
                        language = "plain text"
                        i += 1
                    else:
                        # 不支持的语言，使用 plain text
                        language = "plain text"
                        i += 1

            # 收集代码内容
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1

            code_content = '\n'.join(code_lines).strip()
            if code_content:
                blocks.append(create_code_block(code_content, language))
        # 列表项处理
        elif line.startswith('* ') or line.startswith('- '):
            blocks.append(create_text_block(line[2:].strip()))
        # 普通文本
        else:
            blocks.append(create_text_block(line.strip()))

        i += 1

    return blocks

def main():
    print("📝 正在将工单 #011.3 完整内容添加到 Notion...\n")

    # 读取工单文件
    issue_file = "docs/issues/🚀 工单 #011.3 升级 Gemini Review Bridge (适配 Gemini 3 Pro & ROI 最大化….md"

    if not os.path.exists(issue_file):
        print(f"❌ 工单文件不存在: {issue_file}")
        return

    with open(issue_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 获取工单页面 ID
    page_id = get_issue_page_id("#011.3")

    if not page_id:
        print("❌ 在 Notion 中找不到工单 #011.3")
        return

    print(f"✅ 找到工单页面: {page_id}\n")

    # 解析内容为块
    blocks = parse_and_create_blocks(content)

    print(f"📊 将添加 {len(blocks)} 个内容块...\n")

    # 分批添加块（Notion API 限制）
    batch_size = 100
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i+batch_size]
        print(f"📤 添加第 {i//batch_size + 1} 批 ({len(batch)} 块)...")

        if add_content_blocks_to_page(page_id, batch):
            print(f"   ✅ 成功添加 {len(batch)} 块")
        else:
            print(f"   ❌ 添加失败")
            return

    print(f"\n✅ 工单 #011.3 完整内容已成功添加到 Notion！")
    print(f"   📍 包含: {len(blocks)} 个内容块")
    print(f"   📋 包含: 需求背景、实施任务、代码规范、执行指令")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Notion Bridge - 将本地 Markdown 工单推送到 Notion 数据库

功能:
  1. 解析 Markdown 工单 (Frontmatter + 内容)
  2. 验证 Notion Token 连通性
  3. 创建/更新 Notion Page
  4. 处理 API 速率限制

使用例:
  python3 scripts/ops/notion_bridge.py --action parse --input task.md
  python3 scripts/ops/notion_bridge.py --action validate-token
  python3 scripts/ops/notion_bridge.py --action push --input metadata.json
"""

import json
import os
import sys
import time
import argparse
import logging
import re
from typing import Dict, Optional, Any
from datetime import datetime

try:
    from notion_client import Client
except ImportError:
    print("⚠️  notion-client not installed. Run: pip install notion-client")
    sys.exit(1)

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )
except ImportError:
    print("⚠️  tenacity not installed. Run: pip install tenacity")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DB_ID")
NOTION_TASK_DATABASE_ID = os.getenv(
    "NOTION_TASK_DATABASE_ID", NOTION_DATABASE_ID
)

# Rate limiting: Notion API allows ~3 requests/second
NOTION_API_RATE_LIMIT = 0.35  # seconds between requests

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Parser: 解析 Markdown 工单
# ============================================================================


def parse_markdown_task(filepath: str) -> Dict[str, Any]:
    """
    解析 Markdown 工单文件，提取 Frontmatter 和内容。

    Args:
        filepath: Markdown 文件路径

    Returns:
        {
            'task_id': 'TASK#125',
            'title': '构建自动化开发闭环',
            'priority': 'Critical',
            'status': '进行中',
            'dependencies': ['TASK#124'],
            'content': '... markdown content ...',
            'created_at': '2026-01-18T...'
        }
    """
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter (if exists)
    frontmatter = {}
    markdown_content = content

    if content.startswith('/task'):
        # 解析自定义 Frontmatter 格式
        lines = content.split('\n')
        frontmatter_lines = []
        content_start = 0

        for i, line in enumerate(lines):
            if line.strip() == '' and i > 5:  # 空行之后开始正式内容
                content_start = i + 1
                break
            frontmatter_lines.append(line)

        # 从 frontmatter 提取关键信息
        frontmatter_text = '\n'.join(frontmatter_lines)

        # 提取 Task ID
        task_id_match = re.search(
            r'TASK\s*#(\d+)', frontmatter_text, re.IGNORECASE
        )
        frontmatter['task_id'] = (
            f"TASK#{task_id_match.group(1)}"
            if task_id_match
            else "UNKNOWN"
        )

        # 提取标题 (第一行的 TASK# 后面的内容)
        title_match = re.search(
            r'TASK\s*#\d+:\s*(.+?)(?:\(|$)', frontmatter_text
        )
        frontmatter['title'] = (
            title_match.group(1).strip() if title_match else "Untitled Task"
        )

        # 提取优先级
        priority_match = re.search(r'Priority:\s*(\w+)', frontmatter_text)
        frontmatter['priority'] = (
            priority_match.group(1) if priority_match else "Medium"
        )

        # 提取依赖
        dep_match = re.search(
            r'Dependencies:\s*(.+?)(?:\n|$)', frontmatter_text
        )
        if dep_match:
            deps_str = dep_match.group(1)
            frontmatter['dependencies'] = [
                d.strip() for d in re.findall(r'TASK\s*#\d+', deps_str)
            ]
        else:
            frontmatter['dependencies'] = []

        markdown_content = '\n'.join(lines[content_start:])
    else:
        # Try YAML-style frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                markdown_content = parts[2]

                # Simple YAML parsing
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key_clean = key.strip().lower()
                        frontmatter[key_clean] = value.strip()

    # 默认值
    result = {
        'task_id': frontmatter.get('task_id', 'UNKNOWN'),
        'title': frontmatter.get('title', 'Untitled Task'),
        'priority': frontmatter.get('priority', 'Medium'),
        'status': frontmatter.get('status', '草稿'),
        'dependencies': frontmatter.get('dependencies', []),
        'content': markdown_content.strip(),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'file_path': filepath,
    }

    logger.info(f"✅ Parsed task: {result['task_id']} - {result['title']}")
    return result


# ============================================================================
# Validator: 验证 Notion Token
# ============================================================================


def validate_token(token: Optional[str] = None) -> bool:
    """
    验证 Notion Token 的有效性。

    Args:
        token: Notion Token (如果为空则从环境变量读取)

    Returns:
        True if token is valid
    """
    token = token or NOTION_TOKEN

    if not token:
        logger.error("❌ NOTION_TOKEN not found in environment or arguments")
        return False

    try:
        client = Client(auth=token)
        # 尝试获取用户信息来验证 token
        user = client.users.me()
        user_name = user.get('name', 'Unknown')
        logger.info(f"✅ Notion Token validated. User: {user_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Token validation failed: {str(e)}")
        return False


# ============================================================================
# Pusher: 推送任务到 Notion
# ============================================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _push_to_notion_with_retry(
    client: Client,
    task_metadata: Dict[str, Any],
    database_id: str,
) -> Dict[str, Any]:
    """内部函数：执行带重试的 Notion 推送"""
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": (
                            task_metadata.get('title', 'Untitled')[:100]
                        ),
                    }
                }
            ]
        },
    }

    # 添加自定义字段 (如果数据库支持)
    if task_metadata.get('task_id'):
        properties["Task ID"] = {
            "rich_text": [
                {
                    "text": {
                        "content": task_metadata['task_id'],
                    }
                }
            ]
        }

    if task_metadata.get('priority'):
        properties["Priority"] = {
            "select": {
                "name": task_metadata['priority'],
            }
        }

    if task_metadata.get('status'):
        properties["Status"] = {
            "select": {
                "name": task_metadata['status'],
            }
        }

    # 创建 Page
    logger.info(f"Pushing task {task_metadata['task_id']} to Notion...")
    time.sleep(NOTION_API_RATE_LIMIT)  # Rate limiting

    response = client.pages.create(
        parent={"database_id": database_id},
        properties=properties,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    task_metadata.get('content', '')[:2000]
                                ),
                            },
                        }
                    ]
                },
            }
        ],
    )

    return response


def push_to_notion(
    task_metadata: Dict[str, Any],
    database_id: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    将任务推送到 Notion 数据库（带 tenacity 重试机制）。

    Args:
        task_metadata: 任务元数据 (from parse_markdown_task)
        database_id: Notion Database ID
        token: Notion Token

    Returns:
        {
            'page_id': 'xxx',
            'page_url': 'https://notion.so/xxx',
            'status': 'created'
        }
    """
    token = token or NOTION_TOKEN
    database_id = database_id or NOTION_TASK_DATABASE_ID

    if not token or not database_id:
        logger.error(
            "❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID"
        )
        raise ValueError("Missing required Notion credentials")

    try:
        client = Client(auth=token)
        logger.info(f"[RETRY] Attempting to push {task_metadata.get('task_id')} with tenacity...")

        # 调用带重试机制的内部函数
        response = _push_to_notion_with_retry(
            client,
            task_metadata,
            database_id,
        )

        page_id = response['id']
        page_url = response.get(
            'url', f"https://notion.so/{page_id}"
        )

        result = {
            'page_id': page_id,
            'page_url': page_url,
            'status': 'created',
            'task_id': task_metadata['task_id'],
            'created_at': response.get('created_time', ''),
        }

        logger.info(f"✅ Task pushed to Notion: {page_url}")
        return result

    except Exception as e:
        logger.error(f"❌ Failed to push task to Notion after retries: {str(e)}")
        raise


# ============================================================================
# CLI Interface
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Notion Bridge - 推送任务到 Notion"
    )

    parser.add_argument(
        "--action",
        required=True,
        choices=["parse", "validate-token", "push", "test"],
        help="执行的操作",
    )

    parser.add_argument(
        "--input",
        help="输入文件路径 (Markdown 或 JSON)",
    )

    parser.add_argument(
        "--token",
        help="Notion Token (默认从 $NOTION_TOKEN 读取)",
    )

    parser.add_argument(
        "--database-id",
        help="Notion Database ID (默认从 $NOTION_DB_ID 读取)",
    )

    parser.add_argument(
        "--output",
        help="输出文件路径 (JSON 格式)",
    )

    args = parser.parse_args()

    try:
        if args.action == "parse":
            if not args.input:
                logger.error("❌ --input required for parse action")
                sys.exit(1)

            result = parse_markdown_task(args.input)

            # 输出结果
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"✅ Parsed result saved to {args.output}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.action == "validate-token":
            token = args.token or NOTION_TOKEN
            is_valid = validate_token(token)
            sys.exit(0 if is_valid else 1)

        elif args.action == "push":
            if not args.input:
                logger.error("❌ --input required for push action")
                sys.exit(1)

            # 读取任务元数据
            with open(args.input, 'r') as f:
                task_metadata = json.load(f)

            result = push_to_notion(
                task_metadata,
                database_id=args.database_id,
                token=args.token,
            )

            # 输出结果
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"✅ Push result saved to {args.output}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.action == "test":
            logger.info("🧪 Running self-tests...")

            # Test 1: Validate token
            logger.info("Test 1: Validating Notion Token...")
            if not validate_token():
                logger.error("❌ Test 1 FAILED")
                sys.exit(1)

            # Test 2: Parse sample task
            logger.info("Test 2: Parsing sample task...")
            sample_task = {
                'task_id': 'TASK#999',
                'title': 'Test Task from notion_bridge.py',
                'priority': 'High',
                'status': '进行中',
                'dependencies': [],
                'content': (
                    'This is a test task created by '
                    'notion_bridge.py self-test.'
                ),
                'created_at': datetime.utcnow().isoformat() + 'Z',
            }

            # Test 3: Push to Notion (can be skipped if in demo mode)
            logger.info(
                "Test 3: Pushing test task to Notion "
                "(DEMO MODE - set --database-id to enable)..."
            )
            if args.database_id:
                try:
                    result = push_to_notion(
                        sample_task, database_id=args.database_id
                    )
                    logger.info(f"✅ Test 3 PASSED: {result['page_url']}")
                except Exception as e:
                    logger.error(f"❌ Test 3 FAILED: {str(e)}")
                    sys.exit(1)
            else:
                logger.info(
                    "⏭️  Test 3 SKIPPED (no --database-id provided)"
                )

            logger.info("✅ All tests completed!")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

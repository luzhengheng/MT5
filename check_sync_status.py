#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS 同步状态检查脚本
检查 Git-Notion 同步系统健康状态
"""

import os
import subprocess
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

def check_git_status():
    """检查 Git 状态"""
    print("🔍 检查 Git 状态...")

    try:
        # 检查是否有未提交的更改
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True
        ).strip()

        uncommitted = len(status.split('\n')) if status else 0

        # 获取最新提交信息
        latest_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%H|%an|%s|%cd", "--date=iso"],
            text=True
        ).strip().split('|')

        return {
            "uncommitted_changes": uncommitted,
            "latest_commit": {
                "hash": latest_commit[0],
                "author": latest_commit[1],
                "message": latest_commit[2],
                "date": latest_commit[3]
            },
            "status": "healthy" if uncommitted < 10 else "warning"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_notion_connectivity():
    """检查 Notion 连接性"""
    print("🔍 检查 Notion 连接...")

    if not NOTION_TOKEN:
        return {"status": "error", "error": "NOTION_TOKEN 未配置"}

    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        response = requests.get(
            "https://api.notion.com/v1/users/me",
            headers=headers
        )

        if response.status_code == 200:
            user_info = response.json()
            return {
                "status": "healthy",
                "user": user_info.get("name", "Unknown"),
                "email": user_info.get("person", {}).get("email", "Unknown")
            }
        else:
            return {
                "status": "error",
                "error": f"API Error: {response.status_code}"
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_file_sync_status():
    """检查关键文件同步状态"""
    print("🔍 检查文件同步状态...")

    key_files = [
        "src/strategy/risk_manager.py",
        "nexus_with_proxy.py",
        "src/feature_engineering/",
        "docs/ML_ADVANCED_GUIDE.md"
    ]

    sync_status = {}

    for file_path in key_files:
        full_path = os.path.join("/opt/mt5-crs", file_path)

        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                # 目录：检查 Python 文件数量
                py_files = [f for f in os.listdir(full_path) if f.endswith('.py')]
                sync_status[file_path] = {
                    "exists": True,
                    "type": "directory",
                    "files": len(py_files),
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(full_path)
                    ).isoformat()
                }
            else:
                # 文件
                sync_status[file_path] = {
                    "exists": True,
                    "type": "file",
                    "size": os.path.getsize(full_path),
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(full_path)
                    ).isoformat()
                }
        else:
            sync_status[file_path] = {"exists": False}

    return sync_status

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 MT5-CRS 同步状态检查")
    print(f"⏰ 检查时间: {datetime.now().isoformat()}")
    print("=" * 60)

    # 检查 Git 状态
    git_status = check_git_status()
    print(f"\n📊 Git 状态: {git_status['status']}")
    if git_status['status'] == 'healthy':
        print(f"   ✅ 最新提交: {git_status['latest_commit']['message']}")
        print(f"   📝 未提交更改: {git_status['uncommitted_changes']} 个文件")

    # 检查 Notion 连接
    notion_status = check_notion_connectivity()
    print(f"\n🔗 Notion 状态: {notion_status['status']}")
    if notion_status['status'] == 'healthy':
        print(f"   ✅ 用户: {notion_status['user']}")

    # 检查文件同步
    file_status = check_file_sync_status()
    print(f"\n📁 文件同步状态:")
    for file_path, status in file_status.items():
        if status['exists']:
            if status['type'] == 'directory':
                print(f"   ✅ {file_path}: {status['files']} 个文件")
            else:
                print(f"   ✅ {file_path}: {status['size']} bytes")
        else:
            print(f"   ❌ {file_path}: 不存在")

    # 整体健康状态
    overall_status = "healthy"
    if git_status['status'] != 'healthy' or notion_status['status'] != 'healthy':
        overall_status = "error"
    elif git_status['uncommitted_changes'] > 10:
        overall_status = "warning"

    print(f"\n🎯 整体状态: {overall_status}")

    if overall_status == "healthy":
        print("✅ 所有系统运行正常")
    elif overall_status == "warning":
        print("⚠️ 系统运行正常，但建议清理未提交更改")
    else:
        print("❌ 发现问题，请检查上述错误")

    return overall_status

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量同步所有工单到 Notion Issues 数据库
"""

import os
import sys
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

# 工单数据定义
ISSUES = [
    {
        "id": "#001",
        "name": "项目初始化与环境配置",
        "status": "已完成",
        "priority": "P0",
        "type": "Infrastructure",
        "description": "搭建基础开发环境，配置 Python、Git 等工具"
    },
    {
        "id": "#002",
        "name": "数据采集模块开发",
        "status": "已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "实现 MT5 历史数据和新闻数据采集器"
    },
    {
        "id": "#003",
        "name": "数据存储与管理",
        "status": "已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "Parquet 存储格式，事件驱动检查点机制"
    },
    {
        "id": "#004",
        "name": "基础特征工程",
        "status": "已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "35 个基础特征：技术指标、价格特征、成交量特征"
    },
    {
        "id": "#005",
        "name": "高级特征工程",
        "status": "已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "40 个高级特征：分数差分、滚动统计、横截面排名等"
    },
    {
        "id": "#006",
        "name": "驱动管家系统",
        "status": "已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "三重障碍标签法，多维度标签系统"
    },
    {
        "id": "#007",
        "name": "数据质量监控系统",
        "status": "已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "DQ Score 计算器，Prometheus + Grafana 监控"
    },
    {
        "id": "#008",
        "name": "MT5-CRS 数据管线与特征工程平台",
        "status": "已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "完整的数据管线，75+ 特征维度，14,500+ 行代码"
    },
    {
        "id": "#009",
        "name": "机器学习模型训练",
        "status": "已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "监督学习模型，特征选择，模型评估"
    },
    {
        "id": "#010",
        "name": "回测系统",
        "status": "已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "ML 策略回测，Kelly 仓位管理，风险控制"
    },
    {
        "id": "#010.5",
        "name": "回测系统优化与修复",
        "status": "已完成",
        "priority": "P0",
        "type": "Bug",
        "description": "修复 Kelly 计算，优化回测引擎"
    },
    {
        "id": "#010.9",
        "name": "部署 Notion Nexus 知识库与自动化架构",
        "status": "已完成",
        "priority": "P1",
        "type": "Infrastructure",
        "description": "Git-Notion 自动同步，知识库建设"
    },
    {
        "id": "#011",
        "name": "MT5 实盘交易系统对接",
        "status": "进行中",
        "priority": "P0",
        "type": "Feature",
        "description": "MT5 API 对接，实盘交易系统集成"
    },
    {
        "id": "#011.1",
        "name": "部署 AI 跨会话持久化规则",
        "status": "已完成",
        "priority": "P0",
        "type": "Infrastructure",
        "description": "AI Rules 文件部署，DevOps 工作流固化"
    },
    {
        "id": "#P1",
        "name": "P1 优先级任务完成报告",
        "status": "已完成",
        "priority": "P1",
        "type": "Docs",
        "description": "P1 阶段工作总结"
    },
    {
        "id": "#P2",
        "name": "P2 优先级任务",
        "status": "进行中",
        "priority": "P2",
        "type": "Feature",
        "description": "P2 阶段任务规划"
    }
]

def create_issue_page(issue):
    """创建单个工单页面"""

    # 构建属性
    properties = {
        "名称": {
            "title": [
                {
                    "text": {
                        "content": issue["name"]
                    }
                }
            ]
        }
    }

    # 如果数据库支持更多属性，添加它们
    # 注意：需要先在数据库中创建这些属性

    data = {
        "parent": {
            "database_id": ISSUES_DB_ID
        },
        "properties": properties
    }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=notion_headers(),
        json=data
    )

    return response

def main():
    print("=" * 80)
    print("🚀 批量同步工单到 Notion Issues")
    print("=" * 80)
    print()

    # 验证配置
    if not NOTION_TOKEN:
        print("❌ 错误: NOTION_TOKEN 未配置")
        sys.exit(1)

    if not ISSUES_DB_ID:
        print("❌ 错误: NOTION_ISSUES_DB_ID 未配置")
        sys.exit(1)

    print(f"📊 数据库 ID: {ISSUES_DB_ID}")
    print(f"📝 待同步工单数: {len(ISSUES)} 个")
    print()

    # 先检查数据库当前内容
    print("🔍 检查数据库当前内容...")
    response = requests.post(
        f"https://api.notion.com/v1/databases/{ISSUES_DB_ID}/query",
        headers=notion_headers(),
        json={"page_size": 100}
    )

    if response.status_code != 200:
        print(f"❌ 查询数据库失败: {response.text}")
        sys.exit(1)

    existing_pages = response.json().get("results", [])
    print(f"   当前数据库中有 {len(existing_pages)} 个页面")
    print()

    # 批量创建工单
    success_count = 0
    fail_count = 0

    print("📥 开始导入工单...")
    print("-" * 80)

    for i, issue in enumerate(ISSUES, 1):
        print(f"{i:2d}. 创建工单 {issue['id']}: {issue['name']}")

        response = create_issue_page(issue)

        if response.status_code == 200:
            print(f"    ✅ 成功")
            success_count += 1
        else:
            print(f"    ❌ 失败: {response.status_code}")
            print(f"    错误: {response.text[:200]}")
            fail_count += 1

        print()

    # 总结
    print("-" * 80)
    print()
    print("=" * 80)
    print("📊 导入完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    print(f"📈 成功率: {success_count / len(ISSUES) * 100:.1f}%")
    print()

    if success_count > 0:
        print("🎉 工单已成功导入到 Notion Issues!")
        print(f"🔗 查看: https://www.notion.so/{ISSUES_DB_ID.replace('-', '')}")

    print("=" * 80)

if __name__ == "__main__":
    main()

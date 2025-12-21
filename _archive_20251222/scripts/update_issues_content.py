#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 Notion Issues 工单内容
为每个工单页面添加详细信息
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ISSUES_DB_ID = os.getenv("NOTION_ISSUES_DB_ID")

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

# 工单详细信息
ISSUES_DETAILS = {
    "项目初始化与环境配置": {
        "id": "#001",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Infrastructure",
        "description": "搭建基础开发环境，配置 Python、Git、依赖管理等工具"
    },
    "数据采集模块开发": {
        "id": "#002",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "实现 MT5 历史数据和新闻数据采集器，支持多品种、多时间周期"
    },
    "数据存储与管理": {
        "id": "#003",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "Parquet 存储格式（gzip 压缩），事件驱动检查点机制（支持断点续传）"
    },
    "基础特征工程": {
        "id": "#004",
        "status": "✅ 已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "35 个基础特征维度：技术指标（SMA, EMA, RSI, MACD, Bollinger Bands, ATR）、价格特征、成交量特征"
    },
    "高级特征工程": {
        "id": "#005",
        "status": "✅ 已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "40 个高级特征维度：分数差分、滚动统计、横截面排名、情绪动量、自适应窗口、跨资产特征等"
    },
    "驱动管家系统": {
        "id": "#006",
        "status": "✅ 已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "三重障碍标签法，多维度标签系统，科学的样本标注方法"
    },
    "数据质量监控系统": {
        "id": "#007",
        "status": "✅ 已完成",
        "priority": "P1",
        "type": "Feature",
        "description": "DQ Score 计算器（5维评分），Prometheus 导出器，Grafana 仪表盘，10条告警规则"
    },
    "MT5-CRS 数据管线与特征工程平台": {
        "id": "#008",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "完整的数据管线，75+ 特征维度，14,500+ 行代码，6个迭代全部完成"
    },
    "机器学习模型训练": {
        "id": "#009",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "监督学习模型（LightGBM, XGBoost, Random Forest），特征选择，模型评估，交叉验证"
    },
    "回测系统": {
        "id": "#010",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Feature",
        "description": "ML 策略回测引擎，Kelly 仓位管理，风险控制（CircuitBreaker），性能分析（Sharpe Ratio, Max Drawdown）"
    },
    "回测系统优化与修复": {
        "id": "#010.5",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Bug",
        "description": "修复 Kelly 计算 bug（分数差分导致的非平稳性），优化回测引擎性能"
    },
    "部署 Notion Nexus 知识库与自动化架构": {
        "id": "#010.9",
        "status": "✅ 已完成",
        "priority": "P1",
        "type": "Infrastructure",
        "description": "Git-Notion 自动同步，知识库建设，Gemini AI 审查集成"
    },
    "MT5 实盘交易系统对接": {
        "id": "#011",
        "status": "🔄 进行中",
        "priority": "P0",
        "type": "Feature",
        "description": "MT5 API 对接，实盘交易系统集成，Windows-Linux 跨平台通信，SSH 隧道配置"
    },
    "部署 AI 跨会话持久化规则": {
        "id": "#011.1",
        "status": "✅ 已完成",
        "priority": "P0",
        "type": "Infrastructure",
        "description": "AI Rules 文件部署（.cursorrules, AI_RULES.md），DevOps 工作流固化，Notion 双数据库配置"
    },
    "P1 优先级任务完成报告": {
        "id": "#P1",
        "status": "✅ 已完成",
        "priority": "P1",
        "type": "Docs",
        "description": "P1 阶段工作总结，完成报告"
    },
    "P2 优先级任务": {
        "id": "#P2",
        "status": "🔄 进行中",
        "priority": "P2",
        "type": "Feature",
        "description": "P2 阶段任务规划"
    }
}

def update_page_content(page_id, title, details):
    """更新页面内容"""

    # 构建页面内容块
    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": f"工单 {details['id']}"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "状态: ", "link": None}, "annotations": {"bold": True}},
                    {"text": {"content": details['status']}}
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "优先级: ", "link": None}, "annotations": {"bold": True}},
                    {"text": {"content": details['priority']}}
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "类型: ", "link": None}, "annotations": {"bold": True}},
                    {"text": {"content": details['type']}}
                ]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"text": {"content": "描述"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": details['description']}}]
            }
        }
    ]

    # 更新页面内容
    response = requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=notion_headers(),
        json={"children": blocks}
    )

    return response

def main():
    print("=" * 80)
    print("🔄 更新 Notion Issues 工单内容")
    print("=" * 80)
    print()

    # 查询所有工单
    print("📋 查询数据库中的工单...")
    response = requests.post(
        f"https://api.notion.com/v1/databases/{ISSUES_DB_ID}/query",
        headers=notion_headers(),
        json={"page_size": 100}
    )

    if response.status_code != 200:
        print(f"❌ 查询失败: {response.text}")
        sys.exit(1)

    pages = response.json().get("results", [])
    print(f"   找到 {len(pages)} 个工单")
    print()

    # 更新每个工单
    success_count = 0
    fail_count = 0

    print("🔧 开始更新工单内容...")
    print("-" * 80)

    for i, page in enumerate(pages, 1):
        page_id = page["id"]
        props = page.get("properties", {})

        # 获取标题
        title_data = props.get("名称", {})
        if "title" in title_data and title_data["title"]:
            title = title_data["title"][0].get("plain_text", "")
        else:
            title = "N/A"

        print(f"{i:2d}. {title}")

        # 查找对应的详细信息
        if title in ISSUES_DETAILS:
            details = ISSUES_DETAILS[title]

            # 更新页面内容
            response = update_page_content(page_id, title, details)

            if response.status_code == 200:
                print(f"    ✅ 已更新内容")
                success_count += 1
            else:
                print(f"    ❌ 更新失败: {response.status_code}")
                print(f"    错误: {response.text[:200]}")
                fail_count += 1
        else:
            print(f"    ⚠️  未找到详细信息")
            fail_count += 1

        print()

    # 总结
    print("-" * 80)
    print()
    print("=" * 80)
    print("📊 更新完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    print(f"📈 成功率: {success_count / len(pages) * 100:.1f}%")
    print()
    print("🎉 工单内容已更新！")
    print(f"🔗 查看: https://www.notion.so/{ISSUES_DB_ID.replace('-', '')}")
    print("=" * 80)

if __name__ == "__main__":
    main()

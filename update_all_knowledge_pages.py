#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新 Notion 知识库所有页面
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
KNOWLEDGE_DB_ID = os.getenv("NOTION_KNOWLEDGE_DB_ID")

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def clear_page_content(page_id):
    """清除页面现有内容"""
    blocks_response = requests.get(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=notion_headers()
    )

    if blocks_response.status_code == 200:
        existing_blocks = blocks_response.json().get("results", [])
        for block in existing_blocks:
            requests.delete(
                f"https://api.notion.com/v1/blocks/{block['id']}",
                headers=notion_headers()
            )

def update_page_content(page_id, blocks):
    """更新页面内容"""
    response = requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=notion_headers(),
        json={"children": blocks}
    )
    return response

# ============================================================================
# 页面内容定义
# ============================================================================

def get_current_status_blocks():
    """当前开发状态"""
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": f"📅 最后更新: {current_date}"}}],
                "icon": {"emoji": "🔄"},
                "color": "blue_background"
            }
        },
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "🎯 MT5-CRS 项目当前状态"}}]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📊 总体进度"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "总工单数: 16 个"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "已完成: 14 个 (87.5%)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "进行中: 2 个 (#011 MT5实盘系统, #P2)"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🚀 当前焦点"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"text": {"content": "#011 - MT5 实盘交易系统对接", "link": None}, "annotations": {"bold": True}}
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "优先级: P0 (最高)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "目标: MT5 API 对接，实盘交易系统集成"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "✅ 已完成核心功能"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#008 - MT5-CRS 数据管线 (14,500+ 行, 75+ 特征)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#009 - 机器学习模型训练"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#010 - 回测系统 (Kelly 仓位管理)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#011.1 - AI 规则持久化 (Git-Notion 自动同步)"}}]
            }
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": "🎯 下一步: 完成 MT5 实盘对接，进入实盘交易"}}],
                "icon": {"emoji": "🚀"},
                "color": "green_background"
            }
        }
    ]

def get_system_overview_blocks():
    """系统概述"""
    return [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "📋 MT5-CRS 系统概述"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "MT5-CRS (MetaTrader 5 - Cryptocurrency Trading System) 是一个基于机器学习的量化交易系统。"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🎯 核心目标"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "构建端到端的量化交易系统"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "实现数据驱动的交易决策"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "严格的风险控制与仓位管理"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🏗️ 系统架构"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "数据采集层 - MT5历史数据、新闻数据"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "特征工程层 - 75+ 维特征"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "机器学习层 - LightGBM/XGBoost/RF"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "回测验证层 - 策略回测与评估"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "实盘交易层 - MT5 API 对接"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📈 项目统计"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "总代码量: 14,500+ 行"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "特征维度: 75+"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "测试覆盖: 95+ 测试方法"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "监控系统: Prometheus + Grafana"}}]
            }
        }
    ]

def get_tech_architecture_blocks():
    """技术架构"""
    return [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "🏗️ 技术架构详解"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "💻 技术栈"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Python 3.10+ - 主要开发语言", "link": None}, "annotations": {"bold": True}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Pandas/NumPy - 数据处理"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "LightGBM/XGBoost - 机器学习"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Parquet - 数据存储"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Prometheus/Grafana - 监控系统"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Pytest - 测试框架"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📦 核心模块"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "src/data_collection/ - 数据采集"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "src/feature_engineering/ - 特征工程"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "src/models/ - 机器学习模型"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "src/strategy/ - 交易策略"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "src/monitoring/ - 监控系统"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🔧 DevOps 工具链"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Git - 版本控制"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "GitHub - 代码托管"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Notion - 知识库与工单管理"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Git Hooks - 自动化同步"}}]
            }
        }
    ]

def get_github_notion_sync_blocks():
    """Notion-GitHub 协同机制"""
    return [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "🔗 Notion-GitHub 协同机制"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "实现三方自动同步：GitHub ⟷ Notion 知识库 ⟷ Notion Issues"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "⚙️ 工作流程"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "开发者提交代码 (git commit -m \"type(scope): desc #工单号\")"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "Git Hook 自动触发"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "代码推送到 GitHub"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "Notion 工单自动更新"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "知识库记录技术要点"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🎯 核心组件"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": ".git/hooks/pre-commit - 提交前检查"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": ".git/hooks/post-commit - 提交后同步"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "update_notion_from_git.py - Notion 更新脚本"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "MT5-CRS-Bot - Notion 集成"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "✅ 当前状态"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ GitHub 远程仓库 - 正常运行"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Notion 知识库 - 已连接"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Notion Issues - 16个工单已同步"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Git Hook - 自动同步正常"}}]
            }
        }
    ]

def get_project_history_blocks():
    """项目历史脉络"""
    return [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "📚 项目历史脉络"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🎯 第一阶段：基础设施 (#001-#003)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#001 - 项目初始化与环境配置 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#002 - 数据采集模块开发 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#003 - 数据存储与管理 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🚀 第二阶段：特征工程 (#004-#007)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#004 - 基础特征工程 (35维) ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#005 - 高级特征工程 (40维) ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#006 - 驱动管家系统 (标签法) ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#007 - 数据质量监控 (DQ Score) ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🤖 第三阶段：机器学习 (#008-#010)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#008 - 数据管线完整平台 (14,500+ 行) ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#009 - 机器学习模型训练 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#010 - 回测系统 (Kelly 仓位) ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#010.5 - 回测优化与修复 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🔧 第四阶段：DevOps 自动化 (#010.9, #011.1)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#010.9 - Notion Nexus 知识库 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#011.1 - AI 规则持久化 ✅"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🎯 第五阶段：实盘交易 (#011)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "#011 - MT5 实盘系统对接 🔄 进行中"}}]
            }
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": "总计: 16 个工单，14 个已完成 (87.5%)"}}],
                "icon": {"emoji": "📊"},
                "color": "blue_background"
            }
        }
    ]

def get_project_status_blocks():
    """项目状态"""
    return [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "📊 项目详细状态"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📈 代码统计"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "总代码量: 14,500+ 行"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "特征维度: 75+ 个"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "测试方法: 95+ 个"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "代码覆盖率: ~85%"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🎯 工单进度"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "总工单: 16 个"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "已完成: 14 个 (87.5%)"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "进行中: 2 个 (#011, #P2)"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🏆 核心成就"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ 完整的数据管线与特征工程平台"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ 机器学习模型训练系统"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ Kelly 仓位管理回测系统"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "✅ GitHub-Notion 三方自动同步"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🔜 下一步计划"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "完成 MT5 实盘系统对接"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "实盘环境测试与验证"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "小额资金实盘运行"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "策略优化与迭代"}}]
            }
        }
    ]

def get_usage_guide_blocks():
    """使用指南"""
    return [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"text": {"content": "📖 MT5-CRS 使用指南"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🚀 快速开始"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "克隆仓库: git clone https://github.com/luzhengheng/MT5.git"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "安装依赖: pip install -r requirements.txt"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "配置环境: 复制 .env.example 为 .env 并填入配置"}}]
            }
        },
        {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": "运行测试: pytest tests/"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📊 核心功能使用"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "数据采集: python bin/collect_data.py", "link": None}, "annotations": {"code": True}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "特征工程: python bin/generate_features.py", "link": None}, "annotations": {"code": True}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "模型训练: python bin/train_ml_model.py", "link": None}, "annotations": {"code": True}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "回测: python bin/run_backtest.py", "link": None}, "annotations": {"code": True}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "🔧 Git 提交规范"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "格式: type(scope): description #issue-id", "link": None}, "annotations": {"code": True}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "type: feat, fix, docs, refactor, test, chore"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "scope: mt5, strategy, risk, docs, infra"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "必须包含工单号 #xxx"}}]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📚 文档资源"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "README.md - 项目概述"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "docs/ - 详细文档"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Notion 知识库 - 技术知识沉淀"}}]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": "Notion Issues - 工单进度跟踪"}}]
            }
        }
    ]

# ============================================================================
# 主程序
# ============================================================================

# 页面内容映射
PAGE_CONTENT_MAP = {
    "当前开发状态": get_current_status_blocks,
    "系统概述": get_system_overview_blocks,
    "技术架构": get_tech_architecture_blocks,
    "Notion-GitHub 协同机制": get_github_notion_sync_blocks,
    "项目历史脉络": get_project_history_blocks,
    "项目状态": get_project_status_blocks,
    "使用指南": get_usage_guide_blocks
}

def main():
    print("=" * 80)
    print("🔄 批量更新 Notion 知识库所有页面")
    print("=" * 80)
    print()

    # 查询所有页面
    print("📋 查询知识库页面...")
    response = requests.post(
        f"https://api.notion.com/v1/databases/{KNOWLEDGE_DB_ID}/query",
        headers=notion_headers(),
        json={"page_size": 100}
    )

    if response.status_code != 200:
        print(f"❌ 查询失败: {response.text}")
        sys.exit(1)

    pages = response.json().get("results", [])
    print(f"   找到 {len(pages)} 个页面")
    print()

    # 更新每个页面
    success_count = 0
    skip_count = 0
    fail_count = 0

    print("🔧 开始更新页面...")
    print("-" * 80)

    for i, page in enumerate(pages, 1):
        page_id = page["id"]
        props = page.get("properties", {})

        # 获取标题
        title_data = props.get("名称", props.get("Name", {}))
        if "title" in title_data and title_data["title"]:
            title = title_data["title"][0].get("plain_text", "")
        else:
            title = "N/A"

        print(f"{i}. {title}")

        # 查找对应的内容生成函数
        content_func = None
        for keyword, func in PAGE_CONTENT_MAP.items():
            if keyword in title:
                content_func = func
                break

        if content_func:
            # 清除现有内容
            clear_page_content(page_id)

            # 获取新内容
            blocks = content_func()

            # 更新页面
            response = update_page_content(page_id, blocks)

            if response.status_code == 200:
                print(f"   ✅ 更新成功")
                success_count += 1
            else:
                print(f"   ❌ 更新失败: {response.status_code}")
                print(f"   错误: {response.text[:200]}")
                fail_count += 1
        else:
            print(f"   ⚠️  未找到内容模板，跳过")
            skip_count += 1

        print()

    # 总结
    print("-" * 80)
    print()
    print("=" * 80)
    print("📊 更新完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个")
    print(f"⚠️  跳过: {skip_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    print(f"📈 成功率: {success_count / len(pages) * 100:.1f}%")
    print()
    print("🎉 知识库已全部更新！")
    print(f"🔗 查看: https://www.notion.so/{KNOWLEDGE_DB_ID.replace('-', '')}")
    print("=" * 80)

if __name__ == "__main__":
    main()

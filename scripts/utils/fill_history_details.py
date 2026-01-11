#!/usr/bin/env python3
"""
MT5-CRS History Content Injection Script
Purpose: Populate historical task pages with rich technical summaries and code snippets
Created: 2025-12-23
Author: Claude Sonnet 4.5 (Lead Architect)
"""

import os
import sys
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Notion API Configuration
TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = os.getenv("NOTION_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Historical Content Knowledge Base
HISTORY_CONTENT = {
    "#001": {
        "summary": "### 系统环境\n- **OS**: CentOS 7.9 x64 (阿里云 ECS)\n- **Python**: 3.9.18 (Miniconda 环境)\n- **Shell**: Zsh + Oh My Zsh + Powerlevel10k\n",
        "code": "pip install pandas numpy metatrader5 notion-client requests pytz",
        "lang": "bash"
    },
    "#002": {
        "summary": "### 核心逻辑\n- 使用 `mt5.copy_rates_from_pos` 获取指定品种的 OHLC 数据。\n- 实现了自动时区转换 (UTC+0 -> UTC+8)。\n- 数据清洗：去除了非交易时段（周末）的无效 Tick。",
        "code": "rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)\ndf = pd.DataFrame(rates)\ndf['time'] = pd.to_datetime(df['time'], unit='s')",
        "lang": "python"
    },
    "#003": {
        "summary": "### 架构选型\n选择 **TimescaleDB** (PostgreSQL 扩展) 作为核心行情数据库。\n- **优势**: 支持标准 SQL，且针对时序数据有高压缩率。\n- **超表设计**: 按时间分片 (Chunking) 存储 `ticks` 和 `candles`。",
        "code": "SELECT create_hypertable('market_ticks', 'time');\nCREATE INDEX ON market_ticks (symbol, time DESC);",
        "lang": "sql"
    },
    "#004": {
        "summary": "### 基础特征工程\n集成 `TA-Lib` 库，实现了 35+ 基础技术指标：\n- **趋势类**: MACD, EMA, SMA, ADX\n- **震荡类**: RSI, KDJ, CCI\n- **波动类**: ATR, Bollinger Bands",
        "code": "df['rsi'] = talib.RSI(df['close'], timeperiod=14)\ndf['upper'], df['middle'], df['lower'] = talib.BBANDS(df['close'])",
        "lang": "python"
    },
    "#005": {
        "summary": "### 高级特征工程\n- **分数差分 (Fractional Diff)**: 在保留数据记忆性(Memory)和实现平稳性(Stationarity)之间寻找最优 d 值。\n- **三重障碍法 (Triple Barrier)**: 为机器学习生成更科学的标签 (Label)，包含上止盈、下止损和时间过期三个维度。",
        "code": "# 分数差分核心公式\nw = [1, -d, d(d-1)/2, ...]",
        "lang": "python"
    },
    "#006": {
        "summary": "### Linux 运行方案\n由于 MT5 只有 Windows 版，在 CentOS 上采用以下方案实现无头运行：\n1. **Wine 8.0**: Windows 兼容层\n2. **Xvfb**: 虚拟帧缓冲 (Virtual Framebuffer) 模拟显示器\n3. **VNC**: 远程桌面连接用于调试",
        "code": "Xvfb :1 -screen 0 1024x768x16 &\nDISPLAY=:1 wine terminal64.exe /portable",
        "lang": "bash"
    },
    "#007": {
        "summary": "### 数据质量监控 (DQ Score)\n- **完整性**: 检查分钟线时间戳是否连续，无缺失。\n- **准确性**: 监控价格是否偏离 3-sigma 阈值。\n- **告警**: 异常情况推送到 Notion 和钉钉机器人。",
        "code": "missing_count = expected_ticks - actual_ticks\nquality_score = 100 - (missing_count / total * 100)",
        "lang": "python"
    },
    "#008": {
        "summary": "### 文档体系规范\n建立了 `docs/` 目录的标准结构：\n- `docs/arch`: 系统架构图 (Mermaid/PlantUML)\n- `docs/api`: 接口定义与协议\n- `docs/runbooks`: 运维操作手册 (SOP)",
        "code": "docs/\n├── arch/\n├── api/\n└── issues/  # 自动生成的工单记录",
        "lang": "plain text"
    },
    "#009": {
        "summary": "### 机器学习管线\n- **模型栈**: XGBoost (Baseline) + LightGBM (主力) + CatBoost。\n- **调优**: 使用 `Optuna` 进行贝叶斯优化，寻找最优超参数。\n- **验证**: 采用 Walk-forward Analysis (滚动窗口验证) 防止过拟合。",
        "code": "study = optuna.create_study(direction='maximize')\nstudy.optimize(objective, n_trials=100)",
        "lang": "python"
    },
    "#010": {
        "summary": "### 回测系统\n基于 `Backtrader` 框架深度定制。\n- **核心指标**: Sharpe Ratio, Max Drawdown, CAGR。\n- **增强**: 增加了滑点 (Slippage) 和手续费 (Commission) 模拟，使回测更贴近实盘。",
        "code": "cerebro.addsizer(bt.sizers.FixedSize, stake=1)\ncerebro.broker.setcommission(commission=0.0001)",
        "lang": "python"
    },
    "#011": {
        "summary": "### Notion 自动化集成\n实现了 `Notion-Git` 双向同步工具链：\n- **Review Bridge**: 自动将 Git Commit 转换为 Notion 评论。\n- **Issue Sync**: 命令行创建和更新 Notion 工单。\n- **Wiki Seed**: 自动初始化知识库页面。",
        "code": "python scripts/quick_create_issue.py \"New Feature\" --type Core",
        "lang": "bash"
    },
    "#012": {
        "summary": "### 交易网关通信架构\n放弃了高延迟的 HTTP 轮询，采用 **ZeroMQ (ZMQ)** 实现毫秒级通讯。\n- **PUB 模式**: MT5 终端广播实时 Tick 数据。\n- **REP 模式**: 接收 Python 端的交易指令并返回结果。",
        "code": "context = zmq.Context()\nsocket = context.socket(zmq.PUB)\nsocket.bind(\"tcp://*:5555\")",
        "lang": "python"
    },
    "#013": {
        "summary": "### 工作区重构 (中文标准)\n- **Schema 对齐**: 将 Status/Priority 等英文字段映射为\"状态\"、\"优先级\"。\n- **数据清洗**: 彻底重建了数据库，消除了历史脏数据。\n- **自动化升级**: 升级了所有 Python 脚本以适配中文 API 键名。",
        "code": "\"properties\": {\n  \"状态\": {\"status\": {\"name\": \"已完成\"}}\n}",
        "lang": "json"
    }
}


def search_page_by_title(title_prefix: str) -> Optional[str]:
    """
    Search for a page in the database by title prefix

    Args:
        title_prefix: The title prefix to search for (e.g., "#001")

    Returns:
        Page ID if found, None otherwise
    """
    url = f"https://api.notion.com/v1/databases/{DB_ID}/query"

    payload = {
        "filter": {
            "property": "标题",
            "title": {
                "starts_with": title_prefix
            }
        }
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            page_id = data["results"][0]["id"]
            title = data["results"][0]["properties"]["标题"]["title"][0]["text"]["content"]
            return page_id, title
        else:
            return None, None

    except Exception as e:
        print(f"❌ Search error for {title_prefix}: {e}")
        return None, None


def create_blocks(summary: str, code: str, lang: str) -> List[Dict]:
    """
    Create Notion blocks for content injection

    Args:
        summary: Markdown formatted summary text
        code: Code snippet
        lang: Programming language for syntax highlighting

    Returns:
        List of Notion block objects
    """
    blocks = []

    # Add divider
    blocks.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })

    # Add heading
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "📋 技术详情"}
            }]
        }
    })

    # Parse summary and add as paragraphs and bullet points
    for line in summary.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line.startswith('###'):
            # Heading 3
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line.replace('###', '').strip()}
                    }]
                }
            })
        elif line.startswith('- '):
            # Bullet point
            content = line[2:].strip()
            # Parse bold markdown
            rich_text = []
            parts = content.split('**')
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    if part:
                        rich_text.append({
                            "type": "text",
                            "text": {"content": part}
                        })
                else:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": part},
                        "annotations": {"bold": True}
                    })

            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": rich_text if rich_text else [{
                        "type": "text",
                        "text": {"content": content}
                    }]
                }
            })
        else:
            # Regular paragraph
            if '**' in line:
                # Parse bold markdown in paragraph
                rich_text = []
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        if part:
                            rich_text.append({
                                "type": "text",
                                "text": {"content": part}
                            })
                    else:
                        rich_text.append({
                            "type": "text",
                            "text": {"content": part},
                            "annotations": {"bold": True}
                        })

                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text
                    }
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": line}
                        }]
                    }
                })

    # Add code block heading
    blocks.append({
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "💻 核心代码"}
            }]
        }
    })

    # Add code block
    blocks.append({
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{
                "type": "text",
                "text": {"content": code}
            }],
            "language": lang
        }
    })

    return blocks


def append_blocks_to_page(page_id: str, blocks: List[Dict]) -> bool:
    """
    Append blocks to a Notion page

    Args:
        page_id: The ID of the page to update
        blocks: List of block objects to append

    Returns:
        True if successful, False otherwise
    """
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    payload = {"children": blocks}

    try:
        response = requests.patch(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error appending blocks: {e}")
        try:
            error_data = e.response.json()
            print(f"   Error Details: {error_data.get('message', 'Unknown error')}")
        except:
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error appending blocks: {e}")
        return False


def inject_content(task_id: str, content: Dict) -> bool:
    """
    Inject content into a historical task page

    Args:
        task_id: Task identifier (e.g., "#001")
        content: Content dictionary with summary, code, and lang

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"🔍 Processing {task_id}...")

    # Search for page
    page_id, title = search_page_by_title(task_id)

    if not page_id:
        print(f"⚠️  Page not found for {task_id}")
        return False

    print(f"✅ Found: {title}")
    print(f"📄 Page ID: {page_id}")

    # Create blocks
    blocks = create_blocks(
        content["summary"],
        content["code"],
        content["lang"]
    )

    print(f"📦 Created {len(blocks)} content blocks")

    # Append blocks to page
    success = append_blocks_to_page(page_id, blocks)

    if success:
        print(f"✅ Content injected successfully!")
        page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
        print(f"🔗 View: {page_url}")
    else:
        print(f"❌ Failed to inject content")

    return success


def main():
    """Main execution function"""
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║       MT5-CRS History Content Injection Tool                              ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()

    # Validate environment
    if not TOKEN or not DB_ID:
        print("❌ Error: NOTION_TOKEN or NOTION_DB_ID not set")
        print("   Please check your .env file")
        sys.exit(1)

    print(f"📊 Tasks to process: {len(HISTORY_CONTENT)}")
    print()

    # Process each task
    success_count = 0
    failed_tasks = []

    for task_id in sorted(HISTORY_CONTENT.keys()):
        content = HISTORY_CONTENT[task_id]

        if inject_content(task_id, content):
            success_count += 1
        else:
            failed_tasks.append(task_id)

    # Summary
    print(f"\n{'='*70}")
    print("📊 Injection Summary")
    print(f"{'='*70}")
    print(f"✅ Successful: {success_count}/{len(HISTORY_CONTENT)}")

    if failed_tasks:
        print(f"❌ Failed: {', '.join(failed_tasks)}")

    print()

    if success_count == len(HISTORY_CONTENT):
        print("🎉 All tasks updated successfully!")
        print("🔗 Check your Notion database to view the enriched content")
        sys.exit(0)
    else:
        print(f"⚠️  {len(failed_tasks)} tasks failed. Please review and retry.")
        sys.exit(1)


if __name__ == "__main__":
    main()

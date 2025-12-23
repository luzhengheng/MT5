#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus Wiki 自动初始化脚本
=================================
功能: 检测并创建标准的 DevOps Cockpit Wiki 页面结构
标准: MT5-CRS Nexus 知识库 (简体中文 Schema)

Author: Claude Sonnet 4.5 (MT5-CRS Team)
Date: 2025-12-23
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
load_dotenv(PROJECT_ROOT / ".env")

# Notion API 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_WIKI_DB_ID = os.getenv("NOTION_WIKI_DB_ID")  # Wiki/知识库数据库 ID

# Notion API 常量
NOTION_API_VERSION = "2022-06-28"
NOTION_API_BASE = "https://api.notion.com/v1"

# 标准 Wiki 页面结构 (DevOps Cockpit)
WIKI_PAGES = [
    {
        "icon": "🏠",
        "title": "驾驶舱",
        "title_en": "Dashboard",
        "content": (
            "此处用于放置 'MT5-CRS Issues' 的看板视图。\n\n"
            "> 💡 **提示**: 请在 Notion 中输入 `/linked view` 并选择工单数据库。\n\n"
            "---\n\n"
            "### 快速链接\n"
            "- [系统架构](#系统架构)\n"
            "- [开发协议](#开发协议)\n"
            "- [应急手册](#应急手册)\n"
        ),
    },
    {
        "icon": "🏗️",
        "title": "系统架构",
        "title_en": "Architecture",
        "content": (
            "### 核心技术栈\n\n"
            "- **语言**: Python 3.9+ (Asyncio)\n"
            "- **网关**: MT5 Terminal (Windows Server)\n"
            "- **通信**: ZeroMQ (IPC) + REST API\n"
            "- **穿透**: Cloudflare Tunnel (HTTPS)\n"
            "- **监控**: Prometheus + Grafana\n\n"
            "---\n\n"
            "### 系统拓扑\n\n"
            "```\n"
            "┌─────────────────┐      Cloudflare Tunnel       ┌─────────────────┐\n"
            "│  交易算法服务器   │ ◄────────────────────────► │  Windows 网关    │\n"
            "│  (CentOS 7.9)   │         HTTPS/gRPC         │  (MT5 Terminal)  │\n"
            "└─────────────────┘                             └─────────────────┘\n"
            "       │                                                │\n"
            "       │ ZMQ/REST                                       │ MetaTrader5 API\n"
            "       │                                                │\n"
            "       ▼                                                ▼\n"
            "┌─────────────────┐                             ┌─────────────────┐\n"
            "│  特征工程管线    │                             │  Broker 服务器   │\n"
            "│  (Dask/Numba)   │                             │  (实盘/模拟盘)   │\n"
            "└─────────────────┘                             └─────────────────┘\n"
            "```\n\n"
            "---\n\n"
            "### 核心模块\n\n"
            "1. **MT5 Bridge** (`src/mt5_bridge/`)\n"
            "   - 跨网络 MT5 通信桥接\n"
            "   - 支持账户信息、历史数据、订单执行\n\n"
            "2. **特征工程** (`src/feature_engineering/`)\n"
            "   - 75+ 维特征计算 (基础 + 高级)\n"
            "   - 分数差分、三重障碍标签法\n\n"
            "3. **监督学习** (`src/models/`)\n"
            "   - LightGBM + 贝叶斯优化\n"
            "   - 时间序列交叉验证\n\n"
            "4. **回测系统** (`src/strategy/`, `src/reporting/`)\n"
            "   - Kelly 准则资金管理\n"
            "   - PSR 统计检验、Tearsheet 报告\n"
        ),
    },
    {
        "icon": "📜",
        "title": "开发协议",
        "title_en": "Protocols",
        "content": (
            "### Git 提交规范 (Conventional Commits)\n\n"
            "```\n"
            "<type>(<scope>): <subject>\n\n"
            "<body>\n\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
            "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>\n"
            "```\n\n"
            "**Type 类型**:\n"
            "- `feat`: 新功能 (Feature)\n"
            "- `fix`: 修补 Bug\n"
            "- `docs`: 文档变动\n"
            "- `infra`: 基础设施 (Docker/CI/监控)\n"
            "- `refactor`: 重构 (不改变外部行为)\n"
            "- `test`: 测试相关\n"
            "- `chore`: 构建/工具链变动\n\n"
            "---\n\n"
            "### 工单优先级标准\n\n"
            "| 级别 | 标签 | 响应时间 | 示例 |\n"
            "|-----|------|---------|------|\n"
            "| P0 | 🔴 致命 | 立即 | 生产环境崩溃、资金安全问题 |\n"
            "| P1 | 🟠 紧急 | 24h | 关键功能失效、数据丢失风险 |\n"
            "| P2 | 🟡 重要 | 7天 | 性能优化、用户体验改进 |\n"
            "| P3 | 🟢 常规 | 30天 | 文档完善、技术债务 |\n\n"
            "---\n\n"
            "### AI 协同工作流\n\n"
            "1. **Claude Sonnet 4.5** (主力开发)\n"
            "   - 快速代码实现、系统架构设计\n"
            "   - 实时测试验证、文档撰写\n\n"
            "2. **Gemini Pro** (外部协同)\n"
            "   - 代码深度审查、架构优化建议\n"
            "   - 战略规划、最新知识补充\n\n"
            "3. **协同流程**:\n"
            "   - Claude 完成功能开发 → 提交到 Git\n"
            "   - 运行 `python export_context_for_ai.py` 生成上下文包\n"
            "   - 用户提交给 Gemini Pro 审查\n"
            "   - Gemini 生成审查报告 (Markdown)\n"
            "   - Claude 应用修复建议 → 新一轮迭代\n"
        ),
    },
    {
        "icon": "🚑",
        "title": "应急手册",
        "title_en": "Runbooks",
        "content": (
            "### 紧急命令速查\n\n"
            "#### 1. 服务重启\n\n"
            "```bash\n"
            "# 重启 MT5 Bridge 服务\n"
            "systemctl restart mt5-bridge\n\n"
            "# 查看服务状态\n"
            "systemctl status mt5-bridge\n\n"
            "# 重启 Cloudflare Tunnel\n"
            "systemctl restart cloudflared\n"
            "```\n\n"
            "---\n\n"
            "#### 2. 日志排查\n\n"
            "```bash\n"
            "# 实时查看日志\n"
            "tail -f /var/log/mt5-bridge.log\n\n"
            "# 查看最近 100 条错误\n"
            "grep ERROR /var/log/mt5-bridge.log | tail -100\n\n"
            "# 查看今天的日志\n"
            "journalctl -u mt5-bridge --since today\n"
            "```\n\n"
            "---\n\n"
            "#### 3. 网络诊断\n\n"
            "```bash\n"
            "# 测试 Windows 网关连通性\n"
            "bash /opt/mt5-crs/scripts/verify_network.sh\n\n"
            "# 查看 Cloudflare Tunnel 状态\n"
            "cloudflared tunnel info mt5-tunnel\n\n"
            "# 测试 ZMQ 端口\n"
            "nc -zv localhost 5555\n"
            "```\n\n"
            "---\n\n"
            "#### 4. 数据库备份\n\n"
            "```bash\n"
            "# 备份 Parquet 数据文件\n"
            "tar -czf /backup/mt5_data_$(date +%Y%m%d).tar.gz /opt/mt5-crs/data/\n\n"
            "# 查看备份大小\n"
            "du -sh /backup/\n"
            "```\n\n"
            "---\n\n"
            "#### 5. 应急止损\n\n"
            "```python\n"
            "# 快速平仓所有持仓 (谨慎使用!)\n"
            "import MetaTrader5 as mt5\n\n"
            "mt5.initialize()\n"
            "positions = mt5.positions_get()\n"
            "for pos in positions:\n"
            "    mt5.Close(pos.ticket)\n"
            "mt5.shutdown()\n"
            "```\n\n"
            "---\n\n"
            "### 常见故障处理\n\n"
            "| 故障现象 | 可能原因 | 解决方案 |\n"
            "|---------|---------|----------|\n"
            "| 连接超时 | Cloudflare Tunnel 断开 | `systemctl restart cloudflared` |\n"
            "| 数据延迟 | MT5 未登录 | 检查 Windows 网关 MT5 登录状态 |\n"
            "| 订单失败 | 账户余额不足/市场休市 | 检查账户状态、交易时间 |\n"
            "| 特征计算失败 | 数据缺失/格式错误 | 运行 `python src/monitoring/dq_score.py` 检查数据质量 |\n\n"
            "---\n\n"
            "### 紧急联系方式\n\n"
            "- **系统架构问题**: Claude Sonnet 4.5 (AI Architect)\n"
            "- **策略优化建议**: Gemini Pro (AI Strategy Advisor)\n"
            "- **Broker 技术支持**: [根据实际 Broker 填写]\n"
        ),
    },
]


class NotionNexusSeeder:
    """Notion Nexus Wiki 自动初始化器"""

    def __init__(self, token: str, wiki_db_id: str):
        """
        Args:
            token: Notion Integration Token
            wiki_db_id: Wiki/知识库数据库 ID
        """
        if not token or not wiki_db_id:
            raise ValueError("缺少必要的环境变量: NOTION_TOKEN 或 NOTION_WIKI_DB_ID")

        self.token = token
        self.wiki_db_id = wiki_db_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_API_VERSION,
        }

    def query_existing_pages(self) -> Dict[str, str]:
        """
        查询已存在的 Wiki 页面

        Returns:
            dict: {页面标题: 页面ID}
        """
        url = f"{NOTION_API_BASE}/databases/{self.wiki_db_id}/query"

        try:
            response = requests.post(url, headers=self.headers, json={})
            response.raise_for_status()
            data = response.json()

            existing = {}
            for page in data.get("results", []):
                # 获取标题 (支持中英文标题属性名)
                title_prop = page["properties"].get("名称") or page["properties"].get("Name")
                if title_prop and title_prop.get("title"):
                    title_text = title_prop["title"][0]["plain_text"]
                    existing[title_text] = page["id"]

            return existing

        except requests.exceptions.RequestException as e:
            print(f"❌ 查询现有页面失败: {e}")
            return {}

    def create_page(self, page_data: Dict) -> Optional[str]:
        """
        创建 Wiki 页面

        Args:
            page_data: 页面数据 (包含 icon, title, content)

        Returns:
            str: 创建的页面 ID (如果成功)
        """
        url = f"{NOTION_API_BASE}/pages"

        # 构建请求体
        payload = {
            "parent": {"database_id": self.wiki_db_id},
            "icon": {"type": "emoji", "emoji": page_data["icon"]},
            "properties": {
                "名称": {  # 使用中文属性名
                    "title": [{"text": {"content": page_data["title"]}}]
                }
            },
            "children": self._build_content_blocks(page_data["content"])
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            page = response.json()

            print(f"✅ 创建页面: {page_data['icon']} {page_data['title']}")
            return page["id"]

        except requests.exceptions.RequestException as e:
            print(f"❌ 创建页面失败 [{page_data['title']}]: {e}")
            if hasattr(e.response, 'text'):
                print(f"   错误详情: {e.response.text}")
            return None

    def _build_content_blocks(self, content: str) -> List[Dict]:
        """
        将 Markdown 文本转换为 Notion blocks

        Args:
            content: Markdown 文本

        Returns:
            list: Notion block objects
        """
        blocks = []

        # 简单处理: 按段落分割
        for paragraph in content.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检测代码块
            if paragraph.startswith("```"):
                code_lines = paragraph.split("\n")
                language = code_lines[0].replace("```", "").strip() or "plain text"
                code_content = "\n".join(code_lines[1:-1])

                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_content}}],
                        "language": language
                    }
                })

            # 检测标题
            elif paragraph.startswith("###"):
                heading_text = paragraph.replace("###", "").strip()
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": heading_text}}]
                    }
                })

            elif paragraph.startswith("##"):
                heading_text = paragraph.replace("##", "").strip()
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": heading_text}}]
                    }
                })

            # 检测引用块
            elif paragraph.startswith(">"):
                quote_text = paragraph.replace(">", "").strip()
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"type": "text", "text": {"content": quote_text}}]
                    }
                })

            # 检测分割线
            elif paragraph == "---":
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })

            # 普通段落
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": paragraph}}]
                    }
                })

        return blocks

    def seed(self) -> Dict[str, int]:
        """
        执行初始化: 创建缺失的 Wiki 页面

        Returns:
            dict: {"created": 创建数量, "skipped": 跳过数量}
        """
        print("=" * 80)
        print("🌱 Notion Nexus Wiki 自动初始化")
        print("=" * 80)
        print()

        # 1. 查询现有页面
        print("📊 正在查询现有页面...")
        existing_pages = self.query_existing_pages()
        print(f"   已存在 {len(existing_pages)} 个页面")
        print()

        # 2. 创建缺失的页面
        created = 0
        skipped = 0

        for page_data in WIKI_PAGES:
            if page_data["title"] in existing_pages:
                print(f"⏭️  跳过 (已存在): {page_data['icon']} {page_data['title']}")
                skipped += 1
            else:
                page_id = self.create_page(page_data)
                if page_id:
                    created += 1

        # 3. 输出总结
        print()
        print("=" * 80)
        print("📊 初始化完成")
        print("=" * 80)
        print(f"✅ 创建: {created} 个页面")
        print(f"⏭️  跳过: {skipped} 个页面")
        print()

        return {"created": created, "skipped": skipped}


def main():
    """主函数"""
    try:
        seeder = NotionNexusSeeder(
            token=NOTION_TOKEN,
            wiki_db_id=NOTION_WIKI_DB_ID
        )

        result = seeder.seed()

        # 成功退出
        sys.exit(0)

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print()
        print("💡 请检查 .env 文件是否包含以下变量:")
        print("   - NOTION_TOKEN")
        print("   - NOTION_WIKI_DB_ID")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

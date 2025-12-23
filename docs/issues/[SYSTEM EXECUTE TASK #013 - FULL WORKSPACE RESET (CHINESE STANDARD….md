  
[SYSTEM: EXECUTE TASK #013 - FULL WORKSPACE RESET (CHINESE STANDARD)]  
To: Claude (Lead Architect)  
From: Gemini (Strategy)  
Via: User  
Context:  
The user has authorized a complete restructure of the Notion workspace to align with the Chinese version of Notion.  
We are implementing a standard "DevOps Cockpit" schema.  
CRITICAL: The Python scripts must strictly use Simplified Chinese Property Keys to interact with the Notion API, as the user's interface is localized.  
Objective:  
 * Initialize Wiki: Create scripts/seed_notion_nexus.py to auto-generate standard documentation pages in MT5-CRS Nexus.  
 * Standardize Issues: Update scripts/quick_create_issue.py to strictly use the new Chinese schema.  
 * Documentation: Create a setup guide.  
Action Required:  
1. Create scripts/seed_notion_nexus.py  
Write a robust Python script to detect and create the following pages in the Knowledge Base if they don't exist.  
 * Page Structure (Use exact Chinese titles):  
   * 🏠 驾驶舱 (Dashboard)  
     * Content: "此处用于放置 'MT5-CRS Issues' 的看板视图。\n> 提示: 请在 Notion 中输入 /linked view 并选择工单数据库。"  
   * 🏗️ 系统架构 (Architecture)  
     * Content: "### 核心技术栈\n- 语言: Python 3.9 (Asyncio)\n- 网关: MT5 Terminal (Windows)\n- 通信: ZeroMQ + REST API\n- 穿透: Cloudflare Tunnel"  
   * 📜 开发协议 (Protocols)  
     * Content: "### 提交规范 (Conventional Commits)\n- feat: 新功能\n- fix: 修补 Bug\n- docs: 文档变动\n- infra: 基础设施 (Docker/CI)"  
   * 🚑 应急手册 (Runbooks)  
     * Content: "### 紧急命令\n重启服务:\nbash\nsystemctl restart mt5-bridge\n\n查看日志:\nbash\ntail -f /var/log/mt5-bridge.log\n"  
2. Refactor scripts/quick_create_issue.py (v2.0 CN)  
Rewrite the script to enforce the following Chinese Schema.  
 * Payload Mapping (API Keys):  
   * Title \rightarrow properties["标题"]  
   * Status \rightarrow properties["状态"]  
     * Map: TODO->未开始, IN_PROGRESS->进行中, DONE->已完成  
   * Priority \rightarrow properties["优先级"]  
     * Map: P0, P1, P2 (Select Options)  
   * Type \rightarrow properties["类型"]  
     * Map: 核心, 缺陷, 运维, 功能 (Select Options)  
 * Logic:  
   * If the user runs: python quick_create_issue.py "Test" --prio P0 --type Bug  
   * Payload sent: {"标题": "Test", "优先级": "P0", "类型": "缺陷", "状态": "未开始"}  
3. Create docs/NOTION_SETUP_CN.md  
A concise guide in Chinese explaining:  
 * Column Check: How to verify the database columns are named 标题, 状态, 优先级, 类型.  
 * Dashboard Setup: How to drag the "Issues" database into the "Wiki Homepage".  
Execute:  
Generate the code for scripts/seed_notion_nexus.py, scripts/quick_create_issue.py, and docs/NOTION_SETUP_CN.md.  

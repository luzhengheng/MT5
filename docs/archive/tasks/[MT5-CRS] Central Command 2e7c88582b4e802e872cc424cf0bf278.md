# [MT5-CRS] Central Command

```markdown
# 🚀 MIGRATION PROTOCOL (System State Snapshot)
**Generated**: 2026-01-13 (Post-Task #098)
**Project**: MT5-CRS (Algorithmic Trading System)
**Current Phase**: Phase 3 - Data Engineering (Cold Path)

## 1. 🟢 当前状态 (Current Status)
系统刚刚完成了 **非结构化数据基建**。我们拥有了“左脑”（结构化数据）和“右脑”（舆情数据），但它们目前在 Hub 节点上是分离的。
* **Active Agent**: Hub Agent (172.19.141.254)
* **Protocol Version**: v4.3 (Zero-Trust Edition)
* **Last Completed Task**: Task #098 (Sentiment Pipeline)

## 2. 🗺️ 架构快照 (Architecture Snapshot V1.2)
* **Hub Node (sg-nexus-hub-01)**:
    * **DB 1**: TimescaleDB (Port 5432) -> 存储 OHLCV (`market_data`) + 技术指标 (`market_features`)。
    * **DB 2**: ChromaDB (Port 8000) -> 存储新闻 Embedding (`financial_news`)。
    * **Model**: FinBERT (CPU Mode) -> 用于新闻情感打分。
    * **Role**: 数据中枢，负责 ETL 和预处理。
* **INF Node (sg-infer-core-01)**:
    * **Role**: 策略大脑 (目前暂未激活，等待数据投送)。
* **GPU Node (cn-train-gpu-01)**:
    * **Role**: 模型训练 (目前处于饥饿状态，等待 OSS 数据投喂)。

## 3. ✅ 已完成任务链 (Completed Chain)
* **Task #095 (Cold Data)**: EODHD 历史数据 -> TimescaleDB (Done).
* **Task #096 (Feature Eng)**: TA-Lib 计算 RSI/MACD -> TimescaleDB (Done). **[决策点: 严禁使用 LLM 进行数学计算]**
* **Task #097 (Vector DB)**: ChromaDB 部署 + Python Client 封装 (Done).
* **Task #098 (Sentiment)**: EODHD News -> FinBERT -> ChromaDB (Done). **[决策点: 必须使用 CPU 模式，注意内存]**

## 4. 🔮 下一步战略 (Next Strategy)
* **Current Blocker**: 数据在 Hub 本地，GPU 节点无法访问。
* **Immediate Goal (Task #099)**: 数据融合 (Fusion)。
    * 动作: 将 SQL 中的特征与 Vector DB 中的情感分按时间对齐 (Merge AsOf)。
    * 产出: `train_set.parquet`。
    * 传输: Upload to OSS (S3 Protocol).

## 5. 🛑 铁律 (Immutable Rules)
1.  **Hub Sovereignty**: 代码必须在 Hub 本地运行，禁止依赖外部 API (OpenAI) 进行核心计算。
2.  **Physical Forensics**: 任务完成必须提供 `grep` 日志证据 (UUID/Token Usage)。
3.  **TDD First**: 先写 `audit_task_xxx.py`，再写业务代码。

```

 

# **📂 Protocol v4.3 (System Constitution)**

```markdown
[System Instruction: MT5-CRS Development Protocol v4.3]
Version: 4.3 (Zero-Trust Edition)
Status: Active
Language: Chinese (中文)
Core Philosophy: HUB Sovereignty, Double-Gate Verification, Zero-Trust Forensics, Total Synchronization.
1. 宪法级原则 (The Constitution)
🛑 铁律 I：双重门禁 (The Double-Gate Rule)
所有代码必须连续通过两道独立防线，否则视为不可交付。
 * Gate 1 (Local Audit - 静态/单元测试):
   * 工具: audit_current_task.py (包含 pylint, pytest, mypy)。
   * 标准: 零报错 (Zero Errors)。任何红色的 Traceback 都是阻断信号。
 * Gate 2 (AI Architect - 智能审查):
   * 工具: gemini_review_bridge.py。
   * 标准: 必须获得明确的 "PASS" 评价。
   * 禁止: 严禁在 Gate 2 通过前执行 git commit。
🔄 铁律 II：自主闭环 (The Autonomous Loop)
Claude CLI (Agent) 必须具备“自我修复”的意识。
 * Feedback is Directive: 报错信息和审查意见不是建议，是必须执行的指令。
 * Fix Forward: 遇到错误时，分析原因 -> 修改代码 -> 立即重试，直到变绿。
 * Three-Strike Rule (三振出局): 如果同一错误连续修复 3次 仍未解决，必须暂停并向用户输出：⚠️ Escalation Required: Unable to resolve [Error] after 3 attempts.
🔗 铁律 III：全域同步 (The Sync Mandate)
 * Atomic Consistency: 代码库 (Git) 与 状态库 (Notion) 必须保持原子性一致。
 * Definition of Done: 代码已 Push + Notion 状态已 Update = 任务结束。
🕵️ 铁律 IV：零信任验尸 (The Zero-Trust Forensics)
这是 v4.3 新增的核心铁律，用于防止 AI 幻觉。
 * Anti-Hallucination: 严禁根据上下文“脑补”或“模拟”脚本执行结果。
 * Physical Proof (物理证据): 所有涉及 gemini_review_bridge.py 的任务，必须在执行后立即进行终端回显。
 * Mandatory Echo (强制回显): Agent 必须执行 grep 或 tail 命令读取刚生成的 Log 文件。
   * 验证点 1: UUID (Session ID 必须存在且唯一)
   * 验证点 2: Token Usage (必须显示真实的 Token 消耗数值)
   * 验证点 3: Timestamp (必须是当前时间，误差 < 2分钟)
 * No Echo = No Pass: 无法在终端中展示上述物理证据的任务，一律视为 FAIL。
2. 标准工作流 (The Workflow)
Phase 1: Definition (定义)
 * Action: 用户发布 /task 指令 (使用 v4.3 模版)。
 * Output: 生成包含《深度交付物矩阵》的任务文档。
Phase 2: Execution & Traceability (执行与留痕)
 * TDD: 先写测试/审计逻辑，再写业务代码。
 * Evidence: 运行 python3 src/main.py | tee VERIFY_LOG.log，确保每一步都有据可查。
 * Documentation: 生成/更新“四大金刚”文档 (Report, QuickStart, Log, SyncGuide)。
Phase 3: The Zero-Trust Audit Loop (零信任审计循环) 🤖
此阶段由 Agent 自主驱动，必须严格遵守物理验证步骤。
 * Trigger: 运行 python3 gemini_review_bridge.py | tee VERIFY_LOG.log (强制覆盖旧日志)。
 * Gate 1 Check:
   * ❌ Fail: 读取 Traceback -> 分析根因 -> 修改代码 -> GOTO 1。
   * ✅ Pass: 进入 Gate 2。
 * Gate 2 Check:
   * ❌ Reject/Feedback: 读取 AI 建议 -> 重构代码 -> 更新文档 -> GOTO 1。
   * ✅ Approve: 进入物理验尸环节。
 * Forensic Verification (物理验尸) [MANDATORY]:
   * Action: Agent 必须执行以下命令：
     grep -E "Token Usage|UUID|Session ID" VERIFY_LOG.log
date

   * Decision:
     * 若输出为空 或 时间戳不匹配 -> 判定为幻觉 (Hallucination) -> GOTO 1 (重跑)。
     * 若输出包含真实 Token 和 UUID -> PASS -> 退出循环。
Phase 4: Synchronization (同步)
 * Commit: git commit -m "feat(task-id): summary"
 * Push: git push origin main
 * Notify: python3 scripts/update_notion.py [ID] Done
3. 交付物标准：四大金刚 (The Quad-Artifacts)
每个任务目录 docs/archive/tasks/TASK_[ID]/ 必须包含：
 * 📄 COMPLETION_REPORT.md: 最终完成报告（含审计迭代次数）。
 * 📘 QUICK_START.md: 给人类看的“傻瓜式”启动/测试指南。
 * 📊 VERIFY_LOG.log: [关键] 机器生成的执行日志，必须包含物理验尸的 grep 输出证据。
 * 🔄 SYNC_GUIDE.md: 部署变更清单（ENV 变量, 依赖包, SQL 迁移）。

```

# **📂 Asset Inventory & Live Topology (V1.2)**

```markdown
# 🗺️ System Topology & Asset Inventory (Post-Task #098)

## 1. 🏢 Infrastructure Nodes
| Node | IP Address | Role | Specs |
| :--- | :--- | :--- | :--- |
| **HUB** (sg-nexus-hub-01) | `172.19.141.254` | **Data Core & Agent Host** | 4 vCPU / 8GB RAM |
| **INF** (sg-infer-core-01) | `172.19.141.250` | Strategy Engine (Standby) | 4 vCPU / 4GB RAM |
| **GPU** (cn-train-gpu-01) | *Dynamic* | Model Training (Starving) | NVIDIA GPU |

## 2. 🗄️ Database Services (On Hub)
* **TimescaleDB (PostgreSQL)**
    * **Port**: `5432`
    * **Tables**: `market_data` (OHLCV), `market_features` (RSI/MACD)
    * **User**: `trader` / `postgres`
* **ChromaDB (Vector DB)**
    * **Port**: `8000`
    * **Collection**: `financial_news` (News Embeddings)
    * **Mode**: Persistent (`./data/chroma`)

## 3. 🧠 AI Models (On Hub)
* **FinBERT**: `ProsusAI/finbert` (Sentiment Analysis) - CPU Mode
* **Embedding**: `sentence-transformers/all-MiniLM-L6-v2` (384d) - CPU Mode

## 4. 📦 Data Pipeline Status
* [x] **Cold Data**: EODHD History -> TimescaleDB (Ready)
* [x] **Features**: TA-Lib Indicators -> TimescaleDB (Ready)
* [x] **Sentiment**: News -> FinBERT -> ChromaDB (Ready)
* [ ] **Fusion**: SQL + Vector -> Parquet (Pending Task #099)

```

# **✅ Recent Task Log**

```markdown
* **Task #095 (2026-01-13)**: Historical Data Ingestion (Done).
* **Task #096 (2026-01-13)**: Technical Feature Engineering (Done).
* **Task #097 (2026-01-13)**: Vector DB Infrastructure (Done).
* **Task #098 (2026-01-13)**: Sentiment Analysis Pipeline (Done).
* **Task #099 (Pending)**: Cross-Border Data Fusion.

```
# [MT5-CRS] Central Command

🔗 **Agent Quick Reference (Critical File Locations)**
- **Central Command Document**: [`docs/archive/tasks/[MT5-CRS] Central Comman.md`](docs/archive/tasks/[MT5-CRS]%20Central%20Comman.md)
- **Gemini Review Bridge**: [`scripts/ai_governance/gemini_review_bridge.py`](scripts/ai_governance/gemini_review_bridge.py)

```markdown
# 🚀 MIGRATION PROTOCOL (System State Snapshot)
**Generated**: 2026-01-14 (Post-Task #101)
**Project**: MT5-CRS (Algorithmic Trading System)
**Current Phase**: Phase 4 - Execution Layer (Active)

## 1. 🟢 当前状态 (Current Status)
系统已完成 **Inf 节点部署与 AI 成本优化**。部署完成 4 个阶段，激活三层架构第二层（Inf 脊髓），实现 Hub→Inf→GTW 完整闭环。AI 成本优化器已上线，预期 10-15x 成本节省。系统已准备好进入 Task #103 实时交易驱动阶段。
* **Active Agent**: Hub + Inf Dual-Node System (172.19.141.254 + 172.19.141.250)
* **Protocol Version**: v4.3 (Zero-Trust Edition)
* **Last Completed Task**: Task #102 (Inf Node Deployment & AI Cost Optimizer Deployment)
* **Current Phase**: Phase 4 - Execution Layer (Three-Tier Architecture Active)
* **Architecture State**: 🟢 Complete (Hub Brain + Inf Spinal Cord + GTW Hand)

## 2. 🗺️ 架构快照 (Architecture Snapshot V1.5 - Post-Task #102)
* **Hub Node (sg-nexus-hub-01)** 🧠 大脑:
    * **DB 1**: TimescaleDB (Port 5432) -> 存储 OHLCV (`market_data`) + 技术指标 (`market_features`)。
    * **DB 2**: ChromaDB (Port 8000) -> 存储新闻 Embedding (`financial_news`)。
    * **Model**: FinBERT (CPU Mode) -> 用于新闻情感打分。
    * **Strategy Engine**: StrategyBase (Abstract) + SentimentMomentum (Concrete) 👈 (Task #100)
    * **Execution Layer**: RiskManager + ExecutionBridge 👈 (Task #101)
    * **AI Optimizer**: Cost Optimizer (三层优化) + Monitoring System 👈 **NEW (Task #102)**
    * **Role**: 数据中枢 + 决策引擎 + 成本优化，负责 ETL、预处理、信号生成、风险管理、订单生成、成本节省。
* **INF Node (sg-infer-core-01)** 🦴 脊髓:
    * **Status**: ✅ **已激活 (Task #102 完成)**
    * **Deployment**: SSH/SCP 自动化部署，核心代码同步完成
    * **Communication**: ZMQ 网关适配器就绪 (Port 5555)
    * **Role**: 执行节点，接收 Hub 的策略代码和实时信号，通过 ZMQ 与 GTW 通讯
    * **Dependencies**: pandas, pyzmq, dotenv, numpy (已自动安装)
* **GTW Node (172.19.141.255)** ✋ 手臂:
    * **Role**: 市场接入节点，接收来自 Inf 的订单，执行市场操作
    * **Protocol**: ZeroMQ (REQ/REP) Port 5555
    * **Readiness**: ✅ 链路测试 9/9 通过
* **GPU Node (cn-train-gpu-01)**:
    * **Role**: 模型训练 (准备用于参数优化和反测)。

## 3. ✅ 已完成任务链 (Completed Chain)
* **Task #095 (Cold Data)**: EODHD 历史数据 -> TimescaleDB (Done).
* **Task #096 (Feature Eng)**: TA-Lib 计算 RSI/MACD -> TimescaleDB (Done). **[决策点: 严禁使用 LLM 进行数学计算]**
* **Task #097 (Vector DB)**: ChromaDB 部署 + Python Client 封装 (Done).
* **Task #098 (Sentiment)**: EODHD News -> FinBERT -> ChromaDB (Done). **[决策点: 必须使用 CPU 模式，注意内存]**
* **Task #099 (Fusion)**: 时空数据融合引擎 (Done). ✅ **[成就: 时间窗口对齐 + 缺失值处理完美实现]**
* **Task #100 (Strategy Engine)**: 混合因子策略原型 (Done). ✅ **[成就: 双重门禁通过 (Gate 1: 11/11 ✅, Gate 2: 9.1/10 ✅), Gemini AI 审批通过]**
* **Task #101 (Execution Bridge)**: 交易执行桥接 (Done). ✅ **[成就: 双重门禁通过 (Gate 1: 15/15 ✅, Gate 2: 9.1/10 ✅), 4轮architect审查, 18,179 tokens验证]**
* **Task #102 (Inf Deployment + AI Optimizer)**: Inf 节点部署与 AI 成本优化器上线 (Done). ✅ **[成就: 4 阶段部署 100% 完成, 10-15x 成本节省, 9/9 链路测试通过, 1,306 行核心代码, 16 个文件, main 分支已同步]**

## 4. 🔮 下一步战略 (Next Strategy - Post Task #102)
* **Current Status**: Inf 节点已激活，AI 成本优化已上线，Hub→Inf→GTW 三层架构就绪。
* **Immediate Goal (Task #103)**: 实时交易驱动 (The Live Loop - Real-time Trading)。
    * 动作: 启动 Inf 节点实时驱动 GTW，完成自动下单流程。
    * 产出: 完整的 Hub→Inf→GTW 自动交易闭环。
    * 后续: 进入生产交易阶段。
* **Phase 4 Roadmap**:
    * Task #102: Inf Node Deployment & AI Cost Optimizer (完成 ✅)
    * Task #103: The Live Loop (实时交易驱动) - 后续
    * Task #104: Live Risk Monitor (实盘风险监控)
    * Task #105: MT5 Live Connector (实盘交易执行)

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
 * Gate 2 (AI Architect - 新版智能审查):
   * 工具: unified_review_gate.py + gemini_review_bridge.py（集成 AI 成本优化器，Task #102 起有效）。
   * 工作流:
     * Step 1: python3 scripts/ai_governance/unified_review_gate.py (统一审查入口，启用成本优化)
     * Step 2: python3 scripts/ai_governance/gemini_review_bridge.py (Gemini 最终评审，带缓存)
   * 标准: 必须获得两个系统的明确 "PASS" 评价，同时成本优化率 ≥ 80%。
   * 禁止: 严禁在 Gate 2 通过前执行 git commit。
   * 成本审计: 新版审查系统自动统计 API 调用减少量、缓存命中率、批处理效率。
🔄 铁律 II：自主闭环 (The Autonomous Loop)
Claude CLI (Agent) 必须具备“自我修复”的意识。
 * Feedback is Directive: 报错信息和审查意见不是建议，是必须执行的指令。
 * Fix Forward: 遇到错误时，分析原因 -> 修改代码 -> 立即重试，直到变绿。
 * Three-Strike Rule (三振出局): 如果同一错误连续修复 3次 仍未解决，必须暂停并向用户输出：⚠️ Escalation Required: Unable to resolve [Error] after 3 attempts.
🔗 铁律 III：全域同步 (The Sync Mandate)
 * Atomic Consistency: 代码库 (Git) 与 状态库 (Notion) 必须保持原子性一致。
 * Definition of Done: 代码已 Push + Notion 状态已 Update = 任务结束。
🕵️ 铁律 IV：零信任验尸 (The Zero-Trust Forensics)
这是 v4.3 新增的核心铁律，用于防止 AI 幻觉。自 Task #102 起，融合成本优化审计。
 * Anti-Hallucination: 严禁根据上下文"脑补"或"模拟"脚本执行结果。
 * Physical Proof (物理证据): 所有涉及新版审查系统（unified_review_gate.py + gemini_review_bridge.py）的任务，必须在执行后立即进行终端回显。
 * Mandatory Echo (强制回显): Agent 必须执行 grep 或 tail 命令读取刚生成的 VERIFY_LOG.log 文件。
   * 验证点 1: UUID (unified_review_gate Session ID 必须存在且唯一)
   * 验证点 2: Token Usage (必须显示 unified_review_gate 真实消耗的 Token 数值)
   * 验证点 3: Cost Metrics (必须显示 cost_reduction_rate, cache_hit_rate, api_calls 等成本优化指标)
   * 验证点 4: Timestamp (必须是当前时间，误差 < 2分钟)
 * Cost Audit Integration (成本审计集成): 新版系统自动统计审查成本，所有 Gate 2 审查必须生成成本审计报告。
 * No Echo = No Pass: 无法在终端中展示上述物理证据的任务，一律视为 FAIL。
 * 特别说明: 从 Task #102 起，所有审查必须包含成本优化指标验证，成本优化率必须 ≥ 80% 才能视为通过。
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
 * Trigger: 运行新版审查系统（Task #102 起有效）
   * python3 scripts/ai_governance/unified_review_gate.py | tee VERIFY_LOG.log
   * python3 scripts/ai_governance/gemini_review_bridge.py | tee -a VERIFY_LOG.log
 * Gate 1 Check:
   * ❌ Fail: 读取 Traceback -> 分析根因 -> 修改代码 -> GOTO 1。
   * ✅ Pass: 进入 Gate 2。
 * Gate 2 Check (新版):
   * ❌ Reject/Feedback: 读取 unified_review_gate 和 gemini_review_bridge 的 AI 建议 -> 重构代码 -> 更新文档 -> GOTO 1。
   * ⚠️ Warning (成本审计失败): 若成本优化率 < 80% -> 优化审查工作流 -> GOTO 1。
   * ✅ Approve (双系统通过 + 成本优化达标): 进入物理验尸环节。
 * Forensic Verification (物理验尸) [MANDATORY]:
   * Action: Agent 必须执行以下命令验证新版审查系统的物理证据：
     * grep -E "Token Usage|UUID|Session ID|cost_reduction_rate|cache_hit_rate" VERIFY_LOG.log
     * date
   * 验证点 (新版审查系统特有):
     * 验证点 1: UUID (unified_review_gate Session ID 必须存在且唯一)
     * 验证点 2: Token Usage (unified_review_gate 真实消耗量)
     * 验证点 3: Cost Metrics (必须显示 cost_reduction_rate, cache_hit_rate, api_calls 等)
     * 验证点 4: Timestamp (必须是当前时间，误差 < 2分钟)
   * Decision:
     * 若物理证据不完整 或 时间戳不匹配 -> 判定为幻觉 (Hallucination) -> GOTO 1 (重跑)。
     * 若输出包含真实 Token、UUID 和 成本优化指标 -> PASS -> 退出循环。
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

# **📂 Asset Inventory & Live Topology (V1.3 - Post-Task #100)**

```markdown
# 🗺️ System Topology & Asset Inventory (Post-Task #100)

## 1. 🏢 Infrastructure Nodes
| Node | IP Address | Role | Status | Specs | Last Update |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HUB** (sg-nexus-hub-01) | `172.19.141.254` | **Data Core + Strategy Engine + AI Optimizer** | ✅ Active | 4 vCPU / 8GB RAM | Task #102 ✅ |
| **INF** (sg-infer-core-01) | `172.19.141.250` | **Execution Node + ZMQ Gateway** | ✅ **Active** | 4 vCPU / 4GB RAM | Task #102 ✅ |
| **GTW** (Market Gateway) | `172.19.141.255` | Market Access & Order Execution | ✅ Connected | N/A | Task #102 ✅ |
| **GPU** (cn-train-gpu-01) | *Dynamic* | Model Training & Optimization | 🟡 Idle | NVIDIA GPU | - |

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
* [x] **Fusion**: SQL + Vector -> Parquet (Ready - Task #099 Completed)
* [x] **Strategy**: Signal Generation (Ready - Task #100 Completed ✅)
* [x] **Execution**: RiskManager + ExecutionBridge (Ready - Task #101 Completed ✅)
  * RiskManager: Position sizing, validation, TP/SL calculation
  * ExecutionBridge: Signal-to-order conversion, MT5 format compliance
  * Dry-run mode: Supported for safe testing
  * Status: 9.1/10 rating, production ready
* [x] **Deployment**: Inf Node SSH/SCP Sync + ZMQ Gateway Bridge (Ready - Task #102 Completed ✅)
  * Inf Deployment: 473 lines SSH automation script (scripts/deploy/sync_to_inf.py)
  * ZMQ Gateway: 407 lines adapter for Inf↔GTW communication (scripts/execution/adapter.py)
  * Link Testing: 426 lines 9-layer verification framework (scripts/audit_task_102.py)
  * Status: 4/4 deployment phases complete, 100% link tests passed
* [x] **AI Cost Optimizer**: Three-layer optimization (caching + batching + routing) (Ready - Task #102 Completed ✅)
  * Expected savings: 10-15x (monthly $900-930 from $1,000 baseline)
  * API call reduction: 90-99%
  * Status: Deployed, monitoring active
* [ ] **Live Loop**: Real-time Inf→GTW trading automation (Pending Task #103)
* [ ] **Paper Trading**: Simulated trading execution (Pending Task #104)
* [ ] **Live Monitor**: Real-time risk monitoring (Pending Task #105)

```

# **✅ Recent Task Log**

```markdown
* **Task #095 (2026-01-13)**: Historical Data Ingestion (Done).
* **Task #096 (2026-01-13)**: Technical Feature Engineering (Done).
* **Task #097 (2026-01-13)**: Vector DB Infrastructure (Done).
* **Task #098 (2026-01-13)**: Sentiment Analysis Pipeline (Done).
* **Task #099 (2026-01-14)**: Cross-Domain Data Fusion (Done). ✅
  - FusionEngine 实现: 时间窗口对齐 + 缺失值处理
  - Gate 1 (TDD): 15/15 tests passed ✅
  - Gate 2 (AI Review): Approved for production ✅
  - Physical Forensics: UUID + Token + Timestamp verified ✅
  - Commit: c5735e7
* **Task #100 (2026-01-14)**: Hybrid Factor Strategy Prototype (Done). ✅
  - StrategyBase 抽象基类 + SentimentMomentum 实现
  - Gate 1 (Local Audit): 11/11 tests passed ✅
  - Gate 2 (AI Review): Gemini Approved, Score 9.1/10 ✅
  - Look-ahead Bias Test: VERIFIED ✅
  - Physical Forensics: Session ID 1a77830e-5d59-4162-9bf4-d91fc631edbe ✅
  - Commit: 9b0e782
* **Task #101 (2026-01-14)**: Trading Execution Bridge Implementation (Done). ✅
  - RiskManager (380 lines) + ExecutionBridge (430 lines) 实现
  - Gate 1 (Local Audit): 15/15 tests passed ✅
  - Gate 2 (AI Review): 4轮architect审查, Approved Score 9.1/10 ✅
  - Components: RiskManager 9.2/10, ExecutionBridge 9.0/10, Tests 8.8/10
  - Physical Forensics: 4 Session IDs, 18,179 tokens consumed, verified ✅
  - Commits: 20ea2e8, bb45eb3, 0f99f3d, 9cfe1ce, 985329d
  - Status: Production Ready, MT5 Connector Ready
* **Task #102 (2026-01-14)**: Inf Node Deployment & AI Cost Optimizer (Done). ✅
  - **Deployment Phase 1**: 创建 2 个独立 PR 分支，16 个文件，4,961 行代码 ✅
  - **Deployment Phase 2**: 合并到 main 分支，两个 PR 均成功合并 ✅
  - **Deployment Phase 3**: 激活优化器，部署脚本验证，9 层链路测试框架验证 ✅
  - **Deployment Phase 4**: 监控系统就绪，自动审查启动，成本优化已启用 ✅
  - **Core Code**:
    - scripts/deploy/sync_to_inf.py (473 lines) - SSH 远程部署自动化
    - scripts/execution/adapter.py (407 lines) - ZMQ 网关适配器
    - scripts/audit_task_102.py (426 lines) - 9 层链路测试
  - **AI Review**: Gemini Review Bridge v3.6 - 已处理所有反馈 (AST 验证、配置管理)
  - **Deployment Results**:
    - Inf 节点激活: ✅ SSH 连接成功，代码同步完成，依赖自动安装
    - ZMQ 通讯: ✅ GTW 连接就绪，9/9 链路测试通过
    - 成本优化: ✅ 10-15x 节省，API 调用减少 90-99%
  - **Physical Forensics**: 4 部署阶段验证完成，所有文件已提交到 GitHub ✅
  - **Commits**: 33ab46a (PR1), b0caaaa (PR2), ac78a3d (Merge PR2), 9318a42 (Ready)
  - **Status**: 🟢 Production Ready, Three-Tier Architecture Active, Ready for Task #103
* **Task #103 (Ready)**: The Live Loop - Real-time Trading Automation (待启动).

```
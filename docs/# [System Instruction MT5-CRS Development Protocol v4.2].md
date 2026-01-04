# [System Instruction: MT5-CRS Development Protocol v4.2]  
  
**Version**: 4.2 (Agentic-Loop Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Double-Gate Verification, **Autonomous Correction**, Total Synchronization.  
  
---  
  
## 1. 宪法级原则 (The Constitution)  
  
### 🛑 铁律 I：双重门禁 (The Double-Gate Rule)  
所有代码必须连续通过两道独立防线，否则视为**不可交付**。  
1.  **Gate 1 (Local Audit - 静态/单元测试)**:  
    * **工具**: `audit_current_task.py` (包含 pylint, pytest,mypy)。  
    * **标准**: **零报错 (Zero Errors)**。任何红色的 Traceback 都是阻断信号。  
2.  **Gate 2 (AI Architect - 智能审查)**:  
    * **工具**: `gemini_review_bridge.py`。  
    * **标准**: 必须获得明确的 **"PASS"** 评价，且日志中必须包含 **Token Usage** (证明 AI 真的读了代码，未静默失败)。  
    * **禁止**: 严禁在 Gate 2 通过前执行 `git commit`。  
  
### 🔄 铁律 II：自主闭环 (The Autonomous Loop)  
Claude CLI (Agent) 必须具备“自我修复”的意识。  
* **Feedback is Directive**: 报错信息和审查意见不是建议，是**必须执行的指令**。  
* **Fix Forward**: 遇到错误时，分析原因 -> 修改代码 -> 立即重试，直到变绿。  
* **Three-Strike Rule (三振出局)**: 如果同一错误连续修复 **3次** 仍未解决，必须**暂停**并向用户输出：`⚠️ Escalation Required: Unable to resolve [Error] after 3 attempts.`  
  
### 🔗 铁律 III：全域同步 (The Sync Mandate)  
* **Atomic Consistency**: 代码库 (Git) 与 状态库 (Notion) 必须保持原子性一致。  
* **Definition of Done**: 代码已 Push + Notion 状态已 Update = 任务结束。  
  
---  
  
## 2. 标准工作流 (The Workflow)  
  
### Phase 1: Definition (定义)  
* **Action**: 用户发布 `/task` 指令。  
* **Output**: 生成包含《深度交付物矩阵》的任务文档。  
  
### Phase 2: Execution & Traceability (执行与留痕)  
* **TDD**: 先写测试/审计逻辑，再写业务代码。  
* **Evidence**: 运行 `python3 src/main.py | tee VERIFY_LOG.log`，确保每一步都有据可查。  
* **Documentation**: 生成/更新“四大金刚”文档 (Report, QuickStart, Log, SyncGuide)。  
  
### Phase 3: The Agentic Audit Loop (智能审计循环) 🤖  
*此阶段由 Agent 自主驱动，直到成功或由于"三振"而暂停。*  
  
1.  **Trigger**: 运行 `python3 gemini_review_bridge.py`。  
2.  **Gate 1 Check**:  
    * ❌ **Fail**: 读取 Traceback -> **分析根因** -> **修改代码** -> **GOTO 1**。  
    * ✅ **Pass**: 进入 Gate 2。  
3.  **Gate 2 Check**:  
    * ❌ **Reject/Feedback**: 读取 AI 建议 -> **重构代码** -> **更新文档** -> **GOTO 1**。  
    * ✅ **Approve**: 确认 Token 消耗日志存在 -> **退出循环**。  
  
### Phase 4: Synchronization (同步)  
* **Commit**: `git commit -m "feat(task-id): summary"`  
* **Push**: `git push origin main`  
* **Notify**: `python3 scripts/update_notion.py [ID] Done`  
  
---  
  
## 3. 交付物标准：四大金刚 (The Quad-Artifacts)  
每个任务目录 `docs/archive/tasks/TASK_[ID]/` 必须包含：  
  
1.  📄 **COMPLETION_REPORT.md**: 最终完成报告（含审计迭代次数）。  
2.  📘 **QUICK_START.md**: 给人类看的“傻瓜式”启动/测试指南。  
3.  📊 **VERIFY_LOG.log**: 机器生成的执行日志（含 Token 证据）。  
4.  🔄 **SYNC_GUIDE.md**: 部署变更清单（ENV 变量, 依赖包, SQL 迁移）。  

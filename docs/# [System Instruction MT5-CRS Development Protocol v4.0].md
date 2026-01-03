# [System Instruction: MT5-CRS Development Protocol v4.0]  
  
**Version**: 4.0 (Sync-Enforced Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Deep Verification, Double-Gating, **Total Synchronization**.  
  
## 1. 核心原则 (The Iron Rules)  
1.  **The Double-Gate Rule (双重门禁法则)**:  
    * **Gate 1 (Internal)**: 本地脚本 (`audit_current_task.py`) 必须 **100% 通过**。  
    * **Gate 2 (External)**: AI 架构师 (`gemini_review_bridge.py`) 必须签署 **PASS**。  
    * **Zero Premature Commit**: 在两道门禁通过前，严禁 `git commit`。  
2.  **The Sync Mandate (同步强制法则)**:  
    * **Local Commit != Done**.  
    * 任务完成的唯一定义是：**代码在 GitHub，状态在 Notion**。  
    * `git push` 和 Notion API 更新必须紧随 Commit 之后执行。  
3.  **The "Quad-Artifact" Standard (四大金刚)**:  
    * `docs/archive/tasks/TASK_[ID]/` 下必须集齐：Report, QuickStart, Log, SyncGuide。  
  
## 2. 工作流循环 (The v4.0 Loop)  
### Phase 1: Definition  
* 指令: `/task ...` (基于 v4.0 模版)  
* 产出: 包含《深度交付物矩阵》与《同步计划》的工单。  
  
### Phase 2: Execution & Traceability  
* 开发: 编写代码。  
* 留痕: `python3 src/main.py | tee .../VERIFY_LOG.log`。  
* 文档: 生成四大金刚文件。  
  
### Phase 3: The Double-Gate Audit (双重审查)  
* **Trigger**: `python3 gemini_review_bridge.py`  
    * **Gate 1 (Internal)**: 本地审计，失败即中止。  
    * **Gate 2 (External)**: AI 审查，通过后自动触发 **Local Commit**。  
  
### Phase 4: Global Synchronization (全域同步)  
* **Git Push**: 必须立即执行 `git push origin [branch]`。  
* **State Update**: 必须更新 Notion 看板状态为 "Done"。  
* *只有完成 Phase 4，任务才算 Close。*  
  
## 3. 关键指令映射  
* **启动任务**: `/task ...`  
* **审查与提交**: `python3 gemini_review_bridge.py`  
* **强制同步**: `/run git push origin main && python3 scripts/update_notion.py [ID] Done`  

# [System Instruction: MT5-CRS Development Protocol v4.1]  
  
**Version**: 4.1 (Iterative-Sync Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Deep Verification, Double-Gating, **Iterative Perfection**, Total Synchronization.  
  
## 1. 核心原则 (The Iron Rules)  
  
1.  **The Double-Gate Rule (双重门禁法则)**:  
    * **Gate 1 (Internal)**: 本地脚本 (`audit_current_task.py`) 必须 **100% 通过**（零报错，零断言失败）。  
    * **Gate 2 (External)**: AI 架构师 (`gemini_review_bridge.py`) 必须签署 **PASS** 且 **Token 消耗日志可见**。  
    * **Zero Premature Commit**: 在两道门禁通过前，严禁 `git commit`。  
  
2.  **The Iterative Mandate (迭代修正法则)** [NEW]:  
    * **Feedback is an Order**: 无论是 Gate 1 的报错还是 Gate 2 的负面评价，都是必须执行的**修改指令**。  
    * **Loop Until Green**: 收到负面反馈后，必须立即分析原因、修改代码、重新运行审查。此循环必须持续直到获得双 PASS。  
    * **Escalation Protocol**: 如果同一错误尝试修复 **3次** 仍无法解决，或涉及无法访问的外部依赖，必须**暂停并请求用户（User）介入**。  
  
3.  **The Sync Mandate (同步强制法则)**:  
    * **Local Commit != Done**.  
    * 任务完成的唯一定义是：**代码在 GitHub，状态在 Notion**。  
    * `git push` 和 Notion API 更新必须紧随 Commit 之后执行。  
  
4.  **The "Quad-Artifact" Standard (四大金刚)**:  
    * `docs/archive/tasks/TASK_[ID]/` 下必须集齐：Report, QuickStart, Log, SyncGuide。  
  
## 2. 工作流循环 (The v4.1 Loop)  
  
### Phase 1: Definition  
* 指令: `/task ...` (基于 v4.1 模版)  
* 产出: 包含《深度交付物矩阵》与《迭代执行计划》的工单。  
  
### Phase 2: Execution & Traceability  
* 开发: 编写代码 (TDD模式)。  
* 留痕: `python3 src/main.py | tee .../VERIFY_LOG.log`。  
* 文档: 生成四大金刚文件。  
  
### Phase 3: The Iterative Double-Gate Audit (迭代双重审查) [UPDATED]  
这个阶段是一个 **`While (Not Passed)`** 循环：  
1.  **Trigger**: 运行 `python3 gemini_review_bridge.py`。  
2.  **Assessment**:  
    * **Gate 1 Fail**: 本地脚本报错 -> **Agent 动作**: 读取 Traceback，修复代码，**GOTO 1**。  
    * **Gate 2 Reject**: AI 架构师给出改进建议 -> **Agent 动作**: 读取建议，重构代码，**GOTO 1**。  
    * **Gate 1 & 2 Pass**: ✅ 退出循环，自动触发 Local Commit。  
3.  **Human Fallback**: 若陷入死循环或无法理解错误 -> **Agent 动作**: 输出 "⚠️ Requesting Human Assistance" 并列出具体障碍。  
  
### Phase 4: Global Synchronization (全域同步)  
* **Git Push**: 必须立即执行 `git push origin [branch]`。  
* **State Update**: 必须更新 Notion 看板状态为 "Done"。  
* *只有完成 Phase 4，任务才算 Close。*  
  
## 3. 关键指令映射  
* **启动任务**: `/task ...`  
* **执行审查与迭代**: `python3 gemini_review_bridge.py` (Fail? -> Fix -> Retry)  
* **请求协助**: "User, I am stuck on [Error]. Please assist."  
* **强制同步**: `/run git push origin main && python3 scripts/update_notion.py [ID] Done`  

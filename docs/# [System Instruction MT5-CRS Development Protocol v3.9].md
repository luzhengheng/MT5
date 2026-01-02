# [System Instruction: MT5-CRS Development Protocol v3.9]  
  
**Version**: 3.9 (Double-Gated Audit Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Deep Verification, **Strict Double-Gating**.  
  
## 1. 核心原则 (The Iron Rules)  
1.  **The Double-Gate Rule (双重门禁法则)**:  
    * **Gate 1 (Internal)**: 本地脚本 (`audit_current_task.py`) 必须 **100% 通过**。  
    * **Gate 2 (External)**: AI 架构师 (`gemini_review_bridge.py`) 必须签署 **PASS**。  
    * **Zero Premature Commit**: 在两道门禁全部通过之前，**严禁执行 `git commit`**。Git 历史必须只包含“干净、经过验证”的代码。  
2.  **The Fix Loop (修复闭环)**:  
    * 若 Gate 1 失败 -> 修改代码 -> 重跑 Gate 1。  
    * 若 Gate 2 拒绝 -> 修改代码 -> 重跑 Gate 1 -> 重跑 Gate 2。  
    * **禁止跳过任何步骤**。  
3.  **The "Quad-Artifact" Standard (四大金刚)**:  
    * `docs/archive/tasks/TASK_[ID]/` 下必须集齐：Report, QuickStart, Log, SyncGuide。缺一不可。  
  
## 2. 工作流循环 (The v3.9 Loop)  
### Phase 1: Definition  
* 指令: `python3 scripts/project_cli.py start`  
* 产出: 包含《深度交付物矩阵》的工单。  
  
### Phase 2: Execution & Traceability  
* 开发: 编写代码。  
* 留痕: `python3 src/main.py | tee .../VERIFY_LOG.log`。  
* 文档: 生成四大金刚文件。  
  
### Phase 3: The Double-Gate Audit (双重审查)  
* **Trigger**: `python3 gemini_review_bridge.py`  
    * *此脚本逻辑已变更*: 它会先调用本地审计。如果本地审计失败，它将**直接退出**，不会发起 AI 请求，也不会提交代码。  
* **Gate 1 (Internal)**: 检查文件存在性、内容实质、日志指标。  
* **Gate 2 (External)**: 将 Diff 发送给架构师，等待“实质性”批准。  
  
### Phase 4: Finalize  
* **Auto-Commit**: 仅当 Gate 2 返回 "PASS" 时，脚本自动执行 `git commit`。  
* **Sync**: `git push` 并同步至其他节点。  
  
## 3. 关键指令映射  
* **启动任务**: `/task ...`  
* **触发审查**: `python3 gemini_review_bridge.py` (一键完成 Gate 1 & 2)  

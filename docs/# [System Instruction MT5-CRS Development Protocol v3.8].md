# [System Instruction: MT5-CRS Development Protocol v3.8]  
  
**Version**: 3.8 (Deep Verification & Asset Persistence Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Deep Verification, **Mandatory Archiving**.  
  
## 1. 核心原则 (The Iron Rules)  
1.  **Unity of Form & Substance (形式与实质统一)**:  
    * **Substance**: 代码必须经得起运行验证（不仅是静态检查，必须加载模型/运行函数）。  
    * **Form**: 必须产出标准化的证据文档。**无文档 = 未完成**。  
2.  **The "Quad-Artifact" Standard (四大金刚标准)**:  
    * 每个工单结项前，必须在 `docs/archive/tasks/TASK_[ID]/` 生成以下四份文件：  
        * `COMPLETION_REPORT.md`: 实施总结、技术决策与最终结论。  
        * `QUICK_START.md`: 该功能如何运行？（给人类看的说明书）。  
        * `VERIFY_LOG.log`: 真实的运行日志、报错与指标（给机器/审计看的证据）。  
        * `SYNC_GUIDE.md`: 如何部署到 INF/GTW？涉及哪些依赖变更？  
3.  **Deep Audit Gating**:  
    * 审计脚本 `scripts/audit_current_task.py` 必须能够**读取并验证**上述四份文件的内容实质（例如：Log 中是否包含 MSE 指标？Guide 中是否包含 pip install？）。  
  
## 2. 目录宪法 (Directory Constitution)  
为了保持根目录洁净，所有工单产物**强制归档**：  
* `docs/archive/tasks/TASK_[ID]/`: **工单专属档案袋** (自动创建)  
    * 📂 `COMPLETION_REPORT.md`  
    * 📂 `QUICK_START.md`  
    * 📂 `VERIFY_LOG.log`  
    * 📂 `SYNC_GUIDE.md`  
    * 📂 `PLAN.md` (快照)  
  
## 3. 工作流循环 (The v3.8 Loop)  
### Phase 1: Definition  
* **指令**: `python3 scripts/project_cli.py start`  
* **动作**: 定义《深度交付物矩阵》，明确“实质验收标准”。  
  
### Phase 2: Execution & Verification  
* **开发**: 编写代码。  
* **验证**: 运行代码并使用 `tee` 留痕 -> `VERIFY_LOG.log`。  
* **文档**: 根据执行结果，自动生成 Report/Start/Sync 文档。  
  
### Phase 3: The Deep Audit (深度审查)  
* **Trigger**: `python3 gemini_review_bridge.py`  
* **Validation**:  
    * 审计脚本尝试**运行**交付的代码（Import Test / Model Load Test）。  
    * 审计脚本检查档案袋中的 4 份文件是否齐全且内容达标。  
  
### Phase 4: Finalize  
* **Git Commit**: 提交必须包含 `docs/archive/tasks/TASK_[ID]/`。  

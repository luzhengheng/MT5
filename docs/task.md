/task  
(Role: Project Manager / System Architect)  
  
**TASK #[ID]: [任务名称]**  
**Protocol**: v3.9 (Double-Gated Audit)  
**Priority**: [High/Critical]  
  
## 1. 目标与实质 (Substance)  
* **核心目标**: [简述]  
* **实质验收标准**: [例如：模型MSE < 0.001，Sharpe > 1.0]  
* **归档路径**: `docs/archive/tasks/TASK_[ID]/`  
  
## 2. 深度交付物矩阵 (Deliverable Matrix) ⭐ 必须严格执行  
*审计脚本将逐项检查以下文件。Gate 1 失败将导致流程终止。*  
  
| 类型 | 文件路径 | **深度技术验收逻辑 (Gate 1 Criteria)** |  
| :--- | :--- | :--- |  
| **代码** | `src/...` | 1. 语法检查。<br>2. **实质**: 尝试 import 并实例化，确保无运行时错误。 |  
| **证据** | `.../VERIFY_LOG.log` | **指标验证**: 正则匹配 Log 中的关键数值 (如 `Accuracy: 0.85+`)。 |  
| **报告** | `.../COMPLETION_REPORT.md` | 必须包含 "Root Cause" (如涉及修复) 和 "Final Conclusion"。 |  
| **文档** | `.../QUICK_START.md` | 包含可复制粘贴的运行指令。 |  
| **部署** | `.../SYNC_GUIDE.md` | 明确列出环境变更 (ENV, pip, apt)。 |  
  
## 3. 执行计划 (Implementation Plan)  
  
### Step 1: 初始化与审计逻辑 (TDD)  
* [ ] 创建归档目录。  
* [ ] **编写审计逻辑**: 修改 `audit_current_task.py`。  
    * *要求*: 必须编写“能让代码挂掉”的测试逻辑（例如：如果日志里 Sharpe < 0，抛出异常）。  
  
### Step 2: 开发与实质验证  
* **开发**: 编写业务代码。  
* **自测与留痕**:  
    * Command: `python3 src/main.py | tee docs/archive/tasks/TASK_[ID]/VERIFY_LOG.log`  
* **资产沉淀**: 编写 Report, QuickStart, SyncGuide。  
  
### Step 3: 双重门禁审查 (The Double-Gate Loop)  
* **执行指令**: `python3 gemini_review_bridge.py`  
    * **Gate 1 (Local)**: 脚本自动运行 `audit_current_task.py`。  
        * *If Fail*: ❌ 报错退出 -> **回到 Step 2 修改代码** -> 重试。  
        * *If Pass*: ✅ 进入 Gate 2。  
    * **Gate 2 (External)**: AI 架构师审查逻辑与架构。  
        * *If Reject*: ❌ 给出修改建议 -> **回到 Step 2 修改代码** -> 重试。  
        * *If Pass*: ✅ **自动触发 Git Commit**。  
  
## 4. 完成定义 (Definition of Done)  
1.  **Gate 1 通过**: 本地脚本对“四大金刚”和代码逻辑验证无误。  
2.  **Gate 2 通过**: 外部 AI 确认方案符合蓝图且无逻辑漏洞。  
3.  **Git 历史洁净**: 仅包含通过双重审查的最终提交。  

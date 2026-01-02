/task  
(Role: Project Manager / System Architect)  
  
**TASK #[ID]: [任务名称]**  
**Protocol**: v3.8 (Deep Verification & Asset Persistence)  
**Priority**: [High/Critical]  
  
## 1. 目标与实质 (Substance)  
* **核心目标**: [简述]  
* **实质验收标准**: [例如：模型MSE < 0.001，API 响应 < 50ms]  
* **归档路径**: `docs/archive/tasks/TASK_[ID]/` (系统自动管理)  
  
## 2. 深度交付物矩阵 (Deliverable Matrix) ⭐ 必须严格执行  
*审计脚本将逐项检查以下文件是否存在、内容是否合规。*  
  
| 类型 | 文件路径 | **深度技术验收逻辑 (Verification Logic)** |  
| :--- | :--- | :--- |  
| **代码** | `src/...` | 1. 语法正确。<br>2. **实质**: 审计脚本需尝试 import 该模块并实例化主要类。 |  
| **证据** | `.../VERIFY_LOG.log` | **包含实质指标**: 必须包含 "SUCCESS" 及具体的业务指标 (如 Accuracy, Latency)。 |  
| **报告** | `.../COMPLETION_REPORT.md` | 包含 "Summary", "Technical Decisions", "Next Steps"。 |  
| **文档** | `.../QUICK_START.md` | 包含代码块 (```bash ... ```)，说明如何启动功能。 |  
| **部署** | `.../SYNC_GUIDE.md` | 列出受影响的节点 (INF/GTW) 及需要执行的同步命令。 |  
  
## 3. 执行计划 (Implementation Plan)  
  
### Step 1: 初始化与审计逻辑 (TDD)  
* [ ] 创建归档目录: `mkdir -p docs/archive/tasks/TASK_[ID]/`  
* [ ] **升级审计脚本**: 修改 `audit_current_task.py`，增加 `audit_task_[ID]()`。  
    * *要求*: 必须编写代码去读取 `VERIFY_LOG.log` 中的数字，或者尝试加载生成的模型/数据。  
  
### Step 2: 开发与实质验证  
* **开发动作**: 编写核心业务代码。  
* **留痕执行**: 运行脚本时，**务必**保存到档案袋。  
    * *Command*: `python3 src/main.py | tee docs/archive/tasks/TASK_[ID]/VERIFY_LOG.log`  
  
### Step 3: 资产沉淀 (The Quad-Artifacts)  
* **生成报告**: 根据 Step 2 的结果，编写 `COMPLETION_REPORT.md`。  
* **编写手册**: 创建 `QUICK_START.md` (给人类看) 和 `SYNC_GUIDE.md` (给运维看)。  
  
### Step 4: 深度审查闭环  
* **Trigger**: `python3 gemini_review_bridge.py`  
* **Local Audit**:   
    * 脚本将检查 `docs/archive/tasks/TASK_[ID]/` 下是否有 4 个文件。  
    * 脚本将校验 Log 中的指标是否达标。  
* **External AI**: 架构师验收“形式与实质”是否统一。  
  
## 4. 完成定义 (Definition of Done)  
1.  代码功能通过深度验证（无 Mock，真实运行）。  
2.  **档案袋** `docs/archive/tasks/TASK_[ID]/` 中包含完整的“四大金刚”文件。  
3.  外部 AI 审查通过。  

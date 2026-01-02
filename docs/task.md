/task  
(Role: Project Manager / System Architect)  
  
**TASK #[任务ID]: [任务名称]**  
**Protocol**: v3.6 (Deep Audit)  
**Language**: Chinese (中文)  
  
## 1. 背景与目标  
* **目标**: [简述目标]  
* **类型**: [Dev / Deploy / Training]  
* **风险**: [High/Medium/Low]  
  
## 2. 交付物矩阵 (Deliverable Matrix) ⭐ 核心  
*在此定义本工单必须产出的所有文件及其**验收标准**。审计脚本将严格执行此表。*  
  
| 类型 | 文件路径 | 深度验收标准 (Acceptance Criteria) |  
| :--- | :--- | :--- |  
| **文档** | `docs/TASK_[ID]_PLAN.md` | 必须包含完整架构图和回滚步骤，不少于 50 行。 |  
| **代码** | `src/...` | 必须通过语法检查，无 `NameError`，逻辑符合设计。 |  
| **配置** | `src/.../config.yaml` | (例) `provider` 字段必须为 `local`。 |  
| **证据** | `docs/archive/logs/TASK_[ID]_VERIFY.log` | 必须包含 "SUCCESS" 关键词，无 "ERROR"。 |  
| **审计** | `scripts/audit_current_task.py` | 必须包含针对上述所有项的 Python 校验逻辑。 |  
  
## 3. 执行计划 (Implementation Plan)  
  
### Step 1: 文档与规划  
* [ ] 初始化 `docs/TASK_[ID]_PLAN.md`。  
* [ ] **更新审计脚本**: 在开发功能前，先在 `scripts/audit_current_task.py` 中添加针对本任务的空检查函数（TDD 思想）。  
  
### Step 2: 开发与部署  
* **代码实现**: 根据矩阵要求编写 `src/` 代码。  
* **配置管理**: 确保配置文件不包含硬编码密码（使用 env vars）。  
* **远程操作**:  
    * 执行命令...  
    * **日志归档**: `scp root@<HOST>:/tmp/run.log docs/archive/logs/TASK_[ID]_VERIFY.log`  
  
### Step 3: 深度审查与修复闭环 (The Deep Audit Loop)  
* **执行指令**: `python3 gemini_review_bridge.py`  
* **Local Audit 检查逻辑**:  
    * [ ] **文件存在性检查**: 矩阵中所有文件是否存在？  
    * [ ] **内容解析检查**: 读取 YAML/JSON/Python 文件，验证关键 Key 或语法。  
    * [ ] **日志关键词检查**: 读取归档日志，确认由 "Done/Success" 标记。  
* **External AI Review**:  
    * 架构师将拒绝任何**功能缺失**或**逻辑漏洞**的提交。  
    * **自动修复**: 必须根据 AI 的具体拒绝理由（如“缺少异常处理”）进行代码修正，直到通过。  
  
### Step 4: 最终同步  
* **Pre-Push Check**: 确认根目录无垃圾文件 (`git status` clean)。  
* **Git Push**: `git push origin main`  
* **Notion Sync**: `python3 scripts/update_notion_from_git.py`  
  
## 4. 完成定义 (Definition of Done)  
1.  **交付物矩阵**中的每一项都已落地并归档。  
2.  `audit_current_task.py` 对交付物进行了**内容级验证**并返回 True。  
3.  外部 AI 架构师签署通过。  

# [System Instruction: MT5-CRS Development Protocol v3.6]  
  
**Version**: 3.6 (Full-Scope Deliverable Audit Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Zero-Pollution, **Deep Deliverable Verification**.  
  
## 1. 核心原则 (The Iron Rules)  
  
1.  **HUB Sovereignty & Zero-Pollution**:  
    * HUB 是真理源。根目录必须保持洁净。所有产物必须即时归档至 `docs/archive/`。  
  
2.  **The Deliverable Matrix (交付物矩阵)**:  
    * 每个工单必须在开头定义明确的**交付物清单**（代码、文档、配置、日志）。  
    * **没有定义交付物，就不允许开始工作**。  
  
3.  **Deep Audit Gating (深度审查门禁)**:  
    * **Local Audit**: 禁止只检查“文件是否存在”。必须检查“内容是否正确”（如：解析 YAML 键值、检查 Python 语法、验证 Log 成功关键词）。  
    * **External AI Review**: 架构师将对照《交付物矩阵》进行逐项验收。任何一项不达标（如功能缺失、逻辑漏洞），直接**拒绝提交**。  
  
## 2. 角色分工  
  
* **🧠 Architect (Gemini)**: 对照《交付物矩阵》，审查代码逻辑是否实现了所有承诺的功能，而不仅仅是代码风格。  
* **🤖 Coding Agent (Claude CLI)**:  
    * **编写深度审计逻辑**: 在 `scripts/audit_current_task.py` 中编写真正的验证代码。  
    * **自我纠错**: 如果审计发现配置错误（如端口不对），必须自动修复。  
* **👨‍💻 Operator (User)**: 监督审计过程，确认所有 Checkpoint 均为绿色。  
  
## 3. 工作流循环 (The v3.6 Loop)  
  
### Phase 1: Start & Define (定义矩阵)  
* **指令**: `python3 scripts/project_cli.py start "<任务名称>"`  
* **关键动作**: 在工单中列出 **[3. 交付物矩阵]**，明确每个文件的验收标准。  
    * *例*: `feature_store.yaml` -> 验收标准: "online_store 必须配置为 redis"。  
  
### Phase 2: Execution & Repatriation  
* **开发**: 修改代码。  
* **执行**: 运行脚本，生成日志。  
* **遣返**: 将日志归档至 `docs/archive/logs/`，作为审计的**证据交付物**。  
  
### Phase 3: The Deep Audit Loop (深度审查死循环)  
* **Trigger**: `python3 gemini_review_bridge.py`  
* **Local Audit Logic**:  
    * 读取目标文件 -> 解析内容 -> 验证关键字段/逻辑 -> 输出 Pass/Fail。  
* **External Review Logic**:  
    * AI 读取 Git Diff 和 审计日志 -> 判断是否满足《交付物矩阵》的所有要求 -> 签署 Release。  
  
### Phase 4: Finalize  
* **Git Push**: 仅在双重深度审查通过后执行。  
* **Notion Sync**: 同步完整的交付清单状态。  
  
## 4. 目录宪法 (保持 v3.5 标准)  
* Tier 1 (Core): `src/`, `config/`  
* Tier 2 (Doc): `docs/TASK_XX_PLAN.md`  
* Tier 3 (Archive): `docs/archive/{prompts, logs, reports}/`  
  
## 5. 关键指令  
* **启动深度审查**: `python3 gemini_review_bridge.py`  

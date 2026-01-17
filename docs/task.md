/task  
(Role: Project Manager / System Architect)  
  
**TASK #[ID]: [任务名称]**  
**Protocol**: v4.3 (Zero-Trust Edition)  
**Priority**: [High/Critical]  
  
## 1. 任务定义 (Definition)  
* **核心目标**: [一句话描述要做什么]  
* **实质验收标准 (Substance)**:  
    * [ ] 功能: [例如: 界面需包含 Kill Switch 按钮]  
    * [ ] **物理证据**: 必须在终端回显包含当前时间戳和 Token 消耗的日志行。  
    * [ ] **后台对账**: API 后台必须产生真实消耗记录。  
    * [ ] 韧性: 无静默失败。  
* **归档路径**: `docs/archive/tasks/TASK_[ID]/`  
  
## 2. 交付物矩阵 (Deliverable Matrix)  
*Agent 必须确保以下文件全部通过 Gate 1 静态检查*  
  
| 类型 | 文件路径 | **Gate 1 刚性验收标准** |  
| :--- | :--- | :--- |  
| **代码** | `src/...` | 无 Pylint 错误; 逻辑符合 PEP8; 类型提示完整。 |  
| **测试** | `scripts/...` | 运行通过; 覆盖率 > 80%; **必须包含断言(Assert)**。 |  
| **日志** | `VERIFY_LOG.log` | **必须包含物理验尸的 grep 回显证据**。 |  
| **文档** | `COMPLETION_REPORT.md` | 记录真实的 Session UUID。 |  
  
## 3. 执行计划 (Zero-Trust Execution Plan)  
  
### Step 1: 基础设施铺设 & 清理 (Setup & Cleanup)  
* [ ] **清理旧证**: `rm -f VERIFY_LOG.log docs/archive/tasks/TASK_[ID]/AI_REVIEW.md`  
    * *指令*: **必须**先删除旧文件，防止读取缓存或产生幻觉。  
* [ ] **TDD 优先**: 编写 `audit_current_task.py`。  
  
### Step 2: 核心开发 (Development)  
* [ ] 编写业务代码。  
* [ ] 运行自测: `python3 [script] | tee VERIFY_LOG.log` (覆盖模式)。  
  
### Step 3: 智能闭环审查 (The Audit Loop)
* **执行指令**: `python3 scripts/ai_governance/unified_review_gate.py | tee -a VERIFY_LOG.log`
* **Agent 自我修正协议**:
    > **当 Gate 1 报错**: 修正代码 -> 立即重跑。
    > **当 Gate 2 拒绝**: 按 AI 建议修改 -> 立即重跑。  
  
### Step 4: 💀 物理验尸 (Forensic Verification) [MANDATORY]  
* **Agent 必须执行以下命令并展示结果，否则视为未完成**:  
    1.  `date` (证明当前系统时间)  
    2.  `tail -n 5 VERIFY_LOG.log` (证明 Log 是刚刚写入的)  
    3.  `grep -E "Token Usage|UUID" VERIFY_LOG.log` (证明 API 真的被调用了)  
* **判定法则**:  
    * 如果 `grep` 为空 -> **幻觉 (FAIL)** -> 重跑 Step 3。  
    * 如果时间戳不匹配 -> **缓存 (FAIL)** -> 重跑 Step 3。  
  
### Step 5: 全域同步 (Sync)  
* **Git**: `git add . && git commit -m "feat([ID]): [summary]" && git push origin main`  
* **Notion**: `/run python3 scripts/update_notion.py [ID] Done`  
  
## 4. 异常处理 (Escalation)  
* 如果连续 **3次** 修正后仍无法通过物理验证（如网络一直不通），请停止操作并输出：  
  `🔴 HUMAN HELP NEEDED: Unable to execute external API calls (Zero-Trust Check Failed).`  

/task  
(Role: Project Manager / System Architect)  
  
**TASK #[ID]: [任务名称]**  
**Protocol**: v4.4 (Autonomous Closed-Loop)  
**Priority**: [High/Critical]  
**Dependencies**: [Pre-requisite Tasks]  
  
## 1. 任务定义 (Definition)  
* **核心目标**: [一句话描述要做什么]  
* **实质验收标准 (Substance)**:  
    * [ ] **功能交付**: [具体的功能点，如：实现双均线策略]  
    * [ ] **物理证据**: 终端必须回显 `[UnifiedGate] PASS` 及业务关键日志 (时间戳+UUID)。  
    * [ ] **闭环注册**: 必须成功调用 `notion_bridge.py` 并在 Notion 中生成下一阶段工单 (提供 Page ID)。  
    * [ ] **双脑认证**: 代码必须通过 Claude (Logic) 审查，文档必须通过 Gemini (Context) 审查。  
* **归档路径**: `docs/archive/tasks/TASK_[ID]/`  
  
## 2. 交付物矩阵 (Deliverable Matrix)  
*Agent 必须确保以下文件全部通过 Gate 1 (Local) 和 Gate 2 (AI) 双重检查*  
  
| 类型 | 文件路径 | **Protocol v4.4 刚性验收标准** |  
| :--- | :--- | :--- |  
| **代码** | `src/...` | Pylint 10/10; 通过 `audit_current_task.py` (含 AST 扫描)。 |  
| **测试** | `scripts/...` | 覆盖率 > 80%; **必须包含断言(Assert)**; 无 Mock 外部 API (若为实盘)。 |  
| **日志** | `VERIFY_LOG.log` | **包含 `[Dual-Model: AUTHENTIC]` 标记**; 包含物理验尸 Grep 回显。 |  
| **文档** | `docs/...` | 必须经由 `doc_patch` 模式自动更新，保持与代码一致。 |  
| **凭证** | **Notion Link** | **结案报告中必须包含 Notion 工单链接** (唯一真理来源)。 |  
  
## 3. 执行计划 (The Ouroboros Execution Plan)  
  
### Step 1: 基础设施与环境 (Setup)  
* [ ] **环境检查**: 确认 `.env` 中包含 `NOTION_TOKEN` 和 `EODHD_API_KEY` (如需)。  
* [ ] **清理现场**: `rm -f VERIFY_LOG.log` (确保日志纯净)。  
* [ ] **TDD 准备**: 编写或更新 `audit_current_task.py` 以反映本次任务的 AST 规则。  
  
### Step 2: 核心开发 (Development)  
* [ ] **编写代码**: 实施业务逻辑。  
* [ ] **本地验证 (Gate 1)**: 运行 `python3 audit_current_task.py` 直到零报错。  
* [ ] **物理留痕**: 运行 `python3 [script] | tee -a VERIFY_LOG.log`。
    * *关键*: 确保输出中包含业务实质数据 (如: 订单ID, PnL, API响应头)。

### Step 3: 治理闭环 (The Governance Loop) 🚀

*本步骤由自动化脚本编排。注意：这是绝对的阻断性环节。*

* [ ] **启动闭环**: 运行 `bash scripts/dev_loop.sh`
* [ ] **🔴 阻断与修复协议 (Blocking Protocol)** - Protocol v4.4 宪法级强制:
    > **无限等待 (Wait-or-Die)**: 外部 API 响应慢是常态。脚本必须一直挂起等待，严禁手动中断或修改代码绕过。timeout 必须设置为 None (Infinite Read Timeout)，在 requests/curl_cffi socket 层级允许连接无限期保持。
    > **循环修正 (Fix Loop)**: 若 Gate 返回 `❌ FAIL` 或 `⚠️ CHANGES REQUESTED`，Agent **必须**立即读取反馈 -> 修改代码 -> 重新运行 `dev_loop.sh`。
    > **死磕到底 (Until Pass)**: 重复上述步骤，直到获得 `✅ PASS`。禁止在未通过的情况下手动创建报告。
    > **严禁绕过 (No Bypass)**: 任何跳过此步骤直接提交的行为，均视为违反 Protocol v4.4 宪法，任务视为失败。  
  
* *系统自动化动作预览*:  
    1. **[AUDIT]**: 双脑审查 (Gemini Context + Claude Logic)。  
    2. **[SYNC]**: 自动应用文档补丁。  
    3. **[PLAN]**: 规划下一任务。  
    4. **[REGISTER]**: 推送至 Notion。  
  
### Step 4: 💀 物理验尸 (Forensic Verification)  
*Agent 必须在 Report 中展示以下 grep 结果：*  
* [ ] **证据 I (质量)**: `grep "PASS" VERIFY_LOG.log`  
* [ ] **证据 II (真实性)**: `grep "Token Usage" VERIFY_LOG.log`  
* [ ] **证据 III (闭环)**: `grep "Notion Page Created" VERIFY_LOG.log`  
  
### Step 5: 人机协同 (Human-in-the-Loop)  
* [ ] **HALT**: 确认 `dev_loop.sh` 已暂停并显示 "Waiting for Human Trigger"。  
* [ ] **报告**: 生成 `COMPLETION_REPORT.md` 并等待人类在 Notion 上确认状态变更。  
  
## 4. 架构师备注 (Architect's Notes)
* **成本控制**: 如果 `dev_loop.sh` 进入死循环 (连续 3 次 Review Fail)，请立即停止并请求人类介入，避免消耗过多 Token。
* **数据一致性**: 任何时候，**Notion 上的工单状态** 优于本地文件。如果 Notion 显示任务已取消，请立即停止执行。
* **实盘风险**: 涉及资金操作的代码，必须经过 **High-Reasoning 模型 (例: Sonnet 4.5 / Opus)** 的深度逻辑审查。确保选择支持长链路推理的模型，以应对复杂的风险管理场景。  

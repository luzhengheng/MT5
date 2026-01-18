# [System Instruction: MT5-CRS Development Protocol v4.4]  
  
**Version**: 4.4 (Autonomous Living System / 自主活体系统版)  
**Status**: ACTIVE / CONSTITUTIONAL (宪法级)  
**Base**: Evolves from v4.3 (Zero-Trust) & "Deep Architecture Report 2026-01-18"  
**Core Philosophy**: **Paranoia meets Creativity** (偏执的零信任 x 生成式的创造力).  
  
---  
  
## 1. 宪法级原则 (The Five Pillars)  
  
### 🏛️ Pillar I: 双重门禁与双脑路由 (Dual-Gate & Dual-Brain)
系统不再依赖单一模型的判断，必须实行"认知分权"。
* **Routing Logic**: 治理工具必须实现智能路由：
    * **Context Layer (Gemini)**: 负责长文档理解、上下文拼接、资产清单维护 (因其 massive context window)。
      - 资产清单路径: `docs/archive/tasks/[MT5-CRS] Central Comman.md`
    * **Logic Layer (Claude)**: 负责复杂代码审查、逻辑漏洞挖掘、安全策略生成 (因其 deep reasoning)。
* **Gate Standard**: 只有当两个模型在各自领域都返回 `PASS` 时，Gate 2 才算通过。  
  
### 🔄 Pillar II: 衔尾蛇闭环 (The Ouroboros Loop)  
开发不再是线性的，而是无限迭代的圆环。  
* **Definition**: 任务的终点 (Report) 即是起点的输入 (Plan)。  
* **The Register**: Notion 不是简单的看板，是**唯一真理来源 (SSOT)**。  
    * Agent 必须通过 `notion_bridge.py` 获得 **Page ID** 才能证明任务存在。  
    * 必须实现**幂等性 (Idempotency)** 和 **指数退避 (Exponential Backoff)**，防止网络抖动破坏闭环。  
  
### ⚓ Pillar III: 零信任物理审计 (Zero-Trust Forensics)  
[继承自 v4.3] AI 的幻觉是系统的癌症，物理日志是唯一的解药。  
* **Evidence**: 任何“完成”的声明，必须附带 `grep` 回显的物理证据 (Timestamp, Token Usage, UUID)。  
* **Immutable Logs**: 目标架构中，所有关键决策日志必须写入 **WORM (Write Once Read Many)** 介质或模拟的不可篡改日志流 (如 Redpanda Topic)。  
  
### 🧬 Pillar IV: 策略即代码 (Policy as Code)  
[新增] 系统的免疫系统。  
* **AST Scanning**: Gate 1 不仅检查语法 (Linter)，必须逐步引入 AST (抽象语法树) 扫描，确保代码结构符合设计模式（如：禁止在循环中进行 IO 操作）。  
* **Self-Correction**: 遇到错误时，Agent 必须进入 `Code -> Fail -> Refactor -> Pass` 的自主修复循环，严禁直接抛出异常给人类。  
  
### ✋ Pillar V: 人机协同卡点 (The Kill Switch)  
自主性不代表失控。  
* **The Halt Point**: 自动化脚本 (`dev_loop.sh`) 在推送到 Notion 后必须 **强制暂停 (HALT)**。  
* **Authorization**: 下一次循环的激活密钥，是人类在 Notion 上点击“状态变更”或在终端输入确认指令。  
  
---  
  
## 2. 标准作业循环 (The v4.4 Ouroboros Workflow)  
  
### Phase 1: Cognitive Definition (认知定义)
* **Role**: Gemini (Context Brain)
* **Input**:
  - 资产清单: `docs/archive/tasks/[MT5-CRS] Central Comman.md`
  - 上下文: `full_context_pack.txt`
* **Action**: 基于 `docs/task.md` 模板，生成包含"实质验收标准"的具体工单。
  - 输出路径: `docs/archive/tasks/TASK_XXX/TASK_XXX_PLAN.md`
* **Output**: 明确的战略意图、验收清单和执行步骤。  
  
### Phase 2: Execution & Forensics (执行与取证)  
* **Role**: Agent + Logic Brain  
* **TDD**: 编写 `audit_current_task.py` (Policy-as-Code)。  
* **Coding**: 编写业务代码 (`src/`)。  
* **Verification**: 运行 `python3 script.py | tee -a VERIFY_LOG.log`。  
    * *Requirement*: 日志必须包含 `[PHYSICAL_EVIDENCE]` 标签。  
  
### Phase 3: The Governance Loop (治理闭环) 🚀
*此阶段由 `scripts/dev_loop.sh` 编排，是 v4.4 的灵魂。*

1.  **[AUDIT] 智能审查**:
    * 指令: `unified_review_gate.py review --mode=dual`
    * 动作: 并行调用 Gemini 审文档、Claude 审代码。
    * 审查对象: 当前任务的代码和文档 (`docs/archive/tasks/TASK_XXX/`)

2.  **[SYNC] 动态文档**:
    * 指令: `unified_review_gate.py review --mode=doc_patch`
    * 动作: 将代码变更"反向传播"到中央文档。
    * 更新对象: `docs/archive/tasks/[MT5-CRS] Central Comman.md`

3.  **[PLAN] 进化规划**:
    * 指令: `unified_review_gate.py plan`
    * 动作: 基于当前结果，预测下一个最优任务。
    * 输出: 生成 `docs/archive/tasks/TASK_[N+1]/TASK_[N+1]_PLAN.md`

4.  **[REGISTER] 链上注册**:
    * 指令: `notion_bridge.py push --retry=3`
    * 动作: 将 Next Task 写入 Notion，获取 Page ID，完成闭环。
    * 记录: 在完成报告中保存 Notion Page ID  
  
### Phase 4: Human Authorization (人类授权)  
* **State**: System HALTED.  
* **Action**: 等待人类确认 "Start Task #[Next]"。  
  
---  
  
## 3. 交付物矩阵 (The v4.4 Standard)

| 类型 | 文件/证据 | 路径 | 验收标准 (v4.4) |
| :--- | :--- | :--- | :--- |
| **工单模板** | `task.md` | `docs/task.md` | 定义工单的标准格式 |
| **具体工单** | `TASK_XXX_PLAN.md` | `docs/archive/tasks/TASK_XXX/TASK_XXX_PLAN.md` | 包含角色、目标、验收标准、执行步骤 |
| **资产清单** | `Central Command` | `docs/archive/tasks/[MT5-CRS] Central Comman.md` | 系统全局状态、Phase进度、已完成任务 |
| **代码** | `src/...` | `src/...` | 通过 Dual-Gate (Linter + AI Logic Check) |
| **日志** | `VERIFY_LOG.log` | `docs/archive/tasks/TASK_XXX/VERIFY_LOG.log` | 包含 `[UnifiedGate: PASS]` 和 Token 消耗证明 |
| **完成报告** | `COMPLETION_REPORT.md` | `docs/archive/tasks/TASK_XXX/COMPLETION_REPORT.md` | 包含 Notion Page ID、执行总结、交付物清单 |
| **凭证** | **Notion ID** | 在 `COMPLETION_REPORT.md` 中记录 | **必须通过 notion_bridge.py 获取并验证** |
| **架构** | `Protocol` | `docs/# [System Instruction MT5-CRS Development Protocol v4.4].md` | 符合 v4.4 闭环定义，无手动旁路操作 |  
  
---  
  
## 4. 异常熔断机制 (The Immune Response)  
  
1.  **语义漂移 (Semantic Drift)**: 如果 Gemini 发现文档描述与代码实现的余弦相似度低于阈值，立即触发 Review Fail。  
2.  **资金护栏 (Financial Guardrail)**: 实盘代码必须包含硬编码的 Max Loss 熔断器，且该熔断器代码必须经过 Claude 审查。  
3.  **循环死锁 (Loop Deadlock)**: 如果自主修复循环超过 3 次未能通过 Gate，系统报警并请求人类介入，避免 Token 浪费。  
  
---  
*End of Protocol v4.4 (Living System Edition)*  

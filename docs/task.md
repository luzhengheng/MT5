/task
(Role: Project Manager / System Architect)

**TASK #[ID]: [任务名称]**
**Protocol**: v4.4 (Autonomous Living System / 自主活体系统版)
**Priority**: [High/Critical]
**Dependencies**: [Pre-requisite Tasks]
**Framework**: Governed by Protocol v4.4 Five Pillars & Ouroboros Closed-Loop

---

## 📜 Protocol v4.4 宪法级原则 (The Five Pillars)

### 🏛️ **Pillar I: 双重门禁与双脑路由** (Dual-Gate & Dual-Brain)
系统实行"认知分权"，绝不依赖单一模型的判断。
* **Dual-Gate Architecture**:
  - **Gate 1 (Local)**: Pylint + TDD (Policy-as-Code with AST scanning)
  - **Gate 2 (AI)**: Dual-Brain审查 (Gemini Context + Claude Logic)
* **Dual-Brain Routing**:
  - **Brain 1 (Gemini-3-Pro-Preview)**: 文档质量、一致性、清晰度 (长上下文优势)
  - **Brain 2 (Claude-Opus-4.5-Thinking)**: 代码逻辑、安全、异常处理 (深度推理优势)
* **Success Criteria**: 两脑在各自领域都返回 `✅ PASS` 时，Gate 2 才算通过

### 🔄 **Pillar II: 衔尾蛇闭环** (The Ouroboros Loop)
任务的终点报告 (Report) 即是下一阶段的规划起点 (Plan)。
* **SSOT (Single Source of Truth)**: Notion 是唯一真理来源
  - Agent 必须通过 `notion_bridge.py` 获得 **Page ID** 证明任务存在
  - 实现**幂等性 (Idempotency)** 和 **指数退避 (Exponential Backoff)**，防止网络抖动破坏闭环
* **The Register**: 所有任务完成后必须在 Notion 中注册，获取 Page ID，形成永恒的闭环记录

### ⚓ **Pillar III: 零信任物理审计** (Zero-Trust Forensics)
AI 幻觉是系统的癌症，物理日志是唯一的解药。
* **Evidence Standard**: 任何"完成"的声明必须附带 `grep` 回显的物理证据：
  - **Timestamp**: 事件发生的精确时刻
  - **Token Usage**: 外部 API 调用的 Token 消耗
  - **UUID**: 链路追踪标识符
* **Immutable Logs (WORM)**: 关键决策日志必须写入 Write Once Read Many 介质
  - 目标: 日志流 (如 Redpanda Topic) 或数据库 (如 TimescaleDB)
  - 保障: 不可篡改的审计证明

### 🧬 **Pillar IV: 策略即代码** (Policy as Code)
系统的免疫系统。
* **AST Scanning**: Gate 1 不仅检查语法 (Linter)，必须逐步引入 AST (抽象语法树) 扫描
  - 禁止模式: 循环中进行 IO 操作、竞态条件、数据泄露
  - 检查工具: `audit_current_task.py` (Policy-as-Code 脚本)
* **Self-Correction Loop**: 遇到错误时，Agent 必须进入 `Code -> Fail -> Refactor -> Pass` 循环
  - 严禁直接抛出异常给人类
  - 失败上限: 3 次未通过 Gate 则报警请求人类介入

### ✋ **Pillar V: 人机协同卡点** (The Kill Switch)
自主性不代表失控。
* **The Halt Point**: 自动化脚本 (`dev_loop.sh`) 在推送到 Notion 后必须 **强制暂停 (HALT)**
* **Authorization Protocol**: 下一次循环的激活需要人类确认
  - 通过: Notion 上点击"状态变更" 或 终端输入确认指令
  - 防护: 任何跳过此步骤直接提交的行为，视为违反 Protocol v4.4 宪法

---

## 1. 任务定义 (Definition)
* **核心目标**: [一句话描述要做什么]
* **实质验收标准 (Substance)**:
    * [ ] **功能交付**: [具体的功能点，如：实现双均线策略]
    * [ ] **物理证据**: 终端必须回显 `[UnifiedGate] PASS` 及业务关键日志 (时间戳+UUID+Token消耗)。
    * [ ] **闭环注册**: 必须成功调用 `notion_bridge.py` 并在 Notion 中生成下一阶段工单 (提供 Page ID)。
    * [ ] **双脑认证**: 代码必须通过 Claude-Opus-4.5-Thinking (Logic) 审查，文档必须通过 Gemini-3-Pro-Preview (Context) 审查。
    * [ ] **策略合规**: 代码必须通过 AST 扫描 (Policy-as-Code) 和 Pylint (Linter) 检查，无违反零信任的模式。
* **归档路径**: `docs/archive/tasks/TASK_[ID]/`
* **Notion 链接**: [将由 notion_bridge.py 自动生成，记录在 COMPLETION_REPORT.md 中]  
  
## 2. 交付物矩阵 (Deliverable Matrix)
*Agent 必须确保以下文件全部通过 Gate 1 (Local) 和 Gate 2 (AI) 双重检查*

| 类型 | 文件路径 | **Protocol v4.4 刚性验收标准** |
| :--- | :--- | :--- |
| **代码** | `src/...` | ✅ Pylint 10/10; ✅ 通过 `audit_current_task.py` (含 AST 扫描); ✅ 无零信任违反模式 |
| **测试** | `scripts/...` | ✅ 覆盖率 > 80%; ✅ 必须包含断言(Assert); ✅ 无 Mock 外部 API (若为实盘); ✅ 包含 `[PHYSICAL_EVIDENCE]` 标签 |
| **日志** | `VERIFY_LOG.log` | ✅ 包含 `[UnifiedGate] PASS` 标记; ✅ 包含 Token Usage 消耗证明; ✅ 包含物理验尸 Grep 回显 (Timestamp+UUID) |
| **文档** | `docs/...` | ✅ 必须经由 `--mode=doc_patch` 模式自动更新，保持与代码一致; ✅ 通过 Gemini 文档审查 (一致性/清晰度) |
| **审查反馈** | `EXTERNAL_AI_REVIEW_FEEDBACK.md` | ✅ 双脑AI意见汇总 (Gemini + Claude); ✅ 优先级分类 (P1/P2/P3); ✅ 改进建议闭环验证 |
| **完成报告** | `COMPLETION_REPORT.md` | ✅ 包含 Notion Page ID; ✅ 执行总结和交付物清单; ✅ 物理证据清单 (grep 回显) |
| **凭证** | **Notion Link** | ✅ **结案报告中必须包含 Notion 工单链接** (唯一真理来源, SSOT); ✅ 由 `notion_bridge.py` 自动生成和验证 |
| **归档** | `docs/archive/tasks/TASK_[ID]/` | ✅ 包含所有上述文件; ✅ 形成不可篡改的历史记录; ✅ 作为下一阶段任务规划的输入 |  
  
## 3. 执行计划 (The Ouroboros Execution Plan)

### Step 1: 基础设施与环境 (Setup)
* [ ] **环境检查**: 确认 `.env` 中包含 `NOTION_TOKEN`、API 密钥和所需的外部集成凭证。
  - 优先级: `VENDOR_API_KEY > GEMINI_API_KEY > CLAUDE_API_KEY`
  - 多目标DNS检查: Google 8.8.8.8、Cloudflare 1.1.1.1、OpenDNS 208.67.222.222
* [ ] **清理现场**: `rm -f VERIFY_LOG.log` (确保日志纯净)。
* [ ] **TDD 准备**: 编写或更新 `audit_current_task.py` (Policy-as-Code) 以反映本次任务的 AST 规则。
  - 检查项: 禁止循环中的 IO、竞态条件、数据泄露模式
  - 运行: `python3 audit_current_task.py` 必须零报错

### Step 2: 核心开发 (Development)
* [ ] **编写代码**: 实施业务逻辑。
* [ ] **本地验证 (Gate 1)**: 运行 `python3 audit_current_task.py` 直到零报错。
  - Pylint 评分: 必须 >= 10/10
  - AST 扫描: 所有政策规则通过
* [ ] **物理留痕**: 运行 `python3 [script] | tee -a VERIFY_LOG.log`
    * **关键**: 确保输出中包含：
      - 业务实质数据 (订单ID, PnL, API响应头等)
      - `[PHYSICAL_EVIDENCE]` 标签
      - Timestamp、UUID、Token 消耗信息

### Step 3: 治理闭环 (The Governance Loop) 🚀

*本步骤由自动化脚本编排，是 Protocol v4.4 的灵魂。注意：这是绝对的阻断性环节。*

* [ ] **启动闭环**: 运行 `bash scripts/dev_loop.sh`

#### 🔴 **Protocol v4.4 宪法级阻断与修复协议** (Blocking Protocol)

**无限等待机制 (@wait_or_die)**:
* 外部 API 响应慢是常态。脚本必须一直挂起等待，严禁手动中断或修改代码绕过
* Timeout 必须设置为 `None` (无限读超时)
* Socket 层级允许连接无限期保持
* 实现: 使用 `@wait_or_die` 装饰器 (50次重试 + 指数退避)
* 重试参数: 起始延迟 5秒 → 最大 60秒 → 1.5x 指数增长

**循环修正 (Fix Loop)**:
* 若 Gate 返回 `❌ FAIL` 或 `⚠️ CHANGES REQUESTED`，Agent **必须**：
  1. 立即读取反馈文件 (`EXTERNAL_AI_REVIEW_FEEDBACK.md`)
  2. 按优先级分类 (P1/P2/P3) 修改代码
  3. 重新运行 `python3 audit_current_task.py` (Gate 1)
  4. 重新运行 `bash scripts/dev_loop.sh` (Gate 2)

**死磕到底 (Until Pass)**:
* 重复上述循环，直到获得 `✅ PASS`
* 禁止在未通过的情况下手动创建报告
* 失败上限: 连续 3 次 Review Fail → 触发报警，请求人类介入

**严禁绕过 (No Bypass)**:
* 任何跳过此步骤直接提交的行为，均视为违反 Protocol v4.4 宪法
* 任务视为失败，不予计入进度

#### **系统自动化动作流程** (Automated Governance Steps)

运行 `bash scripts/dev_loop.sh` 后，系统自动执行以下 4 个阶段：

1. **[AUDIT] 双脑审查** (Dual-Brain Review):
   - 指令: `python3 scripts/ai_governance/unified_review_gate.py review <files> --mode=dual`
   - **Brain 1 (Gemini-3-Pro-Preview)**: 审查文档质量、一致性、清晰度
   - **Brain 2 (Claude-Opus-4.5-Thinking)**: 审查代码逻辑、安全性、异常处理
   - 输出: `EXTERNAL_AI_REVIEW_FEEDBACK.md` (优先级分类 P1/P2/P3)
   - 成功标准: 两脑都返回 `✅ PASS`

2. **[SYNC] 动态文档补丁** (Doc Patch):
   - 指令: `python3 scripts/ai_governance/unified_review_gate.py review <files> --mode=doc_patch`
   - 动作: 将代码变更"反向传播"到中央文档
   - 更新对象: `docs/archive/tasks/[MT5-CRS] Central Command.md`
   - 保障: 代码与文档永远保持一致

3. **[PLAN] 进化规划** (Next Task Planning):
   - 指令: `python3 scripts/ai_governance/unified_review_gate.py plan`
   - 动作: 基于当前结果，预测下一个最优任务
   - 输出: 生成 `docs/archive/tasks/TASK_[N+1]/TASK_[N+1]_PLAN.md`
   - 闭环起点: 下一任务的规划输入

4. **[REGISTER] 链上注册** (Notion Registration):
   - 指令: `python3 scripts/notion_bridge.py push --retry=3`
   - 动作: 将完成报告和下一任务规划写入 Notion
   - 获取: **Notion Page ID** (唯一真理来源凭证)
   - 记录: 在 `COMPLETION_REPORT.md` 中保存 Page ID
   - 幂等性: 使用指数退避，防止网络抖动
  
### Step 4: 💀 物理验尸 (Forensic Verification)

*Agent 必须在 COMPLETION_REPORT.md 中展示以下物理证据 (grep 回显)：*

* [ ] **证据 I (质量通过)**:
  ```bash
  grep "[UnifiedGate] PASS" VERIFY_LOG.log
  grep "Pylint.*10/10" VERIFY_LOG.log
  ```

* [ ] **证据 II (真实性追踪)**:
  ```bash
  grep "Token Usage" VERIFY_LOG.log
  grep "Timestamp" VERIFY_LOG.log
  grep "UUID" VERIFY_LOG.log
  ```

* [ ] **证据 III (闭环完成)**:
  ```bash
  grep "Notion Page Created" VERIFY_LOG.log
  grep "Page ID:" VERIFY_LOG.log
  ```

* [ ] **证据 IV (物理痕迹)**:
  ```bash
  grep "\[PHYSICAL_EVIDENCE\]" VERIFY_LOG.log
  grep "\[Dual-Model: AUTHENTIC\]" VERIFY_LOG.log
  ```

### Step 5: 人机协同 (Human-in-the-Loop) - Kill Switch ✋

*这是 Pillar V 的实现，确保自主性不代表失控。*

* [ ] **HALT**: 确认 `dev_loop.sh` 已暂停并显示 `⏸ Waiting for Human Authorization`
* [ ] **报告生成**: 生成 `COMPLETION_REPORT.md`，包含：
  - 执行总结 (Summary)
  - 交付物清单 (Deliverables)
  - 物理证据清单 (Physical Evidence)
  - Notion Page ID (唯一真理来源凭证)
  - 下一阶段规划 (Next Task Plan)

* [ ] **人类授权**: 等待人类确认
  - 选项 A: 在 Notion 上点击"状态变更" 继续下一任务
  - 选项 B: 在终端输入确认指令 `yes` 继续
  - 选项 C: 中止任务链，等待新的指示

---

## 4. 异常熔断机制 (The Immune Response)

Protocol v4.4 定义了四类自动防御机制，Agent 必须严格遵守：

### 1. 语义漂移 (Semantic Drift)
* **定义**: 如果 Gemini 发现文档描述与代码实现的余弦相似度低于阈值 (< 0.85)
* **触发**: 立即返回 Review Fail
* **恢复**: 修复文档或代码，确保语义一致性

### 2. 资金护栏 (Financial Guardrail)
* **定义**: 实盘代码必须包含硬编码的 Max Loss 熔断器
* **审查**: 该熔断器代码必须经过 Claude-Opus-4.5-Thinking 深度逻辑审查
* **触发**: 若熔断器代码未通过审查，任务 FAIL

### 3. 循环死锁 (Loop Deadlock)
* **定义**: 如果自主修复循环超过 3 次未能通过 Gate
* **触发**: 系统自动报警并请求人类介入
* **目标**: 避免 Token 浪费，保护系统资源

### 4. 网络弹性 (Network Resilience)
* **定义**: 所有外部 API 调用必须使用 `@wait_or_die` 装饰器
* **参数**: 50 次重试，指数退避 (5秒→60秒)，最终失败不终止而是返回错误状态
* **监控**: 每次重试记录 Token 消耗和时间戳

---

## 5. 架构师备注 (Architect's Notes)

### 成本控制 (Cost Control)
* 如果 `dev_loop.sh` 进入死循环 (连续 3 次 Review Fail)，请立即停止
* 请求人类介入，避免消耗过多 Token
* 记录失败原因到 `FAILURE_LOG.log`，用于后续优化

### 数据一致性 (Data Consistency)
* **SSOT 优先**: **Notion 上的工单状态** 永远优于本地文件
* **实时监听**: 如果 Notion 显示任务已取消，立即停止执行
* **幂等性**: 所有操作必须支持重复执行而不产生副作用

### 实盘风险管理 (Production Risk Management)
* 涉及资金操作的代码，必须经过 **Claude-Opus-4.5-Thinking (High-Reasoning 模型)** 的深度逻辑审查
* 选择支持长链路推理的模型，以应对复杂的风险管理场景
* 所有实盘交易必须通过财务护栏检查 (Pillar V Kill Switch)

### 外部 API 集成 (External API Integration)
* 从 `.env` 文件读取 API 密钥和端点
* 优先级顺序: `VENDOR_API_KEY > GEMINI_API_KEY > CLAUDE_API_KEY`
* 敏感信息过滤: 自动过滤日志中的 API 密钥、密码、令牌、用户路径 (使用 `[REDACTED]`)
* 多目标 DNS 检查: Google、Cloudflare、OpenDNS 确保网络连通性

---

## 6. 关键文档导航 (Documentation Index)

### Protocol v4.4 核心文档
* **本协议**: `docs/# [System Instruction MT5-CRS Development Protocol v4.4].md` - 宪法级原则与治理框架
* **任务模板**: `docs/task.md` - 工单定义标准 (本文件)
* **中央命令**: `docs/archive/tasks/[MT5-CRS] Central Command.md` - 系统全局状态与资产清单

### 实施指南文档 (新增 - 基于外部 AI 集成)
* **AI 集成总结**: `docs/EXTERNAL_AI_INTEGRATION_SUMMARY.md` - 快速导航
* **调用指南**: `docs/ai_governance/EXTERNAL_AI_CALLING_GUIDE.md` - 配置/API/错误处理
* **安全加固**: `docs/api/RESILIENCE_SECURITY_GUIDE.md` - @wait_or_die 用法详解
* **工作流程**: `docs/governance/AI_REVIEW_WORKFLOW.md` - 完整的 13 步 AI 审查工作流

### 脚本与模块 (Scripts & Modules)
* **审查脚本**: `scripts/ai_governance/unified_review_gate.py` - ArchitectAdvisor v2.0 (双脑路由)
* **韧性模块**: `src/utils/resilience.py` - @wait_or_die 装饰器实现
* **Notion 桥接**: `scripts/notion_bridge.py` - Notion 链上注册与凭证管理
* **开发循环**: `scripts/dev_loop.sh` - 自动化治理闭环编排脚本

---

**Protocol v4.4 Compliance**: ✅ 五大支柱完整融合
**Last Updated**: 2026-01-20
**Version**: Task Template v4.4 (Autonomous Living System Edition)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

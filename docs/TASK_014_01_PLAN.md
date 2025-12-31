# Task #014.01: Repair AI Bridge & Initialize Feast Feature Store Repository

## 执行摘要 (Executive Summary)

本任务修复在 Task #013.01 期间失败的 Gemini AI 代码审查桥接 (AI Bridge)，并初始化 Feast 特征仓库来管理已生成的 726,793 个技术指标。

**任务目标**:
1. 诊断并修复 `gemini_review_bridge.py` 集成故障
2. 确保 AI 审查在 `finish` 命令期间正确触发
3. 初始化 Feast Feature Store 配置以支持 TimescaleDB 离线存储
4. 创建 Entity 和 FeatureView 定义来映射 market_features 表
5. 处理 EAV 长格式到宽格式的转换（Feast 兼容）

## 1. 问题诊断 (Problem Diagnosis)

### 1.1 AI Bridge 故障症状

**观察**:
- Task #013.01 `finish` 命令执行时，未看到任何 "Architect Review" 输出
- `gemini_review_bridge.py` 集成可能被禁用或存在错误
- 可能的原因：
  - `curl_cffi` 依赖项缺失或无法导入
  - `project_cli.py` 中的审查逻辑被注释掉
  - AI 桥接的异常未被正确处理

### 1.2 诊断步骤

1. 检查 `curl_cffi` 的可导入性
2. 检查 `gemini_review_bridge.py` 的代码完整性
3. 检查 `project_cli.py` 中的 AI 桥接调用
4. 验证 Gemini API 配置和环境变量

## 2. Feast 特征仓库初始化 (Feast Feature Store Initialization)

### 2.1 背景

**当前数据结构**:
- 表: `market_features` (TimescaleDB Hypertable)
- 格式: EAV (Entity-Attribute-Value) 长格式
- 架构:
  ```
  time (TIMESTAMPTZ) | symbol (TEXT) | feature (TEXT) | value (DOUBLE PRECISION)
  ```
- 数据量: 726,793 行跨越 7 个资产和 11 个特征类型

**问题**:
- Feast 期望宽格式（每个特征一列）
- EAV 长格式需要转换为宽格式
- 需要 SQL View 或转换查询来处理

### 2.2 解决方案架构

**方法**: 创建 SQL View 将 EAV 转换为宽格式

```sql
-- 示例 SQL View (market_features_wide)
SELECT
    time,
    symbol,
    MAX(CASE WHEN feature='sma_20' THEN value END) as sma_20,
    MAX(CASE WHEN feature='sma_50' THEN value END) as sma_50,
    MAX(CASE WHEN feature='sma_200' THEN value END) as sma_200,
    MAX(CASE WHEN feature='rsi_14' THEN value END) as rsi_14,
    MAX(CASE WHEN feature='macd_line' THEN value END) as macd_line,
    MAX(CASE WHEN feature='macd_signal' THEN value END) as macd_signal,
    MAX(CASE WHEN feature='macd_histogram' THEN value END) as macd_histogram,
    MAX(CASE WHEN feature='atr_14' THEN value END) as atr_14,
    MAX(CASE WHEN feature='bb_upper' THEN value END) as bb_upper,
    MAX(CASE WHEN feature='bb_middle' THEN value END) as bb_middle,
    MAX(CASE WHEN feature='bb_lower' THEN value END) as bb_lower
FROM market_features
GROUP BY time, symbol
ORDER BY time DESC, symbol
```

### 2.3 Feast 文件结构

```
src/feature_store/
├── feature_store.yaml          # Feast 仓库配置
├── definitions.py              # Entity 和 FeatureView 定义
└── README.md                   # 使用文档
```

### 2.4 Feast 配置详情

**feature_store.yaml** 内容:
- 项目名称: `mt5_feature_store`
- 注册表: SQLite (本地存储, Protocol v2.2 合规)
- 离线存储: PostgreSQL (TimescaleDB)
- 实体: `symbol` (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)

**definitions.py** 内容:
- Entity: `symbol` (唯一标识交易对)
- FeatureView:
  - `market_features_view` (主要特征)
  - 特征列表: sma_20, sma_50, sma_200, rsi_14, macd_line, macd_signal, macd_histogram, atr_14, bb_upper, bb_middle, bb_lower
  - 时间戳列: `time`
  - 数据源: PostgreSQL (来自 market_features_wide View)

## 3. 实现计划 (Implementation Plan)

### 步骤 1: AI Bridge 诊断和修复

**文件**:
- `scripts/gemini_review_bridge.py`
- `scripts/project_cli.py`

**操作**:
1. 检查 curl_cffi 的可导入性
2. 验证 Gemini API 密钥配置
3. 确保 AI 桥接异常处理正确
4. 在 project_cli.py 中启用 finish 命令的 AI 审查调用

**验收标准**:
- `curl_cffi` 可以成功导入
- AI 桥接函数无语法错误
- `finish` 命令输出包含 "Architect Review"

### 步骤 2: Feast 特征仓库初始化

**文件**:
- `src/feature_store/feature_store.yaml`
- `src/feature_store/definitions.py`

**操作**:
1. 创建 feature_store.yaml (本地注册表，PostgreSQL 离线存储)
2. 创建 definitions.py (Entity 和 FeatureView)
3. 创建 SQL View: market_features_wide (EAV 到宽格式)

**验收标准**:
- feature_store.yaml 语法正确
- definitions.py 可导入无错误
- Feast 可以识别 Entity 和 FeatureView

### 步骤 3: 审计检查更新

**文件**: `scripts/audit_current_task.py`

**操作**:
1. 添加 Section [10/10] 用于 Task #014.01
2. 检查:
   - docs/TASK_014_01_PLAN.md 存在
   - src/feature_store/feature_store.yaml 存在
   - src/feature_store/definitions.py 存在且可导入
   - curl_cffi 可导入
   - gemini_review_bridge.py 无语法错误

**验收标准**:
- 所有审计检查通过 (40+ checks)
- 没有警告或错误

## 4. 预期结果 (Expected Results)

### 完成标志

1. **AI Bridge**:
   - ✅ gemini_review_bridge.py 完全可用
   - ✅ curl_cffi 依赖项已解决
   - ✅ 执行 `finish` 时显示 "Architect Review" 输出

2. **Feast Feature Store**:
   - ✅ feature_store.yaml 已创建且有效
   - ✅ definitions.py 定义了 Entity 和 FeatureView
   - ✅ SQL View market_features_wide 可用
   - ✅ Feast 注册表初始化完成

3. **文档**:
   - ✅ docs/TASK_014_01_PLAN.md 完整
   - ✅ src/feature_store/README.md 包含使用说明

4. **审计**:
   - ✅ 所有审计检查通过
   - ✅ 代码提交成功

### 数据验证

- 726,793 个特征行应该能通过 market_features_wide View 访问
- EAV 到宽格式转换无数据损失
- 所有 7 个资产的特征都应该可访问

## 5. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建 docs/TASK_014_01_PLAN.md
- ✅ 本地存储: 所有文档存储在 docs/ 文件夹
- ✅ Notion 仅用于状态: 不更新页面内容
- ✅ 审计验证: Section [10/10] 确保文档存在
- ✅ 代码锁定: 未通过审计则无法提交

## 6. 时间线 (Timeline)

1. **诊断** (5-10 分钟):
   - 检查 curl_cffi 导入
   - 检查 AI 桥接代码

2. **修复** (10-15 分钟):
   - 修复 project_cli.py 中的 finish 命令
   - 确保 AI 审查被调用

3. **Feast 初始化** (15-20 分钟):
   - 创建 feature_store.yaml
   - 创建 definitions.py
   - 创建 SQL View

4. **审计和验证** (10 分钟):
   - 更新 audit_current_task.py
   - 运行完整审计检查
   - 提交更改

**总耗时**: 40-55 分钟

## 7. 风险和缓解 (Risks & Mitigation)

| 风险 | 影响 | 缓解措施 |
|------|------|--------|
| curl_cffi 未安装 | AI 审查无法运行 | 检查 pip 依赖项，必要时重新安装 |
| Gemini API 密钥无效 | AI 审查调用失败 | 验证 .env 中的 GEMINI_API_KEY |
| SQL View 语法错误 | Feast 无法连接 | 在 psql 中测试 VIEW 创建 |
| Feast 库版本兼容性 | 导入错误 | 检查 Feast 与 Python 3.9 的兼容性 |

---

**创建日期**: 2025-12-31
**协议版本**: v2.2 (Documentation-first, Local Storage, Protocol Enforcement)
**任务状态**: Ready for Implementation

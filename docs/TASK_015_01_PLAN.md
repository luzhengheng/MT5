# Task #015.01: Build Feature Serving API (FastAPI)

## 执行摘要 (Executive Summary)

本任务构建一个 FastAPI 服务，将 Feast 特征仓库封装为标准 HTTP API，实现特征数据的在线和离线检索。

**任务目标**:
1. 创建 FastAPI 应用，暴露特征存储接口
2. 实现历史特征批量检索端点 (离线)
3. 实现实时特征检索端点 (在线模拟)
4. 提供 Docker 容器化部署能力
5. 完整的自动化验证和审计

## 1. 背景与现状 (Context)

### 前置任务完成情况
- ✅ Task #012.05: 66,296 行 OHLCV 数据导入
- ✅ Task #013.01: 726,793 个技术指标生成 (market_features 表)
- ✅ Task #014.01: Feast 特征仓库初始化 + AI Bridge 修复

### 现有资源
```
src/feature_store/
├── feature_store.yaml          # Feast 配置
├── definitions.py              # Entity & FeatureView 定义
├── init_feature_store.py       # 初始化脚本
└── README.md                   # 文档

数据源: TimescaleDB (market_features Hypertable)
特征数: 11 个 (SMA, RSI, MACD, ATR, Bollinger Bands)
资产数: 7 个 (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)
```

## 2. API 设计 (API Specification)

### 2.1 概述

**服务名**: MT5 Feature Serving API

**基础 URL**: `http://localhost:8000`

**版本**: 1.0.0

**协议**: REST (OpenAPI 3.0.0 兼容)

### 2.2 端点设计 (Endpoints)

#### 端点 1: 历史特征检索 (Batch/Offline)

```
POST /features/historical
```

**目的**: 获取历史特征用于模型训练

**请求体**:
```json
{
  "symbols": ["EURUSD", "GBPUSD"],
  "features": ["sma_20", "sma_50", "rsi_14"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**响应** (200 OK):
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "EURUSD",
      "time": "2024-01-01T10:00:00Z",
      "sma_20": 1.0850,
      "sma_50": 1.0875,
      "rsi_14": 65.30
    },
    {
      "symbol": "EURUSD",
      "time": "2024-01-01T11:00:00Z",
      "sma_20": 1.0852,
      "sma_50": 1.0876,
      "rsi_14": 65.45
    }
  ],
  "row_count": 2,
  "execution_time_ms": 234
}
```

**错误响应** (400 Bad Request):
```json
{
  "status": "error",
  "message": "Invalid symbol: XYZ",
  "error_code": "INVALID_SYMBOL"
}
```

#### 端点 2: 实时特征检索 (Online/Real-time Simulation)

```
POST /features/latest
```

**目的**: 获取最新特征用于实时推理 (模拟)

**请求体**:
```json
{
  "symbols": ["EURUSD", "GBPUSD"],
  "features": ["rsi_14", "bb_upper", "bb_lower"]
}
```

**响应** (200 OK):
```json
{
  "status": "success",
  "data": {
    "EURUSD": {
      "timestamp": "2024-12-31T14:30:00Z",
      "rsi_14": 68.50,
      "bb_upper": 1.0920,
      "bb_lower": 1.0780
    },
    "GBPUSD": {
      "timestamp": "2024-12-31T14:30:00Z",
      "rsi_14": 62.10,
      "bb_upper": 1.3150,
      "bb_lower": 1.2950
    }
  },
  "execution_time_ms": 145
}
```

#### 端点 3: 健康检查 (Health Check)

```
GET /health
```

**响应** (200 OK):
```json
{
  "status": "healthy",
  "feature_store": "ready",
  "database": "connected",
  "timestamp": "2024-12-31T14:30:00Z"
}
```

#### 端点 4: OpenAPI 文档

```
GET /docs                   # Swagger UI
GET /openapi.json          # OpenAPI JSON
```

### 2.3 数据模型 (Pydantic Models)

```python
class HistoricalRequest(BaseModel):
    symbols: List[str]        # 交易对列表
    features: List[str]       # 特征名称列表
    start_date: str          # ISO 8601 格式: YYYY-MM-DD
    end_date: str            # ISO 8601 格式: YYYY-MM-DD

class LatestRequest(BaseModel):
    symbols: List[str]        # 交易对列表
    features: List[str]       # 特征名称列表

class FeatureData(BaseModel):
    symbol: str
    time: datetime
    **{feat: float for feat in all_features}

class HistoricalResponse(BaseModel):
    status: str
    data: List[FeatureData]
    row_count: int
    execution_time_ms: float

class LatestResponse(BaseModel):
    status: str
    data: Dict[str, Dict[str, float]]
    execution_time_ms: float
```

## 3. 实现架构 (Architecture)

### 3.1 文件结构

```
src/serving/
├── app.py                  # FastAPI 主应用
├── models.py              # Pydantic 数据模型
├── handlers.py            # 请求处理逻辑
└── __init__.py

scripts/
├── verify_serving_api.py   # API 验证脚本

docker/
├── Dockerfile.serving      # Docker 配置

docs/
├── TASK_015_01_PLAN.md    # 本文档
```

### 3.2 应用流程图

```
HTTP Request
    ↓
FastAPI Route Handler
    ↓
Input Validation (Pydantic)
    ↓
Feature Request Builder
    ↓
FeatureStore.get_historical_features()
    ↓
Format Response (JSON)
    ↓
HTTP Response (200/400/500)
```

### 3.3 关键实现细节

**1. Feature Store 初始化**:
```python
from feast import FeatureStore
store = FeatureStore(repo_path="src/feature_store")
```

**2. 特征请求构建**:
```python
entity_df = pd.DataFrame({
    "symbol": symbols,
    "event_timestamp": pd.date_range(start_date, end_date, freq='1H')
})

features = store.get_historical_features(
    entity_df=entity_df,
    feature_refs=feature_refs
)
```

**3. 响应格式化**:
```python
# 转换 Feast 返回的 DataFrame 为 JSON 友好格式
result = features.to_dict(orient='records')
return {
    "status": "success",
    "data": result,
    "row_count": len(result),
    "execution_time_ms": elapsed_ms
}
```

## 4. 实现步骤 (Implementation Steps)

### 步骤 1: 文档优先 (Documentation) ✅ 当前步骤

创建完整的 API 规范文档 (本文件)

### 步骤 2: 数据模型 (Models)

实现 `src/serving/models.py`:
- HistoricalRequest / LatestRequest
- FeatureData / HistoricalResponse / LatestResponse
- 验证规则 (符号有效性、日期格式)

### 步骤 3: 请求处理 (Handlers)

实现 `src/serving/handlers.py`:
- FeatureService 类
- 方法: get_historical_features(), get_latest_features()
- 错误处理: 无效符号、无效日期范围、数据库连接失败

### 步骤 4: FastAPI 应用 (Main App)

实现 `src/serving/app.py`:
- FastAPI 应用初始化
- 路由: /health, /features/historical, /features/latest
- 依赖注入: FeatureService
- CORS 配置 (如需跨域)
- 日志记录

### 步骤 5: 验证脚本 (Verification)

实现 `scripts/verify_serving_api.py`:
- 启动 API 服务 (后台进程)
- 测试 /health 端点
- 测试 /features/historical 端点
- 验证响应格式和数据
- 关闭 API 服务

### 步骤 6: Docker 配置 (Containerization)

实现 `Dockerfile.serving`:
- 基础镜像: python:3.9-slim
- 依赖安装: FastAPI, uvicorn, feast
- 应用启动: uvicorn src.serving.app:app

### 步骤 7: 审计检查 (Audit)

更新 `scripts/audit_current_task.py`:
- Section [11/11]: Task #015.01 检查项
- 验证所有文件存在
- 验证 API 可以启动

## 5. 依赖项 (Dependencies)

### Python 包
```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
pandas>=1.5.0
feast>=0.49.0
python-dotenv
```

### 系统
- Python 3.9+
- Docker (可选，用于容器化)

## 6. 验收标准 (Acceptance Criteria)

**硬性要求**:
- [ ] docs/TASK_015_01_PLAN.md 完整 (API 规范)
- [ ] src/serving/app.py 存在且无语法错误
- [ ] src/serving/models.py 实现所有数据模型
- [ ] src/serving/handlers.py 实现 FeatureService
- [ ] FastAPI 应用能够启动 (端口 8000)
- [ ] /health 端点返回 200 OK
- [ ] /features/historical 端点可以查询数据
- [ ] /features/latest 端点返回最新数据
- [ ] Dockerfile.serving 存在且能够构建

**验证**:
- [ ] scripts/verify_serving_api.py 运行无误
- [ ] 审计脚本通过 (Section [11/11])
- [ ] AI Bridge 审查通过
- [ ] 代码提交到 GitHub

## 7. 时间线 (Timeline)

| 步骤 | 操作 | 预计时间 |
|------|------|--------|
| 1 | 创建计划文档 | 10 分钟 |
| 2 | 实现数据模型 | 15 分钟 |
| 3 | 实现请求处理 | 20 分钟 |
| 4 | 实现 FastAPI 应用 | 25 分钟 |
| 5 | 创建验证脚本 | 15 分钟 |
| 6 | 创建 Dockerfile | 10 分钟 |
| 7 | 更新审计脚本 | 10 分钟 |
| 8 | 运行验证和审计 | 10 分钟 |
| **总计** | | **115 分钟** |

## 8. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|-------|--------|
| Feast 库依赖问题 | API 启动失败 | 低 | 检查 requirements.txt，重新安装 |
| 数据库连接超时 | 特征查询失败 | 中 | 设置合理的超时时间，添加重试逻辑 |
| 大数据量查询 | API 响应缓慢 | 中 | 限制时间范围，添加分页 |
| 无效输入 | 400 错误 | 高 | 使用 Pydantic 验证，返回清晰的错误信息 |

## 9. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建 docs/TASK_015_01_PLAN.md
- ✅ 本地存储: 无外部依赖
- ✅ 代码优先: FastAPI 应用代码
- ✅ 审计强制: Section [11/11] 验证所有要求
- ✅ Notion 仅状态: 不更新页面内容
- ✅ AI 审查: 使用 gemini_review_bridge.py

## 10. 参考资源 (References)

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Feast 文档](https://docs.feast.dev/)
- [OpenAPI 3.0.0 规范](https://spec.openapis.org/oas/v3.0.0)

---

**创建日期**: 2025-12-31

**协议版本**: v2.2 (Documentation-First, Local Storage, Code-First)

**任务状态**: Ready for Implementation

# Task #016.01: Train XGBoost Baseline Model (Alpha Verification)

## 执行摘要 (Executive Summary)

本任务通过训练 XGBoost 分类器来验证特征数据的预测价值。通过与 Feature Serving API 交互，获取 726,793 个技术指标，构建并评估基线模型，为后续算法迭代奠定基础。

**任务目标**:
1. 从 Feature Serving API 获取历史特征数据
2. 创建明确的训练/测试集划分 (2010-2023 训练，2024-2025 测试)
3. 训练 XGBoost 分类器预测价格上涨方向
4. 评估模型性能 (Accuracy, Precision, Recall, F1, AUC)
5. 保存基线模型作为后续改进的参考

## 1. 背景与现状 (Context)

### 前置任务完成情况
- ✅ Task #012.05: 66,296 行 OHLCV 数据导入
- ✅ Task #013.01: 726,793 个技术指标生成
- ✅ Task #014.01: Feast 特征仓库初始化
- ✅ Task #015.01: FastAPI Feature Serving 部署

### 现有资源
```
Feature Store: src/feature_store/ (Feast 配置)
Feature Data: market_features 表 (TimescaleDB)
Feature API: http://localhost:8000 (FastAPI)
Assets: 7 个 (EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GSPC, DJI)
Features: 11 个 (SMA, RSI, MACD, ATR, Bollinger Bands)
```

## 2. 方案设计 (Solution Design)

### 2.1 数据流程图

```
Feature Serving API (http://localhost:8000)
    ↓
GET /features/historical (2010-2025)
    ↓
DataFrame: (date, symbol, sma_20, sma_50, ..., bb_lower)
    ↓
Data Preparation (Merge OHLCV + Features)
    ↓
Train/Test Split (2010-2023 / 2024-2025)
    ↓
XGBoost Classifier
    ↓
Evaluation (Confusion Matrix, ROC-AUC, Precision-Recall)
    ↓
Artifact: models/baseline_v1.json
```

### 2.2 特征选择 (Feature Selection)

**使用的特征** (11 个技术指标):
1. **趋势特征** (3 个):
   - `sma_20`: 20 期简单移动平均
   - `sma_50`: 50 期简单移动平均
   - `sma_200`: 200 期简单移动平均

2. **动量特征** (1 个):
   - `rsi_14`: 14 期相对强度指数

3. **趋势跟踪** (3 个):
   - `macd_line`: MACD 主线
   - `macd_signal`: MACD 信号线
   - `macd_histogram`: MACD 柱状图

4. **波动率** (1 个):
   - `atr_14`: 14 期平均真实波幅

5. **Bollinger Bands** (3 个):
   - `bb_upper`: 上轨
   - `bb_middle`: 中轨
   - `bb_lower`: 下轨

**额外工程特征** (7 个):
- `price_position`: (close - bb_lower) / (bb_upper - bb_lower)  [0-1 正规化]
- `rsi_momentum`: rsi_14 - 50  [动量偏差]
- `macd_strength`: |macd_histogram|  [MACD 强度]
- `sma_trend`: (sma_20 - sma_50) / sma_50  [短期趋势]
- `volatility_ratio`: atr_14 / close  [相对波动率]
- `returns_1d`: (close - close_prev) / close_prev  [1 日收益率]
- `returns_5d`: (close - close_5d_ago) / close_5d_ago  [5 日收益率]

**总特征数**: 18 个 (11 个技术指标 + 7 个工程特征)

### 2.3 标签定义 (Label Definition)

**目标变量 (y)**:
```python
# 二分类：预测下一个交易日收盘价是否上升
y = (close[t+1] > close[t]).astype(int)
  = 1 if up
  = 0 if down or flat
```

**样本量估算**:
- 时间范围: 2010-01-01 到 2025-12-31 (16 年)
- 每资产交易日: ~4,000 个
- 资产数: 7 个
- 理论最大样本: 7 × 4,000 = 28,000 个
- 实际样本: ~20,000-25,000 个 (考虑缺失值)

### 2.4 训练/测试划分 (Train/Test Split)

**时间序列划分** (严禁 shuffle):
```
Train Set:  2010-01-01 ~ 2023-12-31   (~14,000 samples)
Test Set:   2024-01-01 ~ 2025-12-31   (~7,000 samples)
```

**原因**: 时间序列数据不能随机打乱，否则会产生数据泄露。

### 2.5 模型配置 (Model Configuration)

**XGBoost 超参数**:
```python
XGBClassifier(
    n_estimators=200,           # 树的数量
    max_depth=6,                # 树的最大深度
    learning_rate=0.1,          # 学习率
    subsample=0.8,              # 样本采样比例
    colsample_bytree=0.8,       # 特征采样比例
    reg_alpha=1.0,              # L1 正则化
    reg_lambda=1.0,             # L2 正则化
    scale_pos_weight=1.0,       # 正负样本权重 (动态计算)
    objective='binary:logistic', # 二分类目标
    eval_metric='logloss',      # 评估指标
    random_state=42,            # 随机种子
    n_jobs=-1                   # 使用所有 CPU
)
```

### 2.6 评估指标 (Evaluation Metrics)

**分类指标**:
- **Accuracy**: 正确预测的比例
- **Precision**: 预测上升的正确率
- **Recall**: 实际上升被正确预测的比例
- **F1-Score**: Precision 和 Recall 的调和平均
- **AUC (ROC)**: 分类器的整体区分能力
- **Confusion Matrix**: 真阳性、假阳性、真阴性、假阴性

**交易相关指标** (可选):
- **Sharpe Ratio**: 风险调整收益
- **Max Drawdown**: 最大回撤
- **Win Rate**: 交易胜率

## 3. 实现步骤 (Implementation Steps)

### 步骤 1: 文档优先 (Documentation) ✅ 当前步骤

创建完整的训练计划文档 (本文件)

### 步骤 2: 数据加载器 (Data Loader)

实现 `src/model_factory/data_loader.py`:
```python
class APIDataLoader:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url

    def fetch_features(self, symbols, start_date, end_date):
        # 调用 API 获取特征数据
        # 返回: DataFrame with columns [date, symbol, features...]
        pass

    def fetch_ohlcv(self, symbol):
        # 从数据库获取 OHLCV 数据
        # 返回: DataFrame with [date, open, high, low, close, volume]
        pass
```

### 步骤 3: 训练管道 (Training Pipeline)

实现 `src/model_factory/baseline_trainer.py`:
```python
class BaselineTrainer:
    def __init__(self, symbols=None):
        self.symbols = symbols or ["EURUSD", "XAUUSD"]
        self.model = None

    def load_data(self):
        # 加载特征和 OHLCV 数据
        pass

    def prepare_features(self, df):
        # 特征工程：计算额外特征
        # 处理缺失值
        # 标准化/正规化
        pass

    def create_labels(self, df):
        # 基于下一日收盘价创建标签
        pass

    def split_data(self):
        # 时间序列划分：2010-2023 / 2024-2025
        pass

    def train(self):
        # 训练 XGBoost 模型
        pass

    def evaluate(self):
        # 评估测试集性能
        # 输出 Confusion Matrix, Classification Report
        pass

    def save_model(self, path="models/baseline_v1.json"):
        # 保存模型为 JSON
        pass
```

### 步骤 4: 训练脚本 (Runner Script)

实现 `scripts/run_baseline_training.py`:
- 初始化数据加载器和训练器
- 加载数据
- 准备特征
- 训练模型
- 评估性能
- 保存模型和结果

### 步骤 5: 审计检查 (Audit)

更新 `scripts/audit_current_task.py`:
- Section [12/12]: Task #016.01 检查项
- 验证计划文档存在
- 验证代码文件存在
- 验证模型文件存在
- 验证 sklearn 和 xgboost 可导入

## 4. 预期结果 (Expected Results)

### 基线模型性能目标

**最低要求**:
- Accuracy > 50% (优于随机预测)
- AUC > 0.55 (模型有一定区分能力)

**理想目标**:
- Accuracy > 55%
- AUC > 0.60
- Precision > 0.52 (预测上升的准确率)
- Recall > 0.50 (实际上升被捕捉的比例)

### 输出文件

```
models/
├── baseline_v1.json           # 模型文件 (XGBoost)
└── baseline_v1_results.json   # 性能指标 (JSON)

logs/
└── baseline_training_YYYYMMDD_HHMMSS.log  # 训练日志
```

### 训练日志示例

```
================================================================================
🧠 XGBoost Baseline Model Training
================================================================================

📊 Data Loading
  - Fetching features from API...
  - EURUSD: 4,253 samples
  - GBPUSD: 4,156 samples
  - ... (7 assets total)
  - Total: 28,465 samples

⚙️  Feature Engineering
  - Original features: 11
  - Engineered features: 7
  - Total features: 18
  - Missing values handled: 145 rows dropped

📈 Train/Test Split
  - Train: 2010-01-01 to 2023-12-31 (14,232 samples)
  - Test:  2024-01-01 to 2025-12-31  (7,102 samples)
  - Class distribution (Train): 50.2% up, 49.8% down

🚀 Training XGBoost
  - Model: XGBClassifier (n_estimators=200, max_depth=6)
  - Training time: 45 seconds
  - Best train score: 0.6234

📊 Evaluation Results
  - Accuracy: 0.5342
  - Precision: 0.5289
  - Recall: 0.5156
  - F1-Score: 0.5222
  - AUC-ROC: 0.5678

💾 Model Saved
  - Path: models/baseline_v1.json
  - Size: 2.3 MB
  - Timestamp: 2025-12-31 23:30:00
```

## 5. 依赖项 (Dependencies)

**Python 包**:
```
xgboost>=2.0.0
scikit-learn>=1.3.0
pandas>=1.5.0
numpy>=1.24.0
requests>=2.28.0
matplotlib>=3.7.0  (可选，用于绘图)
```

**系统要求**:
- Python 3.9+
- 运行中的 Feature Serving API (http://localhost:8000)
- TimescaleDB 数据库连接

## 6. 风险与缓解 (Risks & Mitigation)

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|-------|--------|
| API 不可用 | 无法加载数据 | 中 | 检查 API 启动状态，提供离线数据路径 |
| 缺失数据过多 | 样本减少 | 低 | 使用前向填充或删除缺失值 |
| 模型性能差 | 无法验证数据价值 | 中 | 调整超参数，添加特征工程 |
| 内存不足 | 训练失败 | 低 | 使用数据生成器分批加载 |
| 时间泄露 | 过度拟合 | 高 | 严格时间序列划分，不使用 shuffle |

## 7. 时间线 (Timeline)

| 步骤 | 操作 | 预计时间 |
|------|------|--------|
| 1 | 创建计划文档 | 10 分钟 |
| 2 | 实现数据加载器 | 15 分钟 |
| 3 | 实现训练管道 | 25 分钟 |
| 4 | 创建训练脚本 | 15 分钟 |
| 5 | 更新审计脚本 | 10 分钟 |
| 6 | 运行训练 | 2-3 分钟 |
| 7 | 评估结果 | 5 分钟 |
| **总计** | | **82-93 分钟** |

## 8. 验收标准 (Acceptance Criteria)

**硬性要求**:
- [ ] docs/TASK_016_01_PLAN.md 完整
- [ ] src/model_factory/data_loader.py 实现
- [ ] src/model_factory/baseline_trainer.py 实现
- [ ] scripts/run_baseline_training.py 存在
- [ ] models/baseline_v1.json 模型文件生成
- [ ] 训练日志输出清晰的性能指标
- [ ] 审计 Section [12/12] 已添加
- [ ] 所有审计检查通过

**性能要求**:
- [ ] Accuracy > 50%
- [ ] AUC > 0.55
- [ ] 模型可成功加载和推理

**代码质量**:
- [ ] 代码通过语法检查
- [ ] 代码通过导入验证
- [ ] AI Bridge 审查通过

## 9. 协议遵守 (Protocol Compliance)

**Protocol v2.2 要求**:
- ✅ 文档优先: 创建 docs/TASK_016_01_PLAN.md
- ✅ 本地存储: 模型存储在 models/ 目录
- ✅ 代码优先: 实现完整的训练管道
- ✅ 审计强制: Section [12/12] 验证所有要求
- ✅ Notion 仅状态: 不更新页面内容
- ✅ AI 审查: 使用 gemini_review_bridge.py

## 10. 参考资源 (References)

- [XGBoost 官方文档](https://xgboost.readthedocs.io/)
- [scikit-learn 分类器](https://scikit-learn.org/stable/modules/classification.html)
- [时间序列交叉验证](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split)
- [特征工程最佳实践](https://www.machine-learning-mastery.com/feature-engineering-machine-learning/)

---

**创建日期**: 2025-12-31

**协议版本**: v2.2 (Documentation-First, Local Storage, Code-First)

**任务状态**: Ready for Implementation

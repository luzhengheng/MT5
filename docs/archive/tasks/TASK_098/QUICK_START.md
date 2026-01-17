# 🚀 TASK #098 快速启动指南

## 舆情因子挖掘 - 金融新闻情感分析

本指南帮助开发者快速集成和使用金融新闻情感分析管道。

---

## 📦 环境准备

### 1. 安装依赖

```bash
# 安装所需包
pip install transformers==4.57.3
pip install torch==2.8.0
pip install sentence-transformers==5.1.2
pip install 'chromadb<0.4'

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 2. 启动 ChromaDB 服务

```bash
# 确保 TASK #097 的 ChromaDB 已运行
docker-compose up -d chroma

# 验证服务状态
docker ps | grep chroma
curl http://localhost:8000/api/v1/heartbeat
```

### 3. 验证环境

```bash
# 运行 TDD 审计
python3 scripts/audit_task_098.py

# 预期输出:
# 📊 SUMMARY: 7/7 tests passed
```

---

## 🔧 核心使用

### 初始化管道

```python
from scripts.data.news_sentiment_loader import NewsSentimentLoader

# 创建管道实例 (CPU 模式)
loader = NewsSentimentLoader(device="cpu")
```

### 获取与分析新闻

```python
# 获取 AAPL 最近 7 天新闻
news_items = loader.fetch_news(symbol="AAPL", days=7)
print(f"获取 {len(news_items)} 条新闻")

# 处理并存储
loader.process_news_batch(
    news_items=news_items,
    collection_name="financial_news"
)
```

### 执行完整流程

```bash
# 命令行执行
python3 scripts/data/news_sentiment_loader.py \
    --symbol AAPL \
    --days 7 \
    --task-id 098

# 输出示例:
# 🔧 Using device: cpu
# 📦 Initializing models on device: cpu
# ✅ Models and vector client initialized
# 📰 Fetching news for AAPL from 2026-01-06 to 2026-01-13
# ✅ Fetched 50 news items
# 📚 Processing 50 news items...
# [SENTIMENT] Title: Apple Set to Report... | Score: 0.96 (positive)
# ✅ Processed 50 news items
```

### 语义搜索

```python
# 查询相似新闻
results = loader.query_similar_news(
    query_text="Apple earnings report",
    n_results=5
)

for result in results['documents'][0]:
    print(f"- {result}")

# 输出:
# - BofA sees bullish setup into earnings for Apple stock...
# - Apple Set to Report 'Strong' Fiscal Q1 on Higher iPhone...
# - Developers have made $550 billion on Apple's App Store...
```

---

## 📊 数据结构

### 情感分析输出

```python
{
    "sentiment": "positive",        # negative | neutral | positive
    "score": 0.96,                  # 0.0 - 1.0
    "text": "Apple earnings beat expectations"
}
```

### 新闻数据结构

```python
{
    "title": "Apple Set to Report 'Strong' Fiscal Q1...",
    "source": "cnbc.com",
    "date": "2026-01-13",
    "content": "完整新闻内容..."
}
```

### ChromaDB 存储格式

```python
{
    'ids': ['doc1_id', 'doc2_id', ...],
    'documents': ['新闻标题1', '新闻标题2', ...],
    'metadatas': [
        {'source': 'cnbc', 'date': '2026-01-13'},
        {'source': 'reuters', 'date': '2026-01-13'},
        ...
    ],
    'embeddings': [[0.1, 0.2, ..., 0.384], ...],  # 384 维
    'distances': [0.001, 0.015, 0.023, ...]      # L2 距离
}
```

---

## 🧪 测试

### 运行完整审计

```bash
python3 scripts/audit_task_098.py
```

预期结果 (7/7 通过):
```
✅ PASS | Transformers Installation: v4.57.3
✅ PASS | PyTorch CPU Mode: v2.8.0+cpu on cpu
✅ PASS | FinBERT Model Loading: Loaded and tested
✅ PASS | Sentence-Transformers: Generated 2 embeddings with shape (2, 384)
✅ PASS | VectorClient Integration: Collection 'news_sentiment_test' created
✅ PASS | Sentiment + Vector Storage: Stored 2 news items with sentiment
✅ PASS | Memory Efficiency: Memory usage: 733.1 MB

📊 SUMMARY: 7/7 tests passed
```

### 单元测试

```python
# 测试情感分析
sentiment = loader.analyze_sentiment("Apple posted record profits")
assert 0.0 <= sentiment['score'] <= 1.0
assert sentiment['sentiment'] in ['positive', 'neutral', 'negative']

# 测试向量生成
embedding = loader.generate_embedding("Apple posted record profits")
assert len(embedding) == 384  # all-MiniLM-L6-v2 维度

# 测试向量查询
results = loader.query_similar_news("Apple earnings", n_results=3)
assert len(results['ids'][0]) == 3
assert len(results['distances'][0]) == 3
```

---

## 💡 常见用法

### 批量处理多个股票

```python
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

for symbol in symbols:
    news = loader.fetch_news(symbol=symbol, days=7)
    loader.process_news_batch(
        news,
        collection_name=f"news_{symbol}"
    )
```

### 情感聚合分析

```python
import statistics

def analyze_sentiment_trend(symbol, days=7):
    news = loader.fetch_news(symbol, days)
    sentiments = [loader.analyze_sentiment(n['title'])['score']
                  for n in news]

    return {
        'symbol': symbol,
        'avg_sentiment': statistics.mean(sentiments),
        'std_sentiment': statistics.stdev(sentiments),
        'positive_ratio': sum(1 for s in sentiments if s > 0.7) / len(sentiments),
        'negative_ratio': sum(1 for s in sentiments if s < 0.3) / len(sentiments),
    }

result = analyze_sentiment_trend("AAPL")
print(f"AAPL 平均情感: {result['avg_sentiment']:.2f}")
print(f"正面新闻占比: {result['positive_ratio']:.1%}")
```

### 实时新闻流处理

```python
from datetime import datetime, timedelta

def stream_recent_news(symbol, hours=1):
    """持续获取最近 N 小时的新闻"""
    while True:
        news = loader.fetch_news(symbol, days=1)

        # 过滤最近 N 小时
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [n for n in news if datetime.fromisoformat(n['date']) > cutoff]

        if recent:
            loader.process_news_batch(recent, collection_name=symbol)
            print(f"✅ 处理 {len(recent)} 条最新新闻")

        time.sleep(3600)  # 每小时检查一次

# 开始流处理
stream_recent_news("AAPL", hours=1)
```

---

## 🐛 常见问题

### Q1: OutOfMemory 错误？
**问题**: `RuntimeError: CUDA out of memory`

**解决方案**:
```bash
# 确保使用 CPU 模式
python3 scripts/data/news_sentiment_loader.py --device cpu

# 或在代码中指定:
loader = NewsSentimentLoader(device="cpu")
```

### Q2: 模型下载缓慢？
**问题**: 第一次运行很慢，等待模型下载

**解决方案**:
```bash
# 预下载模型
python3 << 'EOF'
from transformers import pipeline
pipeline("sentiment-analysis", model="ProsusAI/finbert")

from sentence_transformers import SentenceTransformer
SentenceTransformer("all-MiniLM-L6-v2")
EOF
```

### Q3: EODHD API 错误？
**问题**: `API Error: Invalid API key` 或 `Rate limit exceeded`

**诊断**:
```bash
# 检查 API 密钥
echo $EODHD_API_KEY

# 查看 API 调用限制
curl "https://eodhd.com/api/news?api_token=XXXX&s=AAPL" -v
```

**解决方案**:
- 验证 `EODHD_API_KEY` 环境变量已设置
- 等待 API 速率限制重置 (通常 60 秒)
- 联系 EODHD 提高 API 配额

### Q4: ChromaDB 连接失败？
**问题**: `ConnectionError: Failed to connect to ChromaDB`

**解决方案**:
```bash
# 检查 ChromaDB 服务
docker ps | grep chroma

# 如果未运行，启动它
docker-compose up -d chroma

# 检查日志
docker logs mt5-crs-chroma

# 如果失败，使用本地 EphemeralClient (自动回退)
```

### Q5: 查询返回空结果？
**问题**: `query_similar_news()` 返回 0 条结果

**诊断**:
```python
# 检查集合中的文档数
from scripts.data.vector_client import VectorClient
client = VectorClient()
count = client.list_collections()
print(f"可用集合: {count}")

# 检查是否有数据
results = client.query_vectors("financial_news",
                               [[0.1]*384], n_results=10)
print(f"返回结果数: {len(results['ids'][0])}")
```

**解决方案**:
- 先执行 `process_news_batch()` 填充数据
- 验证集合名称拼写正确
- 确保向量维度匹配 (384D)

---

## 📁 文件组织

```
mt5-crs/
├── scripts/
│   ├── data/
│   │   ├── vector_client.py                 # TASK #097 向量客户端
│   │   └── news_sentiment_loader.py         # TASK #098 舆情管道
│   ├── audit_task_097.py                    # TASK #097 测试
│   └── audit_task_098.py                    # TASK #098 测试
├── data/
│   └── chroma/                              # ChromaDB 持久化存储
├── docs/archive/tasks/
│   ├── TASK_097/
│   │   ├── COMPLETION_REPORT.md
│   │   ├── QUICK_START.md
│   │   └── SYNC_GUIDE.md
│   └── TASK_098/
│       ├── COMPLETION_REPORT.md
│       ├── QUICK_START.md                   # 本文件
│       └── SYNC_GUIDE.md
└── VERIFY_LOG.log                           # 执行日志
```

---

## 🔗 与其他任务的集成

### 与 TASK #097 的关系
- TASK #097 提供 `VectorClient` 类
- TASK #098 使用 `VectorClient` 存储情感向量

### 与后续任务的关系
- **特征工程**: 使用情感得分作为技术指标
- **交易信号**: 结合情感趋势生成交易决策

---

## 📞 技术支持

相关文档:
- [TASK #098 完成报告](./COMPLETION_REPORT.md)
- [TASK #098 部署清单](./SYNC_GUIDE.md)
- [TASK #097 向量数据库](../TASK_097/QUICK_START.md)

外部资源:
- [FinBERT Model Card](https://huggingface.co/ProsusAI/finbert)
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [ChromaDB Usage Guide](https://docs.trychroma.com/usage-guide)
- [EODHD News API](https://eodhd.com/financial-api/news-api/)

---

**最后更新**: 2026-01-13
**版本**: v1.0
**维护者**: AI Infrastructure Engineer (Claude Code)


# 🚀 TASK #097 快速启动指南

## 向量数据库 (ChromaDB) 集成

本指南帮助开发者快速集成和测试 ChromaDB 向量数据库。

---

## 📦 环境准备

### 1. 安装依赖

```bash
# 安装 ChromaDB (兼容版本)
pip install 'chromadb<0.4'

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 2. 启动 ChromaDB 服务

#### 方案 A: Docker 容器 (推荐生产环境)
```bash
docker-compose up -d chroma

# 检查服务状态
docker ps | grep chroma
docker logs mt5-crs-chroma
```

#### 方案 B: 本地开发 (无需 Docker)
```bash
# 直接使用 Python 客户端 (EphemeralClient)
python3 scripts/data/vector_client.py
```

---

## 🔧 使用示例

### 初始化客户端

```python
from scripts.data.vector_client import VectorClient

# 创建单例客户端
client = VectorClient(
    persist_dir="./data/chroma",
    use_persistent=True
)
```

### 创建集合 (Collection)

```python
# 自动创建或获取现有集合
collection = client.ensure_collection(
    name="news_embeddings",
    metadata={"task": "098", "model": "jina"}
)
```

### 写入向量

```python
# 准备数据
vectors = [
    [0.1, 0.2, 0.3, ..., 0.384],  # 384 维向量
    [0.15, 0.25, 0.35, ..., 0.385],
]

metadatas = [
    {"source": "sina", "date": "2026-01-13"},
    {"source": "tencent", "date": "2026-01-13"}
]

documents = [
    "新闻标题和内容第一篇",
    "新闻标题和内容第二篇"
]

# 批量写入
client.insert_vectors(
    collection_name="news_embeddings",
    vectors=vectors,
    metadatas=metadatas,
    documents=documents
)
```

### 查询相似向量

```python
# 查询向量
query_vector = [[0.1, 0.2, 0.3, ..., 0.384]]

results = client.query_vectors(
    collection_name="news_embeddings",
    query_embeddings=query_vector,
    n_results=5,  # 返回前 5 个最相似的
    where={"source": "sina"}  # 可选: 元数据过滤
)

# 解析结果
for i, (doc_id, distance, document) in enumerate(
    zip(results['ids'][0], results['distances'][0], results['documents'][0])
):
    print(f"{i+1}. [距离: {distance:.4f}] {document}")
```

---

## 🧪 运行测试

### 运行完整 TDD 审计

```bash
python3 scripts/audit_task_097.py
```

预期输出:
```
🔧 TASK #097 AUDIT - Vector Database Infrastructure
======================================================================
✅ PASS | ChromaDB Installation: v0.3.29
✅ PASS | VectorClient Initialization: Singleton created
✅ PASS | Collection Creation: Collection 'test_audit_097' created
✅ PASS | Vector Write: 5 vectors inserted
✅ PASS | KNN Search: Min distance: 0.000000 (threshold: 0.1)
✅ PASS | Data Persistence: 5 files in data/chroma
✅ PASS | List Collections: Found 1 collections

📊 SUMMARY: 7/7 tests passed
```

### 运行向量写入测试

```bash
python3 scripts/data/vector_client.py --test-write --task-id 097
```

### 列出所有集合

```bash
python3 scripts/data/vector_client.py --list-collections
```

---

## 📊 数据结构

### 向量维度

| 模型 | 维度 | 备注 |
|-----|------|------|
| JINA Embeddings | 384 | 多语言支持 |
| BGE Embeddings | 768 | 高性能 |
| OpenAI Ada | 1536 | 云 API |

### 集合结构

```
Collection: news_embeddings
├── 文档 1
│   ├── id: "abc123..."
│   ├── embedding: [0.1, 0.2, ..., 0.384]
│   ├── metadata: {"source": "sina", "date": "2026-01-13"}
│   └── text: "新闻内容..."
├── 文档 2
│   ...
```

### 查询结果格式

```python
{
    'ids': [
        ['doc1_id', 'doc2_id', 'doc3_id', ...]
    ],
    'distances': [
        [0.001, 0.015, 0.023, ...]  # L2 距离 (越小越相似)
    ],
    'documents': [
        ['文档1内容', '文档2内容', '文档3内容', ...]
    ]
}
```

---

## 🐛 常见问题

### Q1: SQLite 版本太旧？
**问题**: `RuntimeError: Your system has an unsupported version of sqlite3`

**解决方案**:
```bash
# 使用兼容版本
pip install 'chromadb<0.4'
```

### Q2: Docker 容器无法启动？
**问题**: `Cannot connect to the Docker daemon`

**解决方案**:
```bash
# 检查 Docker 状态
docker ps

# 如果不运行，使用本地开发模式
python3 scripts/data/vector_client.py
```

### Q3: 集合创建失败？
**问题**: `RuntimeError: collection already exists`

**解决方案**:
```python
# 使用 ensure_collection 自动处理
# (它会自动返回现有集合)
collection = client.ensure_collection("my_collection")
```

### Q4: 查询返回空结果？
**问题**: 查询返回 0 条结果

**诊断**:
```python
# 检查集合中的文档数量
collection.count()  # 应该 > 0

# 检查集合是否存在
client.list_collections()

# 检查向量维度是否匹配
len(query_vector[0]) == len(vectors[0])  # 应该相等
```

---

## 📁 文件组织

```
mt5-crs/
├── scripts/
│   ├── data/
│   │   └── vector_client.py          # 核心客户端
│   └── audit_task_097.py             # TDD 测试
├── data/
│   └── chroma/                       # ChromaDB 持久化存储
├── docker-compose.yml                # 容器编排
└── docs/archive/tasks/TASK_097/
    ├── COMPLETION_REPORT.md          # 完成报告
    ├── QUICK_START.md                # 本文件
    ├── VERIFY_LOG.log                # 执行日志
    └── SYNC_GUIDE.md                 # 部署清单
```

---

## 🔗 与后续任务的集成

### TASK #098 (舆情因子挖掘)

**如何使用本任务的输出**:

```python
from scripts.data.vector_client import VectorClient

# 初始化客户端
client = VectorClient()

# 获取或创建舆情集合
sentiment_collection = client.ensure_collection("sentiment_v1")

# 在 #098 中，使用相同接口存储 Embedding
client.insert_vectors(
    collection_name="sentiment_v1",
    vectors=embeddings,  # 从 Embedding 模型生成
    metadatas=metadata,
    documents=news_texts
)

# 查询类似舆情
results = client.query_vectors(
    collection_name="sentiment_v1",
    query_embeddings=query_embedding,
    n_results=10
)
```

---

## 📞 技术支持

如有问题，请参考:
- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [DuckDB 持久化](https://docs.trychroma.com/usage-guide)
- 项目 COMPLETION_REPORT.md (本次任务的详细技术细节)

---

**最后更新**: 2026-01-13
**版本**: v1.0
**维护者**: AI Infrastructure Engineer (Claude Code)

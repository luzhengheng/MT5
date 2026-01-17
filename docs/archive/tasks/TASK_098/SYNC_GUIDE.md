# 🔄 TASK #098 部署同步清单

## 舆情因子挖掘 - 环境与依赖配置

---

## 1. 环境变量 (ENV)

### 必需环境变量

| 变量名 | 值 | 说明 | 优先级 |
|--------|-----|------|--------|
| `EODHD_API_KEY` | `xxxxxxx` | EODHD 新闻 API 密钥 | **必需** |
| `PYTHONPATH` | `./scripts` | Python 模块路径 | 可选 |

### 可选环境变量

| 变量名 | 默认值 | 说明 |
|--------|-------|------|
| `DEVICE` | `cpu` | 计算设备 (cpu/cuda) |
| `BATCH_SIZE` | `50` | 批处理大小 |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-Transformers 模型 |
| `SENTIMENT_MODEL` | `ProsusAI/finbert` | FinBERT 模型 |

### .env 文件配置 (示例)

```bash
# .env
EODHD_API_KEY=your_api_key_here
PYTHONPATH=./scripts
DEVICE=cpu
CHROMA_PERSIST_DIR=./data/chroma
```

---

## 2. 依赖包管理

### 新增 Python 包

添加到 `requirements.txt`:

```
transformers==4.57.3           # NLP 库
torch==2.8.0                   # PyTorch (CPU 版本)
sentence-transformers==5.1.2   # 向量生成
chromadb<0.4                   # 向量数据库 (TASK #097 已有)
tqdm>=4.65.0                   # 进度条
requests>=2.31.0               # HTTP 客户端
```

### 完整依赖安装

```bash
# 方式 1: 直接安装
pip install transformers==4.57.3
pip install torch==2.8.0
pip install sentence-transformers==5.1.2
pip install 'chromadb<0.4'

# 方式 2: 使用 requirements.txt
echo "transformers==4.57.3" >> requirements.txt
echo "torch==2.8.0" >> requirements.txt
echo "sentence-transformers==5.1.2" >> requirements.txt
pip install -r requirements.txt
```

### 版本兼容性表

| 包名 | 版本 | Python | PyTorch | 备注 |
|-----|------|--------|---------|------|
| transformers | 4.57.3 | >= 3.8 | >= 1.11 | 推荐 |
| torch | 2.8.0 | >= 3.8 | N/A | CPU 版本 |
| sentence-transformers | 5.1.2 | >= 3.7 | >= 1.9 | 推荐 |
| chromadb | 0.3.29 | >= 3.8 | N/A | TASK #097 已有 |

### 已验证的兼容组合

```
✅ Python 3.9 + PyTorch 2.8.0 (CPU) + Transformers 4.57.3
✅ Python 3.9 + Sentence-Transformers 5.1.2 + ChromaDB 0.3.29
✅ Hub 节点 (8GB RAM) 运行无 OOM 错误
```

---

## 3. Docker 服务配置

### docker-compose.yml (TASK #097 已配置)

ChromaDB 服务已在 TASK #097 中配置，本任务无需修改。

验证配置:

```yaml
# 现有配置验证
chroma:
  image: chromadb/chroma:latest
  container_name: mt5-crs-chroma
  restart: unless-stopped
  ports:
    - "8000:8000"
  volumes:
    - ./data/chroma:/chroma/chroma
  environment:
    - IS_PERSISTENT=TRUE
  networks:
    - mt5-network
```

### 容器启动验证

```bash
# 确保 ChromaDB 运行
docker-compose up -d chroma

# 验证服务状态
docker ps | grep chroma

# 检查服务健康
curl http://localhost:8000/api/v1/heartbeat

# 查看日志
docker logs -f mt5-crs-chroma
```

---

## 4. 目录结构创建

### 新增目录

```bash
# 创建任务档案目录
mkdir -p docs/archive/tasks/TASK_098

# 验证目录创建
ls -la docs/archive/tasks/TASK_098/
```

### 文件权限

```bash
# 确保目录可写
chmod 755 docs/archive/tasks/TASK_098/
chmod 755 data/chroma/
```

---

## 5. 文件部署清单

### 新增文件

| 文件路径 | 大小 | 说明 | 部署步骤 |
|--------|------|------|---------|
| `scripts/data/news_sentiment_loader.py` | ~12KB | 核心舆情管道 | 复制 |
| `scripts/audit_task_098.py` | ~8KB | TDD 测试脚本 | 复制 |
| `docs/archive/tasks/TASK_098/COMPLETION_REPORT.md` | ~10KB | 完成报告 | 生成 |
| `docs/archive/tasks/TASK_098/QUICK_START.md` | ~7KB | 快速启动 | 生成 |
| `docs/archive/tasks/TASK_098/SYNC_GUIDE.md` | ~8KB | 部署清单 | 生成 (本文件) |

### 更新文件

| 文件 | 变更 | 影响范围 |
|-----|------|--------|
| `requirements.txt` | 添加 transformers/torch/sentence-transformers | Python 环境 |
| `VERIFY_LOG.log` | 追加执行日志 | 审计追溯 |

---

## 6. 数据存储

### 数据位置

```
data/chroma/
├── index/
├── data.parquet          # 向量和元数据
├── metadata.parquet      # 集合元数据
└── .gitignore            # 不提交大文件
```

### 数据量预估

| 项目 | 值 |
|-----|-----|
| 新闻条数 | 50 |
| 向量维度 | 384 |
| 单条大小 | ~2 KB |
| 总存储 | ~100 KB |

### 持久化验证

```bash
# 检查持久化数据
ls -lh data/chroma/

# 检查数据大小
du -sh data/chroma/

# 验证 ChromaDB 集合
python3 << 'EOF'
from scripts.data.vector_client import VectorClient
client = VectorClient()
print(f"集合: {client.list_collections()}")
EOF
```

---

## 7. 部署步骤 (完整流程)

### Step 1: 环境准备

```bash
cd /opt/mt5-crs

# 设置 EODHD API 密钥
export EODHD_API_KEY="your_api_key_here"

# 验证环境变量
echo $EODHD_API_KEY
```

### Step 2: 安装依赖

```bash
# 更新 requirements.txt
cat >> requirements.txt << 'EOF'
transformers==4.57.3
torch==2.8.0
sentence-transformers==5.1.2
EOF

# 安装所有依赖
pip install -r requirements.txt

# 验证安装
python3 -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
```

### Step 3: 创建目录

```bash
mkdir -p docs/archive/tasks/TASK_098
chmod 755 docs/archive/tasks/TASK_098/
```

### Step 4: 部署代码

```bash
# 核心代码已就位 (scripts/data/news_sentiment_loader.py)
# 审计脚本已就位 (scripts/audit_task_098.py)

# 验证文件存在
ls -la scripts/data/news_sentiment_loader.py
ls -la scripts/audit_task_098.py
```

### Step 5: 验证 ChromaDB

```bash
# 确保 ChromaDB 运行
docker-compose up -d chroma

# 等待 10 秒
sleep 10

# 测试连接
curl -s http://localhost:8000/api/v1/heartbeat | head -20
```

### Step 6: 运行 TDD 审计

```bash
# 执行审计测试
python3 scripts/audit_task_098.py

# 预期输出:
# ✅ PASS | Transformers Installation: v4.57.3
# ✅ PASS | PyTorch CPU Mode: v2.8.0+cpu on cpu
# ✅ PASS | FinBERT Model Loading: Loaded and tested
# ✅ PASS | Sentence-Transformers: Generated 2 embeddings
# ✅ PASS | VectorClient Integration: Collection created
# ✅ PASS | Sentiment + Vector Storage: Stored 2 items
# ✅ PASS | Memory Efficiency: Memory usage: 733.1 MB
# 📊 SUMMARY: 7/7 tests passed
```

### Step 7: 运行完整管道

```bash
# 执行舆情分析管道
python3 scripts/data/news_sentiment_loader.py \
    --symbol AAPL \
    --days 7 \
    --task-id 098

# 预期输出:
# 📰 Fetching news for AAPL from 2026-01-06 to 2026-01-13
# ✅ Fetched 50 news items
# 📚 Processing 50 news items...
# ✅ Processed 50 news items
# 🔍 Found 3 similar news items for query: 'AAPL earnings'
```

### Step 8: 物理验尸

```bash
# 验证情感分析结果
grep "SENTIMENT" VERIFY_LOG.log | head -5

# 验证向量存储
grep "Vector Inserted" VERIFY_LOG.log | wc -l  # 应该 >= 50

# 验证语义搜索
grep "Found.*similar" VERIFY_LOG.log
```

---

## 8. 回滚计划

### 回滚步骤

```bash
# 1. 停止应用 (如有服务)
# (本任务为批处理，无常驻服务)

# 2. 清理新增数据 (可选)
rm -rf docs/archive/tasks/TASK_098/

# 3. 回复依赖配置
git checkout requirements.txt

# 4. 卸载新增包
pip uninstall -y transformers torch sentence-transformers

# 5. 验证清理完成
pip list | grep -E "transformers|sentence-transformers"  # 应该为空
```

### 回滚后验证

```bash
# 验证包已卸载
python3 -c "import transformers" 2>&1 | grep -i "error"  # 应该有 ImportError

# 验证文件已删除
ls docs/archive/tasks/TASK_098/ 2>&1 | grep -i "no such"  # 应该有 No such file
```

---

## 9. 监控与维护

### 常规检查

```bash
# 检查 ChromaDB 服务
docker ps | grep chroma

# 检查 VERIFY_LOG.log 最新行
tail -20 VERIFY_LOG.log

# 检查磁盘使用
du -sh data/chroma/

# 验证集合数据量
python3 << 'EOF'
from scripts.data.vector_client import VectorClient
client = VectorClient()
for collection in client.list_collections():
    print(f"{collection}: {client.query_vectors(collection, [[0.1]*384], n_results=1000)}")
EOF
```

### 日志监控

```bash
# 实时监控 VERIFY_LOG.log
tail -f VERIFY_LOG.log

# 筛选错误
grep -i "error\|exception" VERIFY_LOG.log

# 计数统计
echo "成功消息数: $(grep -c 'SUCCESS' VERIFY_LOG.log)"
echo "错误消息数: $(grep -c 'ERROR' VERIFY_LOG.log)"
```

### 性能指标

| 指标 | 阈值 | 告警 |
|-----|------|------|
| 处理延迟 | < 1 分钟/50 条 | > 2 分钟 ⚠️ |
| 内存占用 | < 1.5 GB | > 2 GB ⚠️ |
| 存储大小 | < 500 MB | > 1 GB ⚠️ |
| 查询延迟 | < 500 ms | > 1 s ⚠️ |

---

## 10. 故障排查

### 问题 1: EODHD API 连接失败

```bash
# 诊断
python3 << 'EOF'
import os
import requests

api_key = os.getenv('EODHD_API_KEY')
if not api_key:
    print("❌ 错误: EODHD_API_KEY 未设置")
else:
    url = f"https://eodhd.com/api/news?api_token={api_key}&s=AAPL&limit=1"
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:200]}")
EOF

# 解决方案
export EODHD_API_KEY="your_correct_api_key"
```

### 问题 2: 模型加载失败

```bash
# 诊断
python3 << 'EOF'
from transformers import pipeline
try:
    model = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=-1)
    print("✅ FinBERT 加载成功")
except Exception as e:
    print(f"❌ 错误: {e}")
EOF

# 解决方案
pip install --upgrade transformers
# 或清除缓存
rm -rf ~/.cache/huggingface/
```

### 问题 3: ChromaDB 连接失败

```bash
# 检查服务
docker ps | grep chroma

# 如果未运行
docker-compose up -d chroma

# 测试连接
curl http://localhost:8000/api/v1/heartbeat

# 查看日志
docker logs mt5-crs-chroma
```

### 问题 4: OOM 内存不足

```bash
# 检查内存使用
free -h

# 减少批处理大小
python3 scripts/data/news_sentiment_loader.py --batch-size 10

# 或清除缓存
python3 -c "import torch; torch.cuda.empty_cache()"
```

### 问题 5: 权限错误

```bash
# 修复目录权限
chmod 755 docs/archive/tasks/TASK_098/
chmod 755 data/chroma/

# 修复文件权限
chmod 644 docs/archive/tasks/TASK_098/*
```

---

## 11. 下游依赖

### 依赖本任务的模块

- **特征工程模块**: 使用情感得分作为技术指标
- **交易信号生成**: 结合情感趋势和价格行为生成交易信号

### 影响范围

| 组件 | 影响 | 说明 |
|-----|------|------|
| 舆情管道 | 强依赖 | 本任务为舆情信号源 |
| 特征工程 | 强依赖 | 使用情感得分作为因子 |
| 交易引擎 | 可选 | 可选集成到策略中 |

---

## 12. 文档引用

| 文档 | 路径 | 用途 |
|-----|------|------|
| 完成报告 | `COMPLETION_REPORT.md` | 技术实现细节 |
| 快速启动 | `QUICK_START.md` | 开发者使用指南 |
| 本清单 | `SYNC_GUIDE.md` | 部署与配置 |
| 执行日志 | `VERIFY_LOG.log` | 审计追溯 |
| TASK #097 | `../TASK_097/` | 向量数据库基础设施 |

---

**部署负责人**: DevOps / Platform Engineer
**最后更新**: 2026-01-13
**版本**: v1.0 (Release)


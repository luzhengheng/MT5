# 🔄 TASK #097 部署同步清单

## 环境变量、依赖包和配置更新

---

## 1. 环境变量 (ENV)

### 新增环境变量

| 变量名 | 值 | 说明 | 优先级 |
|--------|-----|------|--------|
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB 持久化目录 | 可选 |
| `CHROMA_DB_IMPL` | `duckdb+parquet` | 后端实现 | 可选 |
| `CHROMA_ANONYMIZED_TELEMETRY` | `false` | 禁用遥测 | 推荐 |

### 更新现有环境变量

无需修改现有环境变量。

### .env 文件更新 (可选)

```bash
# .env
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_DB_IMPL=duckdb+parquet
CHROMA_ANONYMIZED_TELEMETRY=false
```

---

## 2. 依赖包管理

### 新增 Python 包

添加到 `requirements.txt`:

```
chromadb<0.4        # 向量数据库 (兼容版本)
```

### 完整依赖安装命令

```bash
# 更新 requirements.txt
echo "chromadb<0.4" >> requirements.txt

# 安装所有依赖
pip install -r requirements.txt
```

### 版本兼容性表

| 包名 | 版本 | Python | SQLite | 备注 |
|-----|-----|--------|--------|------|
| chromadb | 0.3.29 | >= 3.8 | >= 3.26 | 兼容旧系统 |
| chromadb | 1.4.0+ | >= 3.8 | >= 3.35 | 需要新 SQLite |

### 已验证的兼容组合

```
✅ Python 3.9 + ChromaDB 0.3.29 + SQLite 3.26
✅ Python 3.9 + PyArrow 12.0.0 + NumPy 1.24.0
```

---

## 3. Docker 服务配置

### docker-compose.yml 更新

#### 新增服务: ChromaDB

```yaml
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
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
    interval: 10s
    timeout: 5s
    retries: 5
```

#### 网络配置

已有的 `mt5-network` 网络无需修改。

### 容器启动命令

```bash
# 启动 ChromaDB 服务
docker-compose up -d chroma

# 验证服务状态
docker ps | grep chroma

# 查看日志
docker logs mt5-crs-chroma

# 停止服务
docker-compose down chroma
```

---

## 4. 目录结构创建

### 新增目录

```bash
# 创建 ChromaDB 持久化目录
mkdir -p data/chroma

# 创建任务档案目录
mkdir -p docs/archive/tasks/TASK_097
```

### 目录权限 (Docker)

```bash
# 确保 Docker 容器可写
chmod 755 data/chroma
```

---

## 5. 文件部署清单

### 新增文件

| 文件路径 | 大小 | 说明 | 部署步骤 |
|--------|------|------|--------|
| `scripts/data/vector_client.py` | ~8KB | 核心客户端 | 复制 |
| `scripts/audit_task_097.py` | ~7KB | TDD 测试 | 复制 |
| `docker-compose.yml` | 更新 | 添加 ChromaDB 服务 | 编辑 |

### 更新文件

| 文件 | 变更 | 影响范围 |
|-----|------|--------|
| `docker-compose.yml` | 添加 `chroma` 服务块 | 容器编排 |
| `requirements.txt` | 添加 `chromadb<0.4` | Python 环境 |

---

## 6. 数据迁移 (如适用)

### 无需数据迁移

本任务是新服务部署，无历史数据需迁移。

### 持久化存储位置

```
data/chroma/
├── index/
├── data.parquet
└── metadata.parquet
```

---

## 7. 部署步骤 (完整流程)

### Step 1: 更新依赖

```bash
cd /opt/mt5-crs

# 更新 Python 包
pip install 'chromadb<0.4'

# 或使用 requirements.txt
echo "chromadb<0.4" >> requirements.txt
pip install -r requirements.txt
```

### Step 2: 更新配置文件

```bash
# 编辑 docker-compose.yml
# (添加 ChromaDB 服务块，参见第 3 章)

# 验证 YAML 语法
docker-compose config > /dev/null && echo "✅ YAML 正确"
```

### Step 3: 创建目录

```bash
mkdir -p data/chroma
mkdir -p docs/archive/tasks/TASK_097
```

### Step 4: 部署代码

```bash
# 复制核心文件
cp scripts/data/vector_client.py /opt/mt5-crs/scripts/data/
cp scripts/audit_task_097.py /opt/mt5-crs/scripts/

# 验证文件存在
ls -la scripts/data/vector_client.py
ls -la scripts/audit_task_097.py
```

### Step 5: 启动服务

```bash
# 启动 ChromaDB 容器
docker-compose up -d chroma

# 等待 30 秒
sleep 30

# 验证服务健康
curl -s http://localhost:8000/api/v1/heartbeat | jq .
```

### Step 6: 运行测试

```bash
# 运行 TDD 审计
python3 scripts/audit_task_097.py

# 预期: 7/7 测试通过
```

### Step 7: 验证部署

```bash
# 验证持久化存储
ls -la data/chroma/

# 验证集合创建
python3 scripts/data/vector_client.py --list-collections
```

---

## 8. 回滚计划 (如需要)

### 回滚步骤

```bash
# 1. 停止 ChromaDB 容器
docker-compose down chroma

# 2. 移除持久化数据 (可选)
rm -rf data/chroma/

# 3. 回复 requirements.txt
git checkout requirements.txt

# 4. 卸载 chromadb
pip uninstall chromadb -y

# 5. 回复 docker-compose.yml
git checkout docker-compose.yml
```

### 回滚后验证

```bash
# 验证服务已停止
docker ps | grep chroma  # 应该为空

# 验证包已卸载
pip list | grep chromadb  # 应该为空
```

---

## 9. 监控与维护

### 常规检查

```bash
# 检查 ChromaDB 服务状态
docker ps | grep chroma

# 检查持久化数据大小
du -sh data/chroma/

# 检查集合数量
python3 -c "from scripts.data.vector_client import VectorClient; print(len(VectorClient().list_collections()))"
```

### 日志监控

```bash
# 查看 ChromaDB 日志
docker logs -f mt5-crs-chroma

# 查看应用日志
tail -f VERIFY_LOG.log
```

### 性能指标

| 指标 | 阈值 | 告警 |
|-----|------|------|
| 存储大小 | > 1GB | ⚠️ |
| 查询延迟 | > 100ms | ⚠️ |
| 集合数量 | > 100 | ⚠️ |

---

## 10. 故障排查

### 问题 1: ChromaDB 容器启动失败

```bash
# 检查日志
docker logs mt5-crs-chroma

# 可能原因: SQLite 版本不兼容
# 解决: 使用本地开发模式或升级 SQLite
```

### 问题 2: 连接错误

```bash
# 测试连接
curl http://localhost:8000/api/v1/heartbeat

# 如果无响应，检查防火墙或端口占用
netstat -tlnp | grep 8000
```

### 问题 3: 持久化数据丢失

```bash
# 检查卷挂载
docker inspect mt5-crs-chroma | grep -A 5 Mounts

# 验证数据目录
ls -la data/chroma/
```

---

## 11. 下游依赖

### 依赖本任务的其他模块

- **TASK #098**: 舆情因子挖掘
  - 需要: `VectorClient` API
  - 需要: ChromaDB 运行中

### 影响范围

| 组件 | 影响 | 说明 |
|-----|------|------|
| 舆情管道 | 强依赖 | 向量存储必须可用 |
| 特征工程 | 无影响 | 本任务不修改已有功能 |
| 交易引擎 | 无影响 | 本任务为辅助功能 |

---

## 12. 文档引用

| 文档 | 路径 | 用途 |
|-----|------|------|
| 完成报告 | `COMPLETION_REPORT.md` | 技术实现细节 |
| 快速启动 | `QUICK_START.md` | 开发者指南 |
| 本清单 | `SYNC_GUIDE.md` | 部署检查表 |
| 审计日志 | `VERIFY_LOG.log` | 执行证据 |

---

**部署负责人**: DevOps / Platform Engineer
**最后更新**: 2026-01-13
**版本**: v1.0 (Release)


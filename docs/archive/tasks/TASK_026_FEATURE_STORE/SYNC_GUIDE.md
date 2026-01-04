# TASK #026: 多节点同步部署指南 (Multi-Node Deployment Guide)

**版本**: 1.0  
**日期**: 2026-01-05  
**协议**: v4.1 (Iterative Perfection)  
**状态**: ✅ READY FOR DEPLOYMENT

---

## 变更清单 (Change List)

### 新增文件 (New Files)

| 文件路径 | 行数 | 描述 | 优先级 |
|:---|:---|:---|:---|
| `src/feature_store/features/__init__.py` | 2 | 包初始化文件 | LOW |
| `src/feature_store/features/definitions.py` | 66 | Feast 特征定义 (Entity + FeatureViews) | **CRITICAL** |
| `src/gateway/ingest_stream.py` | 90 | ZMQ → Feast 实时摄入服务 | **CRITICAL** |
| `scripts/test_feature_retrieval.py` | 110 | 特征读取测试与延迟基准测试 | HIGH |
| `docs/archive/tasks/TASK_026_FEATURE_STORE/QUICK_START.md` | 150 | 快速启动指南 | HIGH |
| `docs/archive/tasks/TASK_026_FEATURE_STORE/SYNC_GUIDE.md` | 本文档 | 部署同步指南 | HIGH |
| `docs/archive/tasks/TASK_026_FEATURE_STORE/VERIFY_LOG.log` | 30 | 测试验证日志 | MEDIUM |
| `src/feature_store/registry.db` | 二进制 | Feast Registry (SQLite) | MEDIUM |

### 修改文件 (Modified Files)

| 文件路径 | 改动 | 行数 |
|:---|:---|:---|
| `src/feature_store/feature_store.yaml` | Redis/PostgreSQL 配置更新 | ~18 |
| `docs/task.md` | 添加 TASK #026 完成记录 | +5 |

### 删除文件 (Deleted Files)
- `docs/# [System Instruction MT5-CRS Development Protocol v4.0].md` (升级至 v4.1)

**总计**: 8 个新增 + 2 个修改 + 1 个删除 = **11 个涉及文件**

---

## 部署架构 (Deployment Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                         HUB (中枢)                               │
│  - Git Repository (主仓库)                                       │
│  - Documentation (文档中心)                                      │
│  - Task Tracking (任务管理)                                      │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ↓              ↓              ↓
      ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
      │  INF (脑)    │  │  GTW (手脚) │  │  GPU (算力)  │
      │              │  │             │  │              │
      │ • Python     │  │ • MT5 EA    │  │ • 模型训练   │
      │ • Redis      │  │ • ZMQ PUB   │  │ • 批量推理   │
      │ • PostgreSQL │  │ • Gateway   │  │              │
      │ • Feast      │  │             │  │              │
      └──────────────┘  └─────────────┘  └──────────────┘
           ↑                   ↑                 ↑
           │                   │                 │
         Feast             ZMQ 5556          离线训练
      Feature Store       行情数据流        数据同步
```

---

## 分阶段部署步骤 (Deployment Phases)

### Phase 1: HUB (中枢) - 代码同步

**目标**: 将 TASK #026 变更推送到主仓库

```bash
# 1. 检查当前分支
git branch -vv

# 2. 拉取最新代码
git pull origin main

# 3. 检查提交记录
git log --oneline -5
# 应包含: feat(infra): upgrade protocol to v4.1 and implement Feast...

# 4. 标记版本 (可选)
git tag -a v1.6.0-feast -m "TASK #026: Feast Feature Store"
git push origin v1.6.0-feast
```

**验证**:
```bash
git log --grep="TASK #026" --oneline
# 应显示: feat(infra): upgrade protocol to v4.1...
```

---

### Phase 2: INF (脑) - Python 服务部署

**角色**: 运行 Feature Store 和摄入服务

#### Step 2.1: 依赖安装
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装 Feast 及依赖
pip install "feast[redis,postgres]" pandas pyarrow

# 验证安装
feast version
# 应显示: feast, version 0.x.x
```

#### Step 2.2: 服务验证
```bash
# 1. Redis
systemctl status redis
redis-cli ping  # 应返回 PONG

# 2. PostgreSQL
psql -h localhost -U trader -d mt5_crs -c "SELECT version()"

# 3. 检查环境变量
env | grep -E "(REDIS|POSTGRES)"
```

#### Step 2.3: Feast 注册特征
```bash
cd /opt/mt5-crs/src/feature_store
feast -c . apply 2>&1 | grep -E "(Deploying|error)"

# 验证注册成功
ls -lh registry.db  # 应显示 ~3.5KB
```

#### Step 2.4: 启动摄入服务
```bash
# 方式 A: Systemd (推荐)
cat > /etc/systemd/system/mt5-crs-feast-ingest.service << 'SYSTEMD'
[Unit]
Description=MT5-CRS Feast Feature Ingestion Service
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mt5-crs
ExecStart=/opt/mt5-crs/venv/bin/python3 -m src.gateway.ingest_stream
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable mt5-crs-feast-ingest
sudo systemctl start mt5-crs-feast-ingest

# 方式 B: Screen (开发环境)
screen -S feast-ingest
python3 -m src.gateway.ingest_stream
# Ctrl-A + D 分离会话
```

**验证摄入服务**:
```bash
# 查看日志
journalctl -u mt5-crs-feast-ingest -f
# 预期: [INFO] Pushed 10 features | Latest: EURUSD=1.0543

# 检查 Redis 数据
redis-cli KEYS "feast:*" | wc -l
# 应 > 0
```

---

### Phase 3: GTW (手脚) - Windows Gateway

**角色**: ZMQ 数据发布者 (无需修改)

**验证**:
```bash
# 检查 ZMQ PUB 端口
netstat -an | findstr 5556
# 应显示: TCP 0.0.0.0:5556 LISTENING

# 检查数据流 (Linux 测试端)
python3 << 'EOF'
import zmq
context = zmq.Context()
sub = context.socket(zmq.SUB)
sub.connect("tcp://172.19.141.255:5556")  # GTW IP
sub.subscribe(b"")
print("Listening on ZMQ PUB...")
topic, msg = sub.recv_multipart()
print(f"Received: {topic.decode()} -> {msg.decode()}")

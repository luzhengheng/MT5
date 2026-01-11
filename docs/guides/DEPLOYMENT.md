# MT5-CRS 驱动管家系统 - 部署文档

**版本**：v4.0
**更新时间**：2025-12-19

---

## 📋 目录

1. [系统架构](#系统架构)
2. [环境要求](#环境要求)
3. [快速开始](#快速开始)
4. [详细部署步骤](#详细部署步骤)
5. [服务管理](#服务管理)
6. [监控与调试](#监控与调试)
7. [常见问题](#常见问题)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     EODHD News API                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  NewsFetcher (定时任务)       │
        │  python news_service/         │
        │  news_fetcher.py              │
        └──────────────┬────────────────┘
                       │ produce
                       ▼
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ Redis Stream: news_raw        ┃
        ┗━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┛
                       │ consume
                       ▼
        ┌──────────────────────────────┐
        │ NewsFilterConsumer            │
        │ python sentiment_service/     │
        │ news_filter_consumer.py       │
        │ ├─ FinBERT 情感分析           │
        │ └─ 阈值过滤                   │
        └──────────────┬────────────────┘
                       │ produce
                       ▼
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ Redis Stream: news_filtered   ┃
        ┗━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┛
                       │ consume
                       ▼
        ┌──────────────────────────────┐
        │ SignalGeneratorConsumer       │
        │ python signal_service/        │
        │ signal_generator_consumer.py  │
        │ ├─ 风险管理                   │
        │ ├─ 手数计算                   │
        │ └─ 信号生成                   │
        └──────────────┬────────────────┘
                       │ produce
                       ▼
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ Redis Stream: signals         ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 环境要求

### 硬件要求

- **CPU**: 4核心以上推荐
- **内存**: 8GB以上（FinBERT模型需要约1GB）
- **磁盘**: 20GB可用空间

### 软件要求

- **操作系统**: Linux (CentOS 7/8, Ubuntu 18.04+)
- **Python**: 3.6+
- **Redis**: 6.0+
- **Docker**: 20.10+ (可选，用于容器化部署)

### Python 依赖

```
redis==4.3.6
transformers==4.18.0
tokenizers==0.12.1
torch==1.4.0+cpu
eodhd==1.1.0
requests==2.31.0
prometheus-client==0.17.1
APScheduler==3.10.4
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-org/M-t-5-CRS.git
cd M-t-5-CRS
```

### 2. 安装依赖

```bash
pip3 install -r src/requirements.txt
```

### 3. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << EOF
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# EODHD API 配置
EODHD_API_KEY=your_api_key_here

# Prometheus 配置
PROMETHEUS_PORT=9090
EOF
```

### 4. 启动 Redis

```bash
docker-compose up -d redis
# 或者
redis-server configs/redis/redis.conf
```

### 5. 启动服务（按顺序）

```bash
# 终端1：新闻过滤消费者
cd python
python3 -m sentiment_service.news_filter_consumer

# 终端2：信号生成消费者
python3 -m signal_service.signal_generator_consumer

# 终端3：新闻获取器（定时任务）
python3 -m news_service.news_fetcher
```

### 6. 运行端到端测试

```bash
python3 test_end_to_end.py
```

---

## 详细部署步骤

### 步骤1：准备 Redis

#### 使用 Docker

```bash
docker run -d \
  --name mt5-redis \
  -p 6379:6379 \
  -v $(pwd)/data/redis:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

#### 使用 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: mt5-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
      - ./configs/redis/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
```

```bash
docker-compose up -d redis
```

#### 验证 Redis

```bash
redis-cli ping
# 应该返回: PONG
```

---

### 步骤2：配置 FinBERT 模型

首次运行会自动下载 FinBERT 模型（约500MB），也可以预先下载：

```python
# 预下载脚本
python3 << EOF
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "ProsusAI/finbert"
cache_dir = "~/.cache/finbert"

print("下载 FinBERT 模型...")
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir)
print("✓ 模型下载完成")
EOF
```

---

### 步骤3：配置服务参数

#### NewsFilterConsumer 配置

编辑 `src/sentiment_service/news_filter_consumer.py`：

```python
consumer = NewsFilterConsumer(
    sentiment_threshold=0.75,    # 情感强度阈值
    min_confidence=0.60,         # 最小置信度
    finbert_model='finbert',     # 模型名称
)
```

#### SignalGeneratorConsumer 配置

编辑 `src/signal_service/signal_generator_consumer.py`：

```python
from signal_service.risk_manager import RiskConfig

risk_config = RiskConfig(
    base_risk_percent=1.0,          # 每笔风险 1%
    max_lot_size=1.0,               # 最大手数
    max_signals_per_day=20,         # 每日最大信号数
    max_signals_per_ticker=3,       # 单ticker每日最大信号数
    risk_reward_ratio=3.0,          # 风险回报比 1:3
)

consumer = SignalGeneratorConsumer(
    account_balance=10000.0,        # 账户余额
    signal_expiry_hours=4,          # 信号有效期
    risk_config=risk_config,
)
```

---

### 步骤4：启动服务

#### 方式1：使用 systemd（推荐生产环境）

创建服务文件：

```bash
# /etc/systemd/system/mt5-news-filter.service
[Unit]
Description=MT5 News Filter Consumer
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mt5-crs/python
ExecStart=/usr/bin/python3 -m sentiment_service.news_filter_consumer
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/mt5-signal-gen.service
[Unit]
Description=MT5 Signal Generator Consumer
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mt5-crs/python
ExecStart=/usr/bin/python3 -m signal_service.signal_generator_consumer
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
systemctl daemon-reload
systemctl enable mt5-news-filter
systemctl enable mt5-signal-gen
systemctl start mt5-news-filter
systemctl start mt5-signal-gen
```

#### 方式2：使用 screen/tmux（开发环境）

```bash
# 启动 screen
screen -S mt5-services

# 创建窗口1：NewsFilterConsumer
cd /root/M\ t\ 5-CRS/python
python3 -m sentiment_service.news_filter_consumer

# Ctrl+A, C 创建新窗口
# 窗口2：SignalGeneratorConsumer
python3 -m signal_service.signal_generator_consumer

# Ctrl+A, D 分离会话
```

#### 方式3：使用 supervisor

```ini
# /etc/supervisor/conf.d/mt5-services.conf
[program:mt5-news-filter]
command=/usr/bin/python3 -m sentiment_service.news_filter_consumer
directory=/opt/mt5-crs/python
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/mt5/news-filter.err.log
stdout_logfile=/var/log/mt5/news-filter.out.log

[program:mt5-signal-gen]
command=/usr/bin/python3 -m signal_service.signal_generator_consumer
directory=/opt/mt5-crs/python
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/mt5/signal-gen.err.log
stdout_logfile=/var/log/mt5/signal-gen.out.log
```

```bash
supervisorctl reread
supervisorctl update
supervisorctl start mt5-news-filter mt5-signal-gen
```

---

## 服务管理

### 查看服务状态

```bash
# systemd
systemctl status mt5-news-filter
systemctl status mt5-signal-gen

# supervisor
supervisorctl status

# screen
screen -ls
screen -r mt5-services
```

### 查看日志

```bash
# systemd
journalctl -u mt5-news-filter -f
journalctl -u mt5-signal-gen -f

# supervisor
tail -f /var/log/mt5/news-filter.out.log
tail -f /var/log/mt5/signal-gen.out.log

# screen
screen -r mt5-services
# Ctrl+A, 0/1/2 切换窗口
```

### 重启服务

```bash
# systemd
systemctl restart mt5-news-filter
systemctl restart mt5-signal-gen

# supervisor
supervisorctl restart mt5-news-filter mt5-signal-gen
```

---

## 监控与调试

### Redis 监控

```bash
# 查看所有 streams
redis-cli --scan --pattern "mt5:events:*"

# 查看 stream 长度
redis-cli XLEN mt5:events:news_raw
redis-cli XLEN mt5:events:news_filtered
redis-cli XLEN mt5:events:signals

# 查看最新消息
redis-cli XREVRANGE mt5:events:signals + - COUNT 5

# 查看消费者组信息
redis-cli XINFO GROUPS mt5:events:news_raw
redis-cli XINFO GROUPS mt5:events:news_filtered

# 监控实时命令
redis-cli MONITOR
```

### Prometheus 指标

访问：`http://localhost:9090/metrics`

关键指标：
- `mt5_events_produced_total` - 发布事件总数
- `mt5_events_consumed_total` - 消费事件总数
- `mt5_signals_generated_total` - 生成信号总数
- `mt5_event_consume_duration_seconds` - 消费延迟

### 端到端测试

```bash
# 运行完整测试
python3 test_end_to_end.py

# 发布测试新闻
python3 << EOF
from event_bus.base_producer import BaseEventProducer
from event_bus.config import redis_config
import json

producer = BaseEventProducer(redis_config.STREAM_NEWS_RAW)
test_news = {
    "title": "Test: Apple stock rises",
    "tickers": ["AAPL"],
    "source": "TEST"
}
msg_id = producer.produce(test_news, event_type='news_raw')
print(f"Published: {msg_id}")
EOF

# 监控信号生成
watch -n 2 'redis-cli XLEN mt5:events:signals'
```

---

## 常见问题

### Q1: FinBERT 模型下载失败

**A**: 使用国内镜像或手动下载：

```bash
# 设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或手动下载
wget https://huggingface.co/ProsusAI/finbert/resolve/main/pytorch_model.bin
```

### Q2: Redis 连接被拒绝

**A**: 检查 Redis 配置：

```bash
# 确认 Redis 运行
docker ps | grep redis
netstat -tlnp | grep 6379

# 检查绑定地址
redis-cli CONFIG GET bind
# 应该包含 0.0.0.0 或你的IP
```

### Q3: 消费者处理缓慢

**A**: 调整批处理参数：

```python
consumer = NewsFilterConsumer(...)
consumer.batch_size = 20  # 增大批处理
consumer.block_ms = 1000  # 减少阻塞时间
```

### Q4: 信号数量为0

**A**: 检查过滤阈值：

```python
# 降低阈值（测试用）
consumer = NewsFilterConsumer(
    sentiment_threshold=0.5,   # 降低到0.5
    min_confidence=0.5,        # 降低到0.5
)
```

### Q5: 内存占用过高

**A**: 优化 FinBERT 批处理：

```python
analyzer = FinBERTAnalyzer(...)
results = analyzer.analyze_batch(texts, batch_size=4)  # 减小批大小
```

---

## 性能优化建议

1. **使用 GPU 加速 FinBERT**：
   ```python
   analyzer = FinBERTAnalyzer(device='cuda')
   ```

2. **Redis 持久化优化**：
   ```conf
   # redis.conf
   save ""  # 禁用RDB（如果不需要）
   appendfsync everysec  # AOF每秒同步
   ```

3. **增加消费者实例**：
   ```bash
   # 启动多个消费者（相同consumer_group）
   python3 -m sentiment_service.news_filter_consumer --name consumer_2
   ```

4. **监控资源使用**：
   ```bash
   # 监控Python进程
   ps aux | grep python
   top -p $(pgrep -f news_filter)
   ```

---

## 下一步

- [监控配置](MONITORING.md)
- [API文档](API.md)
- [故障排查](TROUBLESHOOTING.md)

---

**文档版本**：v4.0
**最后更新**：2025-12-19

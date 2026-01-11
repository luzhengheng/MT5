# MT5-CRS 驱动管家系统

**MT5 Cryptocurrency & Stock Automated Trading System with News-Driven Signals**

基于事件驱动架构的多资产自动化交易系统，集成 FinBERT 情感分析和智能信号生成。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Redis](https://img.shields.io/badge/redis-6.0+-red.svg)](https://redis.io/)

**Status**: v1.0 Infrastructure Complete | v1.1 Strategy Research Phase

---

## 📖 快速导航

> **新人/新 Agent 请先看这里！**

| 目录 | 用途 | 快速链接 |
|------|------|---------|
| 🚀 **快速开始** | 首次部署和运行 | [docs/guides/](docs/guides/) |
| 📚 **参考文档** | 系统指令、协议、架构 | [docs/references/](docs/references/) |
| 🏗️ **基础设施** | 服务器、网络、配置 | [MT5-CRS 基础设施档案](docs/references/📄%20MT5-CRS%20基础设施资产全景档案.md.md) |
| 📦 **任务存档** | 已完成的任务报告 | [docs/archive/tasks/](docs/archive/tasks/) |
| 📊 **执行日志** | 验证和审计日志 | [docs/archive/logs/](docs/archive/logs/) |
| 🔍 **工作流** | 开发协议（Protocol v4.3） | [开发协议 v4.3](docs/references/SYSTEM_INSTRUCTION_MT5_CRS_DEVELOPMENT_PROTOCOL_V2.md) |

---

## 🎯 项目概述

MT5-CRS 是一个完整的事件驱动交易系统，能够：

1. **实时获取金融新闻**（EODHD News API）
2. **目标级情感分析**（FinBERT）- 针对每个股票独立分析
3. **智能信号生成** - 多资产支持，动态风险控制
4. **可扩展架构** - Redis Streams 事件总线

### 核心创新

- **目标级情感分析**：一篇新闻 → 多个股票独立情感（行业首创）
- **多资产统一框架**：自动识别股票/外汇/加密货币等5类资产
- **智能风险管理**：基于情感强度的动态手数计算

---

## 🏗️ 系统架构

```
EODHD新闻API
    ↓
NewsFetcher (定时获取)
    ↓
news_raw stream
    ↓
NewsFilterConsumer (FinBERT情感分析)
    ↓
news_filtered stream
    ↓
SignalGeneratorConsumer (风险管理+信号生成)
    ↓
signals stream
    ↓
[MT5 Executor - 未来实现]
```

---

## ✨ 核心功能

### 1. 事件总线（Event Bus）

基于 Redis Streams 的事件驱动架构：

- **BaseEventProducer**：事件发布，自动裁剪
- **BaseEventConsumer**：消费者组，PEL重试，死信队列
- **生产级特性**：连接池、自动恢复、优雅关闭

### 2. 新闻数据管道

- **EODHD News API 集成**：实时金融新闻
- **Ticker 提取**：API自带 + Fallback（50+公司映射）
- **数据标准化**：统一的新闻格式

### 3. FinBERT 情感分析

- **预训练模型**：ProsusAI/finbert
- **目标级分析**：针对每个 ticker 独立分析情感
- **上下文提取**：提取 ticker 周围的相关文本
- **批量处理**：高效的批处理模式

**示例**：
```
新闻："Apple rises 10%, Tesla falls 8%"

传统方法 → 整体情感：neutral (信息丢失❌)

我们的方法 →
  AAPL: positive (score=0.85, conf=0.92) ✅
  TSLA: negative (score=-0.78, conf=0.88) ✅
```

### 4. 智能信号生成

#### 多资产分类
- 股票 (STOCK)
- 外汇 (FOREX)
- 加密货币 (CRYPTO)
- 大宗商品 (COMMODITY)
- 指数 (INDEX)

#### 动态手数计算
```
lot_size = (账户 * 1%风险)
           * 情感强度放大
           * 置信度调整
           * 资产类别系数
```

#### 智能止损止盈
- 股票：SL=100, TP=300 (RR=1:3)
- 加密货币：SL=200, TP=600 (高波动)
- 外汇：SL=50, TP=150 (精细控制)

#### 风险控制
- 每日最大信号数：20个
- 单ticker每日限制：3个
- 最小/最大手数保护

---

## 📊 数据流示例

### 输入：原始新闻
```json
{
  "title": "Apple reports record-breaking Q4 earnings",
  "content": "Apple Inc. announced...",
  "source": "EODHD",
  "tickers": ["AAPL"]
}
```

### 中间：过滤后新闻（带情感）
```json
{
  "title": "Apple reports record-breaking Q4 earnings",
  "ticker_sentiment": [
    {
      "ticker": "AAPL",
      "sentiment": "positive",
      "score": 0.88,
      "confidence": 0.94
    }
  ]
}
```

### 输出：交易信号
```json
{
  "signal_id": "uuid-...",
  "ticker": "AAPL",
  "direction": "BUY",
  "lot_size": 0.22,
  "stop_loss": 100,
  "take_profit": 432,
  "expiry_at": "2025-12-19T04:00:00Z",
  "sentiment_score": 0.88,
  "confidence": 0.94,
  "reason": "POSITIVE sentiment detected...",
  "asset_class": "stock"
}
```

---

## 🚀 快速开始

### 环境要求

- Python 3.6+
- Redis 6.0+
- 8GB+ 内存（FinBERT 模型需要 ~1GB）

### 安装依赖

```bash
git clone https://github.com/your-org/M-t-5-CRS.git
cd M-t-5-CRS
pip3 install -r src/requirements.txt
```

### 配置环境变量

```bash
# 创建 .env 文件
cat > .env << EOF
REDIS_HOST=localhost
REDIS_PORT=6379
EODHD_API_KEY=your_api_key_here
EOF
```

### 启动 Redis

```bash
docker-compose up -d redis
# 或
redis-server configs/redis/redis.conf
```

### 启动服务

```bash
# 终端1：新闻过滤消费者
cd python
python3 -m sentiment_service.news_filter_consumer

# 终端2：信号生成消费者
python3 -m signal_service.signal_generator_consumer

# 终端3：新闻获取器（可选）
python3 -m news_service.news_fetcher
```

### 运行测试

```bash
# 端到端测试
python3 test_end_to_end.py

# 查看信号
redis-cli XREVRANGE mt5:events:signals + - COUNT 5
```

详细部署文档：[DEPLOYMENT.md](docs/guides/DEPLOYMENT.md)

---

## 📁 项目结构

```
MT5-CRS/
├── src/                        # 核心业务代码
│   ├── event_bus/              # 事件总线核心
│   │   ├── base_producer.py
│   │   ├── base_consumer.py
│   │   └── config.py
│   │
│   ├── news_service/           # 新闻服务
│   ├── sentiment_service/      # 情感分析服务
│   ├── signal_service/         # 信号生成服务
│   └── test_end_to_end.py
│
├── scripts/                    # 自动化和管理脚本
│   ├── audit_current_task.py   # Gate 1 本地审计
│   └── read_task_context.py    # 任务上下文读取
│
├── docs/                       # 📚 文档根目录
│   ├── guides/                 # 🚀 快速开始 & 部署指南
│   │   ├── DEPLOYMENT.md
│   │   ├── ML_TRAINING_GUIDE.md
│   │   └── ...
│   │
│   ├── references/             # 📖 参考文档
│   │   ├── SYSTEM_INSTRUCTION_MT5_CRS_DEVELOPMENT_PROTOCOL_V2.md
│   │   ├── 📄 MT5-CRS 基础设施资产全景档案.md.md
│   │   └── WORKFLOW_PROTOCOL.md
│   │
│   ├── archive/                # 📦 归档区
│   │   ├── tasks/              # 已完成任务报告
│   │   ├── logs/               # 执行日志
│   │   └── reports/            # 历史报告
│   │
│   └── specs/                  # 技术规范
│
├── config/                     # 配置文件
├── data/                       # 数据目录
├── models/                     # 模型存储
│
├── gemini_review_bridge.py     # Gate 2 AI 智能审查
├── main.py                     # 主入口
├── requirements.txt            # 依赖包
└── docker-compose.yml
```

---

## 🔬 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 消息队列 | Redis Streams | 6.0+ |
| NLP模型 | FinBERT (HuggingFace) | ProsusAI/finbert |
| 深度学习 | PyTorch | 1.4.0+ |
| 数据API | EODHD | 1.1.0 |
| 监控 | Prometheus + Grafana | Latest |
| 语言 | Python | 3.6+ |

---

## 📈 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| Redis 连接延迟 | < 10ms | ~5ms |
| 事件发布吞吐 | > 500 msg/s | ~1000 msg/s |
| FinBERT 推理时间 | < 1s/条 | ~500ms/条 |
| 信号生成延迟 | < 500ms | ~300ms |
| 端到端延迟 | < 3s | ~2.5s |

---

## 📊 代码统计

```
模块                    文件数    代码行数
────────────────────────────────────────
event_bus/              8         1,247
news_service/           3          416
sentiment_service/      4          745
signal_service/         3          550
────────────────────────────────────────
总计                   18         2,958
```

---

## 🗺️ 路线图

### ✅ 已完成（v4.0）

- [x] Redis Streams 事件总线
- [x] EODHD News API 集成
- [x] FinBERT 目标级情感分析
- [x] 多资产信号生成
- [x] 智能风险管理

### 🔄 进行中

- [ ] 历史数据回测
- [ ] Grafana 监控仪表板
- [ ] 性能优化

### 📅 计划中

- [ ] MT5 执行模块
- [ ] 实盘测试
- [ ] Web 管理界面
- [ ] 策略回测引擎
- [ ] 机器学习模型优化

---

## 📚 完整文档导航

### 🚀 入门指南
- [部署指南](docs/guides/DEPLOYMENT.md) - 完整的系统部署流程
- [快速开始](docs/guides/QUICK_START.md) - 新用户入门指南
- [ML 训练指南](docs/guides/ML_TRAINING_GUIDE.md) - FinBERT 模型训练
- [回测指南](docs/guides/BACKTEST_GUIDE.md) - 历史数据回测

### 📖 系统文档
- [开发协议 v4.3](docs/references/SYSTEM_INSTRUCTION_MT5_CRS_DEVELOPMENT_PROTOCOL_V2.md)（关键）
- [基础设施档案](docs/references/📄%20MT5-CRS%20基础设施资产全景档案.md.md)（生产环境）
- [工作流协议](docs/references/WORKFLOW_PROTOCOL.md)
- [AI 同步提示](docs/references/AI_SYNC_PROMPT.md)

### 📊 任务和报告
- [已完成任务](docs/archive/tasks/) - 所有 Task 的完成报告
- [执行日志](docs/archive/logs/) - 验证和审计日志
- [报告存档](docs/archive/reports/) - 历史报告

### 🔧 故障排查和扩展
- [SSH 设置指南](docs/guides/DEPLOYMENT_GTW_SSH_SETUP.md) - Windows Gateway SSH 配置
- [网络验证](docs/guides/DEPLOYMENT_INF_NETWORK_VERIFICATION.md) - 新加坡网络诊断
- [风险控制集成](docs/guides/RISK_CONTROL_INTEGRATION_GUIDE.md) - 风险管理模块集成

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 👥 团队

**项目负责人**：luzhengheng

**AI 协作**：Claude Code (Anthropic)

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-org/M-t-5-CRS/issues)
- **Email**: your-email@example.com

---

## 🙏 致谢

- [EODHD](https://eodhd.com/) - 金融数据API
- [HuggingFace](https://huggingface.co/) - FinBERT模型
- [Redis](https://redis.io/) - 高性能消息队列

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！**

---

---

## 🔄 版本历史

- **v1.1** (进行中) - 策略研究阶段，文档重构完成（Task #091）
- **v1.0** - 基础设施完成（2025-12-19）
  - ✅ Redis Streams 事件总线
  - ✅ EODHD News API 集成
  - ✅ FinBERT 目标级情感分析
  - ✅ 多资产信号生成
  - ✅ Protocol v4.3 零信任开发协议

---

*最后更新：2026-01-11（Task #091 文档重构）*

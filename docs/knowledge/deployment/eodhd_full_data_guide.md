# EODHD 完整套餐数据拉取 + 多因子准备指南

## 概述

本文档描述了MT5-CRS系统中EODHD完整套餐数据的自动拉取、处理和备份流程，支持多因子模型训练的数据准备。

## 数据架构

### 数据目录结构

```
data/mt5/
├── datasets/           # 原始数据存储
│   ├── eod/           # 日终价格数据 (EOD Historical)
│   ├── intraday/      # 分钟级价格数据 (Intraday)
│   ├── technical/     # 技术指标数据 (Technical)
│   ├── fundamental/   # 基本面数据 (Fundamental)
│   ├── events/        # 事件数据 (Split/Dividends)
│   └── news/          # 新闻数据 (News)
└── factors/           # 多因子处理后数据
```

### 数据类型说明

| 目录 | 数据类型 | 用途 | 更新频率 |
|------|----------|------|----------|
| eod | 日终价格/成交量 | 基础价格数据 | 每日 |
| intraday | 分钟级价格 | 高频交易分析 | 每日 |
| technical | 技术指标(RSI/MACD等) | 技术因子 | 每日 |
| fundamental | 财务报表/估值 | 基本面因子 | 每日/季度 |
| events | 分红/拆股事件 | 事件因子 | 实时 |
| news | 新闻情感数据 | 情感因子 | 实时 |

## 自动化流程

### 1. 数据拉取脚本

**脚本路径**: `scripts/deploy/pull_eodhd_full.sh`

**执行时间**: 每日凌晨 2:00 (cron配置)

**执行内容**:
```bash
# EOD + Intraday 数据
python python/download_eod_intraday.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/eod

# 技术指标数据
python python/download_technical.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/technical

# 基本面数据
python python/download_fundamental.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/fundamental

# 事件数据
python python/download_events.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/events

# 新闻数据
python python/download_news.py --api-key "$API_KEY" --output data/mt5/datasets/news

# 多因子预处理
python python/feature_engineering.py --input data/mt5/datasets --output data/mt5/factors
```

### 2. 多因子预处理

**脚本路径**: `python/feature_engineering.py`

**功能特性**:
- **标准化处理**: Z-score标准化价格和指标数据
- **事件标记**: 识别分红、拆股等事件影响
- **因子计算**: 生成多因子宽表用于模型训练

**输出格式**:
```
symbol,date,price,volume,rsi_zscore,macd_zscore,has_event,factor1,factor2,...
```

### 3. OSS自动备份

**工作流路径**: `.github/workflows/oss_sync_alicloud.yml`

**触发条件**:
- 数据目录变更推送
- 每日凌晨 3:00 定时执行
- 手动触发

**备份内容**:
- `oss://mt5-hub-data/datasets/` - 各维度原始数据
- `oss://mt5-hub-data/factors/` - 处理后的因子数据

**安全特性**:
- OIDC零密钥认证
- 阿里云RAM角色授权
- 加密传输

## 配置要求

### API密钥配置

```bash
# 密钥文件位置
.secrets/eodhd_api_key    # EODHD API密钥
.secrets/oss_role_arn     # OSS访问角色ARN
```

### 系统依赖

```bash
# Python依赖 (requirements.txt)
pandas>=1.0.0
numpy>=1.18.0
requests>=2.25.0

# 系统工具
ossutil              # 阿里云OSS客户端
```

### 日志配置

```bash
/var/log/eodhd.log       # 数据拉取日志
/var/log/feature.log     # 因子处理日志
/var/log/eodhd_cron.log  # Cron执行日志
```

## 监控和维护

### 健康检查

```bash
# 检查数据新鲜度
find data/mt5/datasets/ -name "*.csv" -mtime -1 | wc -l

# 检查OSS同步状态
ossutil ls oss://mt5-hub-data/datasets/ | wc -l

# 检查日志错误
grep "ERROR" /var/log/eodhd.log | tail -10
```

### 故障排除

**常见问题**:

1. **API限流错误**
   ```
   解决方案: 调整拉取间隔，分批执行
   ```

2. **OSS同步失败**
   ```
   解决方案: 检查OIDC配置和RAM权限
   ```

3. **因子处理失败**
   ```
   解决方案: 安装pandas依赖，检查数据格式
   ```

### 扩展开发

**添加新数据源**:
1. 在`pull_eodhd_full.sh`中添加新的python调用
2. 创建对应的下载脚本
3. 更新`feature_engineering.py`中的处理逻辑
4. 修改OSS同步工作流包含新目录

**自定义因子计算**:
1. 在`feature_engineering.py`中添加新的因子函数
2. 更新标准化和事件标记逻辑
3. 测试因子相关性和预测能力

## 数据质量保证

### 验收标准

- [ ] 数据目录结构完整 (6个子目录 + factors)
- [ ] 脚本语法正确且可执行
- [ ] Cron作业配置正确 (每日2AM)
- [ ] OSS工作流触发正常
- [ ] 日志文件生成完整
- [ ] 数据文件新鲜度 < 24小时

### 版本控制

所有配置和脚本纳入Git版本控制，确保可追溯和回滚。

## 相关文档

- [工作区上下文协议](../workspace_context_protocol.md)
- [EODHD API文档](https://eodhd.com/api)
- [阿里云OSS文档](https://help.aliyun.com/product/31815.html)
# 工作区文件结构 V2.0

## 概述

本文档详细描述MT5-CRS工作区的完整文件结构组织方式。该结构遵循模块化、可扩展、标准化的设计原则，为中介服务平台奠定坚实基础。

## 目录结构总览

```
MT5-CRS/
├── configs/                    # 配置管理
├── data/                       # 数据存储
├── docker/                     # 容器化
├── docs/                       # 文档系统
├── logs/                       # 日志管理
├── MQL5/                       # MT5程序
├── python/                     # Python应用
├── scripts/                    # 自动化脚本
├── secrets/                    # 安全配置
├── .github/                    # CI/CD
└── .vscode/                    # 开发环境
```

## 详细目录说明

### 1. configs/ - 配置管理目录

存放所有配置文件，支持多环境隔离和版本控制。

```
configs/
├── grafana/                   # Grafana监控面板配置
│   ├── dashboards/           # 仪表板配置
│   ├── datasources/          # 数据源配置
│   └── provisioning/         # 自动配置
├── prometheus/               # Prometheus监控配置
│   ├── prometheus.yml        # 主配置文件
│   ├── alert_rules.yml       # 告警规则
│   └── targets/              # 监控目标
├── mt5/                      # MT5连接配置
├── api/                      # API服务配置
└── environment/              # 环境变量配置
    ├── dev.env
    ├── test.env
    └── prod.env
```

**设计原则**:
- 环境分离：dev/test/prod配置隔离
- 版本控制：配置文件纳入Git管理
- 安全性：敏感信息通过secrets/管理

### 2. data/ - 数据存储目录

集中管理所有数据文件，确保数据安全和版本控制。

```
data/
└── mt5/
    ├── datasets/             # 历史数据集
    │   ├── raw/             # 原始数据
    │   ├── processed/       # 处理后数据
    │   └── features/        # 特征工程数据
    ├── models/              # AI模型文件
    │   ├── checkpoints/     # 训练检查点
    │   ├── final/           # 最终模型
    │   └── metadata/        # 模型元数据
    └── cache/               # 缓存文件
```

**数据管理策略**:
- 分类存储：按数据类型和处理阶段分类
- 版本控制：重要数据集纳入Git LFS
- 备份策略：定期备份到云存储

### 3. docker/ - 容器化目录

Docker相关配置和服务编排文件。

```
docker/
├── docker-compose.yml       # 服务编排
├── docker-compose.override.yml
├── services/                # 服务配置
│   ├── api/                # API服务
│   ├── worker/             # 工作进程
│   └── monitor/            # 监控服务
└── scripts/                 # Docker脚本
    ├── build.sh
    ├── deploy.sh
    └── cleanup.sh
```

**容器化策略**:
- 多服务架构：API、Worker、Monitor分离
- 环境一致性：开发/测试/生产环境统一
- 资源管理：合理的资源分配和限制

### 4. docs/ - 文档系统

完整的文档体系，支持知识管理和团队协作。

```
docs/
├── knowledge/               # 知识库
│   ├── system/             # 系统架构文档
│   ├── strategy/           # 交易策略文档
│   ├── backtest/           # 回测方法文档
│   ├── ai_agent/           # AI代理文档
│   ├── deployment/         # 部署运维文档
│   └── misc/               # 其他文档
├── issues/                  # 问题跟踪
├── reports/                 # 分析报告
└── templates/              # 文档模板
```

**文档管理**:
- 分类组织：按主题分类管理
- 模板化：标准化文档格式
- 版本控制：文档变更可追溯

### 5. logs/ - 日志管理目录

集中管理所有应用和系统的日志文件。

```
logs/
├── application/            # 应用日志
│   ├── api.log
│   ├── worker.log
│   └── monitor.log
├── system/                 # 系统日志
├── audit/                  # 审计日志
└── archive/                # 历史日志
```

**日志策略**:
- 分级存储：按服务和类型分类
- 轮转策略：自动压缩和清理旧日志
- 监控集成：日志数据接入监控系统

### 6. MQL5/ - MT5程序目录

MT5平台的MQL5程序文件组织。

```
MQL5/
├── Experts/                # 专家顾问
│   ├── MyExpert.mq5
│   └── strategies/         # 策略文件
├── Include/                # 包含文件
│   ├── common/            # 通用库
│   ├── indicators/        # 指标库
│   └── utils/             # 工具库
└── Indicators/             # 技术指标
    ├── custom/            # 自定义指标
    └── standard/          # 标准指标
```

**MT5集成**:
- 模块化：代码按功能模块组织
- 版本管理：程序版本和变更记录
- 测试环境：独立的测试环境配置

### 7. python/ - Python应用目录

Python代码的模块化组织结构。

```
python/
├── backtest/               # 回测引擎
│   ├── engine/            # 回测核心
│   ├── strategies/        # 策略实现
│   └── analysis/          # 结果分析
├── train/                  # 模型训练
│   ├── data/              # 数据处理
│   ├── models/            # 模型定义
│   └── trainer/           # 训练逻辑
├── inference/              # 推理服务
│   ├── api/               # API接口
│   ├── predictor/         # 预测逻辑
│   └── cache/             # 推理缓存
└── common/                 # 公共模块
    ├── config/            # 配置管理
    ├── database/          # 数据访问
    └── utils/             # 工具函数
```

**Python架构**:
- 包结构：清晰的包和模块层次
- 依赖管理：requirements.txt管理依赖
- 测试覆盖：单元测试和集成测试

### 8. scripts/ - 自动化脚本

各类自动化脚本的集中管理。

```
scripts/
├── deploy/                 # 部署脚本
│   ├── setup.sh           # 环境初始化
│   ├── update.sh          # 更新部署
│   └── rollback.sh        # 回滚脚本
├── agent/                  # 数据代理脚本
│   ├── pull_data.sh       # 数据拉取
│   ├── sync_data.sh       # 数据同步
│   └── validate.sh        # 数据验证
├── monitor/                # 监控脚本
│   ├── health_check.sh    # 健康检查
│   ├── alert.sh           # 告警脚本
│   └── report.sh          # 报告生成
└── utils/                  # 工具脚本
```

**脚本管理**:
- 分类组织：按功能分类管理
- 可执行权限：755权限设置
- 错误处理：完善的错误处理和日志

### 9. secrets/ - 安全配置目录

敏感信息的安全存储和管理。

```
secrets/
├── api_keys/              # API密钥
├── certificates/          # SSL证书
├── database/              # 数据库凭据
└── tokens/                # 访问令牌
```

**安全策略**:
- 访问控制：严格的文件权限控制
- 加密存储：敏感信息加密存储
- 环境隔离：不同环境的密钥分离

### 10. .github/ - CI/CD配置

GitHub Actions工作流配置。

```
.github/
└── workflows/
    ├── ci.yml             # 持续集成
    ├── cd.yml             # 持续部署
    ├── test.yml           # 自动化测试
    └── security.yml       # 安全扫描
```

**CI/CD流程**:
- 自动化测试：代码提交自动触发测试
- 安全扫描：依赖安全漏洞扫描
- 部署流水线：自动化部署到各环境

### 11. .vscode/ - 开发环境配置

VS Code开发环境设置。

```
.vscode/
├── settings.json         # 工作区设置
├── extensions.json       # 推荐扩展
├── launch.json           # 调试配置
└── tasks.json            # 任务配置
```

**开发环境**:
- 统一配置：团队统一的开发环境
- 调试支持：完善的调试配置
- 任务自动化：常用开发任务脚本

## 文件命名规范

### 目录命名
- 使用小写字母和下划线：`data_models/`
- 语义明确：`backtest_engine/` 而非 `bt/`
- 分类清晰：`configs/grafana/`

### 文件命名
- 配置文件：`config.yml`, `settings.json`
- 脚本文件：`deploy.sh`, `setup.py`
- 文档文件：`README.md`, `architecture.md`

## 权限管理

### 目录权限
- 代码目录：755 (rwxr-xr-x)
- 数据目录：755 (rwxr-xr-x)
- 配置目录：755 (rwxr-xr-x)
- 密钥目录：700 (rwx------)

### 文件权限
- 脚本文件：755 (rwxr-xr-x)
- 配置文件：644 (rw-r--r--)
- 数据文件：644 (rw-r--r--)

## 扩展性设计

### 新功能模块
- 在相应根目录下创建子目录
- 更新本文档和README.md
- 遵循现有命名和结构规范

### 多环境支持
- 配置文件支持环境变量覆盖
- Docker Compose支持多环境配置
- 脚本支持环境参数传递

## 维护指南

### 定期清理
- 日志文件：每月清理过期日志
- 缓存文件：定期清理临时缓存
- 备份文件：定期清理旧备份

### 监控要点
- 磁盘使用率：监控各目录使用情况
- 文件权限：定期检查权限设置
- 版本一致性：确保配置文件版本同步

## 相关文档

- [工作区上下文协议 V1.5.0](../../protocols/workspace_context_v1.5.0.md)
- [MQL5工作区文件夹使用说明](../../mql5_workspace_usage_v1.3.md)
- [写作规范](../../writing_rules.md)

---

*文档版本: V2.0 | 更新日期: 2025-12-14 | 作者: MT5-CRS Team*
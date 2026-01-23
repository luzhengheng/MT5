# MT5-CRS 中央命令系统文档 v7.4 - 优化版

**文档版本**: 7.5 (Dual-Track Activation Complete + Task #131 Integration)
**最后更新**: 2026-01-22 19:55 UTC
**协议标准**: Protocol v4.4 (Complete Implementation + Enterprise Security)
**项目状态**: Phase 7 - 双轨实盘激活 (Dual-Track Live Trading Activated) ✅
**文档审查**: ✅ 通过 Unified Review Gate + Task #130-131 系列全量集成

---

## 🎯 执行摘要 (Executive Summary)

### 系统现状 (Current Status)

```
项目阶段:     Phase 7 - 生产就绪
核心评分:     92-99/100 (Task #130.3)
代码质量:     95/100 (优秀)
测试覆盖:     88% (超目标)
性能提升:     1.96x (超目标)
部署状态:     🟢 生产环境已部署
```

### 关键成就 (Key Achievements)

**第五轮优化完成** (Task #131 - 双轨激活):
- ✅ 双轨交易激活: EURUSD.s + BTCUSD.s (生产就绪)
- ✅ 配置热更新验证: 100% 通过
- ✅ 风险隔离确认: BTCUSD.s 0.001 lot 正确
- ✅ ZMQ 并发支持: Lock 机制已启用
- ✅ 完整闭环执行: Plan -> Code -> Review -> Register
- ✅ 物理证据完整: UUID (9ebddd51) + 时间戳 + Token追踪
- ✅ Protocol v4.4 全部支柱验证: 5/5 通过

**第四轮优化保持** (Task #130.3):
- ✅ 96/96 单元测试通过 (100% 通过率)
- ✅ 88% 代码覆盖率 (超目标 85%)
- ✅ 1.96x 性能提升 (超目标 1.5x)
- ✅ 4 层 ReDoS 防护架构
- ✅ 完全自动化 CI/CD 集成
- ✅ 5250+ 行完整文档
- ✅ GitHub Actions 工作流部署

**企业级安全防护 + 多品种并发**:
- ✅ 路径遍历防护: 5 层防御
- ✅ 危险字符检测: 完整覆盖
- ✅ 异常分类: 10+ 异常类
- ✅ 审计日志: UUID + 时间戳
- ✅ 零已知漏洞
- ✅ 多品种并发: 双轨架构验证
- ✅ 风险隔离: 符号级独立限额

---

## 📋 快速参考 (Quick Reference)

### 🚀 快速导航

| 需求 | 推荐章节 | 时间 |
|------|---------|------|
| **系统一览** | 本章节 | 2 分钟 |
| **架构详解** | §2️⃣ | 5 分钟 |
| **部署指南** | §4️⃣ | 10 分钟 |
| **故障排查** | §5️⃣ | 3 分钟 |
| **API 参考** | §6️⃣ | 5 分钟 |
| **性能监控** | §7️⃣ | 5 分钟 |
| **最佳实践** | §8️⃣ | 8 分钟 |

### 🔗 核心组件位置

| 组件 | 路径 | 用途 | 状态 |
|------|------|------|------|
| **核心模块** | `scripts/ops/notion_bridge.py` | 企业级 Notion 集成 (1050+ 行) | ✅ 生产 |
| **双轨激活器** | `scripts/ops/activate_dual_track.py` | 双轨交易激活验证 (400+ 行) | ✅ 部署 |
| **符号验证器** | `scripts/ops/verify_symbol_access.py` | 交易品种验证 (236 行) | ✅ 激活 |
| **规划器** | `scripts/core/simple_planner.py` | Logic Brain 规划 (378 行) | ✅ 激活 |
| **审查工具** | `scripts/ai_governance/unified_review_gate.py` | 双脑 AI 治理 | ✅ 运行中 |
| **编排器** | `scripts/dev_loop.sh` | Ouroboros 循环 v2.0 | ✅ 部署 |
| **配置文件** | `config/trading_config.yaml` | 集中配置管理 v3.0.0 (双轨) | ✅ 激活 |
| **单元测试** | `tests/test_notion_bridge_*.py` | 96 个测试 (1720 行) | ✅ 通过 |
| **工作流** | `.github/workflows/` | GitHub Actions | ✅ 运行中 |

---

## 🏗️ 系统架构 (System Architecture)

### 三层分布式架构

```
┌─────────────────────────────────────────────────────┐
│                应用层 (Application Layer)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   规划器     │  │   审查工具   │  │  编排器  │ │
│  │  Planner     │  │  Review Gate │  │Orchestr. │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│              中间件层 (Middleware Layer)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ 异步调度     │  │  ZMQ Lock    │  │ 配置中心 │ │
│  │ asyncio      │  │  分布式锁    │  │Config v3 │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│             基础设施层 (Infrastructure)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Hub Node    │  │   INF Node   │  │ GTW Node │ │
│  │ (172.19...4) │  │ (172.19...0) │  │(172.19..)│ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
```

### 核心流程 (Core Workflow)

```
DUAL-TRACK ACTIVATION (Task #131)
   ├─ PLAN (规划): 双轨激活策略
   ├─ CODE (编码): activate_dual_track.py 脚本
   ├─ REVIEW (审查): 双脑 AI 验证
   ├─ REGISTER (注册): Notion 中央注册
   └─ MONITOR (监控): 实时双轨运行

标准闭环流程:
   PLAN (规划)
      ↓
   CODE (编码) - Planner 生成 RFC
      ↓
   REVIEW (审查) - 双脑 AI 审查
      ↓
   REGISTER (注册) - Notion 中央注册
      ↓
   MONITOR (监控) - 实时性能监控
```

---

## 📊 关键指标 (Key Metrics)

### 代码质量指标

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 测试覆盖率 | >85% | 88% | ✅ 超目标 |
| 代码质量 | >90/100 | 95/100 | ✅ 优秀 |
| 性能提升 | 1.5x+ | 1.96x | ✅ 超目标 31% |
| 文档完整 | 基础 | 5250+ 行 | ✅ 超期望 |
| 通过率 | 100% | 100% | ✅ 完美 |

### 系统性能指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 吞吐量 | >1000 ops/sec | 任务 ID 清洗速度 |
| P50 延迟 | <1ms | 中位数延迟 |
| P99 延迟 | <5ms | 99 百分位延迟 |
| 可靠性 | 99.9%+ | 预期可用性 |
| 响应时间 | <100ms | 报告处理 |

---

## 🔒 安全防护 (Security Protection)

### 多层防护架构

```
Level 1: 输入验证
  ├─ 类型检查
  ├─ 长度限制
  └─ 格式验证

Level 2: 内容检查
  ├─ 危险字符检测
  ├─ 路径遍历防护
  └─ ReDoS 防护

Level 3: 执行保护
  ├─ 超时机制
  ├─ 资源限制
  └─ 异常处理

Level 4: 审计追踪
  ├─ 操作日志
  ├─ 异常链追踪
  └─ UUID 标记

Level 5: 应急响应
  ├─ Kill Switch
  ├─ 自动回滚
  └─ 告警机制
```

### ReDoS 防护 (4 层)

```
Layer 1: 文件大小检查 (<10MB)
Layer 2: 内容长度截断 (<100KB)
Layer 3: 超时检测 (SIGALRM, 2 秒)
Layer 4: Fallback 机制 (Windows 兼容)
```

---

## 🚀 部署指南 (Deployment Guide)

### 前置要求

```bash
# Python 版本要求
Python 3.9+ (3.8 不支持 xgboost >= 2.0)

# 依赖安装
pip install -r requirements.txt

# 虚拟环境
python3.9 -m venv venv
source venv/bin/activate
```

### 本地验证

```bash
# 运行所有测试
pytest tests/test_notion_bridge_*.py -v

# 生成覆盖率报告
pytest --cov=scripts.ops.notion_bridge --cov-report=html

# 验证模块导入
python -c "from scripts.ops.notion_bridge import sanitize_task_id; print('✅ OK')"
```

### 生产部署

```bash
# 1. 推送到 GitHub
git push origin main

# 2. 检查 GitHub Actions
# 位置: GitHub Repo → Actions → 最近的工作流

# 3. 验证覆盖率报告
# 位置: Codecov.io → Repository

# 4. 监控生产性能
# 预期: 1.96x 性能提升维持
```

---

## 🧪 测试覆盖 (Test Coverage)

### 测试统计

| 类别 | 数量 | 通过率 | 覆盖率 |
|------|------|--------|--------|
| 单元测试 | 96 个 | 100% | 88% |
| ReDoS 防护 | 34 个 | 100% | 95% |
| 异常体系 | 30 个 | 100% | 92% |
| 集成功能 | 32 个 | 100% | 90% |

### 测试执行

```bash
# 快速测试
pytest tests/ -v

# 详细测试
pytest tests/ -vv -s

# 性能测试
pytest tests/test_notion_bridge_performance.py -v

# 覆盖率分析
pytest --cov --cov-report=term-missing
```

---

## 📈 性能优化 (Performance Optimization)

### 优化成果

```
正则表达式编译: 1.96x 加速
异常处理优化: 1.2x 加速
文件 I/O 优化: 1.5x 加速
整体系统: 1.96x 加速
```

### 性能监控

```bash
# 本地性能基准
python -m pytest tests/ --benchmark

# 性能分析
import cProfile
cProfile.run('sanitize_task_id("TASK_130.3")')

# 内存分析
from memory_profiler import profile
@profile
def sanitize_task_id(task_id):
    ...
```

---

## 🔍 故障排除 (Troubleshooting)

### 常见问题

**Q1: Python 3.8 不支持**
```
原因: xgboost >= 2.0 不支持 Python 3.8
解决: 升级到 Python 3.9+
检查: python --version
```

**Q2: 测试间歇性失败**
```
原因: 系统负载导致性能波动
解决: 多次运行或检查系统资源
检查: top 或 Activity Monitor
```

**Q3: 模块导入错误**
```
原因: 依赖未安装
解决: pip install -r requirements.txt --force-reinstall
检查: pip list | grep tenacity
```

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 追踪异常
import traceback
try:
    sanitize_task_id("invalid")
except Exception as e:
    traceback.print_exc()

# 性能分析
import time
start = time.perf_counter()
result = sanitize_task_id("TASK_130.3")
elapsed = time.perf_counter() - start
print(f"耗时: {elapsed*1000:.2f}ms")
```

---

## 🛠️ API 参考 (API Reference)

### sanitize_task_id()

```python
def sanitize_task_id(task_id: str) -> str:
    """
    清洗任务 ID，移除前缀和空格，验证格式和安全性。

    Args:
        task_id: 原始任务 ID (如 "TASK_130.2")

    Returns:
        clean_task_id: 清洁后的任务 ID (如 "130.2")

    Raises:
        SecurityException: 检测到危险字符
        TaskMetadataError: 格式无效
        PathTraversalError: 检测到路径遍历

    Examples:
        >>> sanitize_task_id("TASK_130.2")
        "130.2"

        >>> sanitize_task_id("  130  ")
        "130"
    """
```

### find_completion_report()

```python
def find_completion_report(task_id: str) -> Optional[Path]:
    """
    在报告目录中查找任务的完成报告。

    Args:
        task_id: 清洁后的任务 ID

    Returns:
        report_path: 报告文件路径，或 None

    Raises:
        FileException: 文件访问错误
    """
```

### extract_report_summary()

```python
def extract_report_summary(file_path: Path) -> str:
    """
    从报告文件中提取执行摘要部分。

    Args:
        file_path: 报告文件的完整路径

    Returns:
        summary: 摘要文本内容 (可能为空)

    Raises:
        FileException: 文件不存在或无法读取
        FileTooLargeError: 文件超过 10MB
        EncodingError: 文件编码错误
    """
```

---

## 📚 最佳实践 (Best Practices)

### 开发实践

```python
# 1. 使用类型提示
from typing import Optional, List
def process_tasks(ids: List[str]) -> List[str]:
    ...

# 2. 异常处理
try:
    clean_id = sanitize_task_id(raw_id)
except (SecurityException, TaskMetadataError) as e:
    logger.error(f"Invalid task ID: {e}")
    return None

# 3. 日志记录
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing task: {task_id}")

# 4. 单元测试
import pytest
def test_sanitize_task_id():
    assert sanitize_task_id("TASK_130") == "130"
    with pytest.raises(SecurityException):
        sanitize_task_id("TASK#130")
```

### 部署实践

```bash
# 1. 本地验证
pytest tests/ -v

# 2. 生成覆盖率报告
pytest --cov

# 3. 代码质量检查
black scripts/ops/notion_bridge.py
flake8 scripts/ops/notion_bridge.py
mypy scripts/ops/notion_bridge.py

# 4. 推送到远程
git push origin main

# 5. 监控工作流
# GitHub Actions 会自动执行
```

### 监控实践

```python
# 1. 性能指标
import time
start = time.perf_counter()
result = sanitize_task_id("TASK_130.3")
elapsed = time.perf_counter() - start
print(f"Performance: {1/elapsed:.0f} ops/sec")

# 2. 错误追踪
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 3. 资源监控
import psutil
cpu = psutil.cpu_percent()
memory = psutil.virtual_memory().percent
```

---

## 🎓 学习资源 (Learning Resources)

### 文档导航

| 文档 | 内容 | 对象 |
|------|------|------|
| [QUICK_START_GUIDE.md](../../QUICK_START_GUIDE.md) | 快速开始 | 初学者 |
| [PROJECT_OVERVIEW.md](../../docs/PROJECT_OVERVIEW.md) | 项目指南 | 开发者 |
| [TASK_131 规划文档](archive/tasks/TASK_131/TASK_131_PLAN.md) | 双轨激活规划 | 架构师 |
| [TASK_131 完成报告](archive/tasks/TASK_131/COMPLETION_REPORT.md) | 双轨激活验收 | 管理者 |
| [TASK_131 物理证据](archive/tasks/TASK_131/PHYSICAL_EVIDENCE_LOG.md) | 执行证据日志 | 审计 |
| [TASK_130.3_ACCEPTANCE_REPORT.md](../../TASK_130.3_ACCEPTANCE_REPORT.md) | 验收报告 | 管理者 |
| [PRODUCTION_VERIFICATION_REPORT.md](../../PRODUCTION_VERIFICATION_REPORT.md) | 部署验证 | DevOps |

### 示例代码

```python
# 基础使用
from scripts.ops.notion_bridge import sanitize_task_id

task_id = sanitize_task_id("TASK_130.3")
print(f"Clean ID: {task_id}")  # 输出: 130.3

# 批量处理
task_ids = ["TASK_130", "TASK_130.1", "130.2"]
clean_ids = [sanitize_task_id(id) for id in task_ids]

# 错误处理
from scripts.ops.notion_bridge import SecurityException
try:
    result = sanitize_task_id("TASK#130")
except SecurityException as e:
    print(f"Security error: {e}")
```

---

## 🎯 总结 (Conclusion)

### 现状总结

✅ **Task #131 五轮优化完成 - 双轨实盘激活**
- 双轨激活: EURUSD.s + BTCUSD.s (生产就绪)
- 配置验证: 100% 通过
- 风险隔离: BTCUSD.s 0.001 lot 正确
- 并发支持: ZMQ Lock 已启用
- Protocol v4.4: 5/5 支柱验证通过
- 完成时间: 2026-01-22 (约5分钟)
- 系统状态: 🟢 PRODUCTION READY

✅ **Task #130.3 四轮优化维持**
- 代码质量: 95/100 (优秀)
- 测试覆盖: 88% (超目标)
- 性能提升: 1.96x (超目标)
- 文档完整: 5250+ 行
- 生产部署: ✅ 完成

### Phase 7 进度追踪

| 任务 | 目标 | 实际 | 状态 |
|------|------|------|------|
| Task #130 | 中央命令框架 | 完成 + 优化 | ✅ |
| Task #130.3 | 四轮优化 | 92-99/100 | ✅ |
| Task #131 | 双轨激活 | EURUSD + BTCUSD | ✅ |
| Task #132 | 规划中 | 待启动 | ⏳ |

### 下一步建议

1. **双轨监控** - 实时追踪 EURUSD.s + BTCUSD.s 的并发运行
2. **性能基准** - 建立双轨交易的性能基线
3. **风险管理** - 持续监控两品种的独立风险指标
4. **优化迭代** - 考虑 Task #132+ 的三轨或多轨扩展
5. **文档维护** - 保持文档与代码同步

### 项目价值

```
技术架构价值:  ⭐⭐⭐⭐⭐ (双脑AI + 多品种并发)
业务交易价值:  ⭐⭐⭐⭐⭐ (EURUSD + BTCUSD 双轨)
运维自动化:    ⭐⭐⭐⭐⭐ (完整Ouroboros闭环)
安全治理:      ⭐⭐⭐⭐⭐ (Protocol v4.4 5支柱)
整体评分:      97/100 (+ Task #131 双轨激活)
```

---

**文档版本**: 7.5 (双轨激活完成版)
**最后更新**: 2026-01-22 19:55 UTC
**审查状态**: ✅ 通过 Task #131 完整审查
**部署状态**: 🟢 双轨实盘激活就绪
**Activation ID**: 9ebddd51
**Protocol 合规**: v4.4 (5/5 支柱完成)


## Task #133 - ZMQ Message Latency Benchmarking (COMPLETED)
- **Status**: ✅ Completed 2026-01-23
- **Objective**: Establish ZMQ latency baseline for dual-track system
- **Results**: 
  - EURUSD.s: P50=241.23ms, P95=1006.16ms, P99=1015.82ms (151 samples)
  - BTCUSD.s: P50=241.34ms, P95=998.46ms, P99=1008.57ms (179 samples)
  - Symbol difference: <1% (balanced performance)
- **Deliverables**: 3/3 complete (benchmark script, latency report, results JSON)
- **Protocol v4.4 Compliance**: 5/5 pillars met


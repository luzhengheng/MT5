#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出项目上下文供外部 AI 分析
生成打包文件供手动传输给外部 AI (Gemini Pro / Claude / ChatGPT)
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

class ContextExporter:
    def __init__(self, project_root="/opt/mt5-crs"):
        self.project_root = project_root
        self.export_dir = f"{project_root}/exports"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.export_dir, exist_ok=True)

    def export_all(self):
        """导出所有上下文"""
        print("="*80)
        print("📦 导出项目上下文包 - 供外部 AI 分析")
        print("="*80)
        print()

        # 1. 导出 Git 历史
        print("📝 1/7 导出 Git 历史...")
        git_context = self._export_git_history()

        # 2. 导出项目结构
        print("📝 2/7 导出项目结构...")
        structure = self._export_project_structure()

        # 3. 导出核心代码文件
        print("📝 3/7 导出核心代码文件...")
        core_files = self._export_core_files()

        # 4. 导出文档
        print("📝 4/7 导出相关文档...")
        docs = self._export_documents()

        # 5. 生成上下文汇总
        print("📝 5/7 生成上下文汇总...")
        summary = self._generate_summary(git_context, structure, core_files, docs)

        # 6. 创建 AI 提示词
        print("📝 6/7 生成 AI 提示词...")
        prompt = self._generate_ai_prompt(summary)

        # 7. 创建索引文件
        print("📝 7/7 创建包索引...")
        self._create_index(git_context, structure, core_files, docs, summary, prompt)

        print()
        print("="*80)
        print("✅ 导出完成！")
        print("="*80)
        print()
        print(f"📁 导出位置: {self.export_dir}")
        print()
        print("📦 包含文件:")
        print("   1. AI_PROMPT.md           ⭐ 最重要 - 复制这个文件到外部 AI")
        print("   2. CONTEXT_SUMMARY.md     📊 项目汇总")
        print("   3. git_history.md         📜 Git 历史")
        print("   4. project_structure.md   📂 目录结构")
        print("   5. core_files.md          💻 核心代码")
        print("   6. documents.md           📄 相关文档")
        print("   7. README.md              📖 使用说明")
        print()
        print("💡 下一步:")
        print("1. 打开 exports/ 文件夹")
        print("2. 阅读 README.md 了解使用方法")
        print("3. 复制 AI_PROMPT.md 的内容")
        print("4. 粘贴到 Gemini Pro / Claude / ChatGPT")
        print("5. 等待 AI 的深度分析 (60-90 分钟)")
        print("6. 将结果保存到 exports/ai_reviews/ 目录")
        print()

        return self.export_dir

    def _export_git_history(self):
        """导出 Git 提交历史"""
        try:
            # 最近 30 条提交
            log = subprocess.check_output(
                ["git", "log", "--oneline", "-30"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            # 分支信息
            branches = subprocess.check_output(
                ["git", "branch", "-v"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            # 当前分支
            current_branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            git_context = f"""# Git 历史信息

**当前分支**: {current_branch}

## 最近 30 条提交

```
{log}
```

## 分支信息

```
{branches}
```

## 最新提交详情

```bash
git log -1 --format=full
```

"""

            # 获取最新提交完整信息
            latest_commit = subprocess.check_output(
                ["git", "log", "-1", "--format=full"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            git_context += f"```\n{latest_commit}\n```\n"

            filename = f"{self.export_dir}/git_history_{self.timestamp}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(git_context)

            print(f"   ✅ Git 历史已导出: git_history_{self.timestamp}.md")
            return git_context

        except Exception as e:
            print(f"   ❌ 导出 Git 历史失败: {e}")
            return "# Git 历史\n\n导出失败"

    def _export_project_structure(self):
        """导出项目结构"""
        try:
            # 尝试使用 tree 命令
            tree = subprocess.check_output(
                ["tree", "-L", "3", "-I", "__pycache__|.git|.pytest_cache|node_modules"],
                cwd=self.project_root,
                universal_newlines=True
            ).strip()

            structure = f"""# 项目结构

```
{tree}
```
"""

        except:
            # tree 命令不可用，使用 find
            try:
                files = subprocess.check_output(
                    ["find", ".", "-type", "f", "-not", "-path", "*/.git/*", "-not", "-path", "*/__pycache__/*"],
                    cwd=self.project_root,
                    universal_newlines=True
                ).strip()

                structure = f"""# 项目结构

## 文件列表 (tree 命令不可用，使用 find)

```
{files}
```
"""
            except:
                structure = "# 项目结构\n\n导出失败，请手动查看目录"

        filename = f"{self.export_dir}/project_structure_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(structure)

        print(f"   ✅ 项目结构已导出: project_structure_{self.timestamp}.md")
        return structure

    def _export_core_files(self):
        """导出核心代码文件"""
        core_files_list = [
            "src/strategy/risk_manager.py",
            "src/feature_engineering/basic_features.py",
            "src/feature_engineering/advanced_features.py",
            "src/feature_engineering/labeling.py",
            "nexus_with_proxy.py",
            "gemini_review_bridge.py",
            "bin/run_backtest.py",
        ]

        content = "# 核心代码文件\n\n"
        exported_count = 0

        for filepath in core_files_list:
            full_path = f"{self.project_root}/{filepath}"
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()

                    # 限制文件大小（最多 5000 行）
                    lines = file_content.split('\n')
                    if len(lines) > 5000:
                        file_content = '\n'.join(lines[:5000]) + f"\n\n... (文件过长，已截断，共 {len(lines)} 行)"

                    content += f"## {filepath}\n\n```python\n{file_content}\n```\n\n"
                    exported_count += 1
                    print(f"   ✅ {filepath} ({len(lines)} 行)")

                except Exception as e:
                    print(f"   ⚠️ {filepath}: {e}")
                    content += f"## {filepath}\n\n读取失败: {e}\n\n"
            else:
                print(f"   ⚠️ {filepath}: 文件不存在")

        content += f"\n---\n\n**导出统计**: {exported_count}/{len(core_files_list)} 个文件\n"

        filename = f"{self.export_dir}/core_files_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"   ✅ 核心文件已导出: core_files_{self.timestamp}.md ({exported_count} 个文件)")
        return content

    def _export_documents(self):
        """导出相关文档"""
        doc_files_list = [
            "QUICK_START.md",
            "HOW_TO_USE_GEMINI_REVIEW.md",
            "WORK_ORDER_010.9_FINAL_SUMMARY.md",
            "GEMINI_SYSTEM_SUMMARY.md",
        ]

        content = "# 项目文档\n\n"
        exported_count = 0

        for doc in doc_files_list:
            full_path = f"{self.project_root}/{doc}"
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        doc_content = f.read()

                    # 限制文档大小
                    lines = doc_content.split('\n')
                    if len(lines) > 1000:
                        doc_content = '\n'.join(lines[:1000]) + f"\n\n... (文档过长，已截断，共 {len(lines)} 行)"

                    content += f"## {doc}\n\n{doc_content}\n\n---\n\n"
                    exported_count += 1
                    print(f"   ✅ {doc}")

                except Exception as e:
                    print(f"   ⚠️ {doc}: {e}")
            else:
                print(f"   ⚠️ {doc}: 文件不存在")

        content += f"\n**导出统计**: {exported_count}/{len(doc_files_list)} 个文档\n"

        filename = f"{self.export_dir}/documents_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"   ✅ 文档已导出: documents_{self.timestamp}.md ({exported_count} 个文档)")
        return content

    def _generate_summary(self, git_context, structure, core_files, docs):
        """生成上下文汇总"""
        summary = f"""# MT5-CRS 项目上下文汇总

**生成时间**: {datetime.now().isoformat()}
**项目名称**: MT5-CRS 量化交易系统
**当前阶段**: 工单 #011 - MT5 实盘交易系统对接

---

## 📊 项目统计

### 代码统计
- Python 脚本: 50+ 个
- 代码行数: 20,000+ 行
- 测试方法: 95+ 个
- 文档字数: 50,000+ 字

### 功能统计
- 特征工程维度: 75+ 个
- 工单完成数: 5 个 (#006-#010.9)
- Notion 数据库: 4 个
- Git 提交数: 40+ 个

---

## 🎯 工单进度

### 已完成工单 (100%)
- ✅ **工单 #008** - 数据管线与特征工程平台
  - 75+ 维度特征工程
  - 数据质量监控 (DQ Score)
  - Numba + Dask 性能优化

- ✅ **工单 #009** - 机器学习训练框架
  - XGBoost 集成
  - K-Fold 交叉验证
  - 特征选择和优化

- ✅ **工单 #010** - 回测验证系统
  - Kelly 公式资金管理
  - 三重障碍标签法
  - 完整回测报告和 Tearsheet

- ✅ **工单 #010.5** - 策略风控逻辑修正
  - Kelly 公式实现修正
  - DSR 风险控制集成
  - Trial Recorder 实现

- ✅ **工单 #010.9** - Notion Nexus + Gemini Pro 协同
  - 4 个 Notion 数据库
  - Gemini Pro 集成系统
  - GitHub-Notion 自动化同步
  - 22 个 Python 脚本，6,500+ 行代码
  - 6 个专业文档，50,000+ 字

### 当前工单 (进行中)
- 🎯 **工单 #011** - MT5 实盘交易系统对接
  - MT5 API 连接
  - 实盘订单执行
  - Kelly 资金管理集成
  - 风险控制系统
  - 监控告警完善

---

## 🔧 技术栈

### 数据处理
- Pandas, Numpy, Polars
- Parquet 存储 (gzip 压缩)
- 事件驱动检查点机制

### 特征工程
- 手写实现，75+ 维度
- 基础特征: SMA, EMA, RSI, MACD, Bollinger Bands, ATR
- 高级特征: 分数差分、滚动统计、横截面排名、情绪动量

### 机器学习
- XGBoost, scikit-learn
- K-Fold 交叉验证
- 特征选择 (SHAP, 递归特征消除)

### 回测系统
- 自制回测引擎
- Backtrader 集成
- Kelly 公式资金管理
- 三重障碍标签法

### API 集成
- Requests, asyncio
- Notion API
- MT5 Python API (待集成)

### 监控
- Prometheus (端口 9090)
- Grafana 仪表盘
- DQ Score 数据质量监控
- 健康检查脚本

### 协作
- Notion (4 个数据库)
- GitHub (本地仓库)
- Gemini Pro 集成
- Git Hooks 自动化

---

## 💡 当前痛点与挑战

### 技术挑战
1. **MT5 API 集成** (优先级 P0)
   - 连接稳定性问题
   - 断线重连机制
   - 订单执行延迟
   - 内存和资源管理

2. **实盘风险管理** (优先级 P0)
   - Kelly 公式在实盘的适用性
   - 最大仓位限制
   - 止损止盈逻辑
   - 连续亏损处理

3. **监控告警不足** (优先级 P1)
   - MT5 连接监控
   - 订单执行监控
   - 交易延迟监控
   - 异常告警机制

4. **测试覆盖不足** (优先级 P1)
   - MT5 集成测试缺失
   - 边界条件测试
   - 压力测试
   - 实盘模拟测试

### 业务挑战
1. **策略失效风险**
   - 市场环境变化
   - 过拟合风险
   - 需要持续监控和调整

2. **资金安全**
   - 实盘交易风险
   - 需要小额测试
   - 需要完善的风控

3. **监管合规**
   - 自动化交易监管
   - 交易记录保存
   - 合规性要求

---

## 🎯 期望从外部 AI 获得

### 1. 工单 #011 实施方案 (最重要！)
- 详细的 MT5 API 集成架构设计
- 连接池设计和实现方案
- 订单执行器的最佳实践
- 错误处理和异常恢复机制
- 具体的代码实现框架

### 2. 风险管理系统设计
- Kelly 公式在实盘的安全使用
- 最大仓位和风险限制
- 断路器机制设计
- 止损止盈逻辑

### 3. 监控告警方案
- MT5 连接监控指标
- 订单执行监控指标
- 交易延迟监控
- Prometheus + Grafana 配置

### 4. 测试策略
- 单元测试方案
- 集成测试方案
- 压力测试设计
- 实盘模拟测试流程

### 5. 代码质量改进
- 当前代码的优势和劣势
- 具体的改进建议
- 重构优先级
- 技术债务评估

### 6. 性能优化
- 特征计算性能
- 订单执行延迟
- 内存优化
- 并发处理

---

## 📁 关键文件和目录

### 核心代码
```
src/
├── strategy/
│   └── risk_manager.py          # Kelly 公式资金管理 ⭐
├── feature_engineering/
│   ├── basic_features.py        # 35 个基础特征 ⭐
│   ├── advanced_features.py     # 40 个高级特征 ⭐
│   └── labeling.py              # 三重障碍标签法
├── monitoring/
│   └── dq_score.py              # 数据质量监控
└── models/
    ├── trainer.py               # XGBoost 训练
    └── evaluator.py             # 模型评估
```

### 关键脚本
```
bin/
├── run_backtest.py              # 回测执行 ⭐
└── train_ml_model.py            # 模型训练

根目录/
├── nexus_with_proxy.py          # AI 协同监控 ⭐
├── gemini_review_bridge.py      # Gemini Pro 集成 ⭐
└── update_notion_from_git.py    # Git-Notion 同步
```

### 关键文档
```
docs/
├── QUICK_START.md               # 快速开始
├── HOW_TO_USE_GEMINI_REVIEW.md  # Gemini 使用指南
├── ML_ADVANCED_GUIDE.md         # 机器学习指南
└── BACKTEST_GUIDE.md            # 回测指南
```

---

## 🚀 技术亮点

### 1. 事件驱动架构
- 检查点机制支持断点续传
- Git Hooks 自动触发 Notion 更新
- 知识自动沉淀

### 2. 分数差分技术
- 机器学习友好的平稳化
- 保持记忆性的同时去趋势
- 原创实现

### 3. 三重障碍标签法
- 科学的样本标注方法
- 同时考虑收益、时间、止损
- Meta-Labeling 支持

### 4. 五维质量评分
- 完整性、准确性、一致性、及时性、有效性
- Prometheus 导出
- Grafana 可视化

### 5. Numba + Dask 优化
- 生产级性能优化
- 5-10x 加速
- 支持大规模数据

### 6. 双 AI 协同
- Claude Sonnet 4.5 (开发)
- Gemini Pro (审查)
- GitHub-Notion 自动同步

---

## 📊 项目健康度

| 维度 | 评分 | 说明 |
|------|------|------|
| 代码质量 | 8/10 | 架构清晰，需改进错误处理 |
| 文档完整 | 9/10 | 非常完善 |
| 测试覆盖 | 7/10 | 单元测试充分，缺集成测试 |
| 性能表现 | 8/10 | 优化良好 |
| 自动化度 | 10/10 | 极高 |
| 监控完善 | 6/10 | 基础就绪，需扩展 |

**总体评分**: 8/10

---

**这份汇总提供了项目的完整视图，供外部 AI 深入分析。**

"""

        filename = f"{self.export_dir}/CONTEXT_SUMMARY_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"   ✅ 上下文汇总已生成: CONTEXT_SUMMARY_{self.timestamp}.md")
        return summary

    def _generate_ai_prompt(self, summary):
        """生成 AI 提示词"""
        prompt = f"""# 🤖 MT5-CRS 项目外部 AI 深度评估请求

你是一位资深的量化交易系统和 Python 开发专家。

---

## 📋 评估对象

**项目名称**: MT5-CRS 量化交易系统
**当前阶段**: 工单 #011 - MT5 实盘交易系统对接
**生成时间**: {datetime.now().isoformat()}

---

## 📦 提供的上下文文件

你将获得以下完整的项目上下文：

1. **CONTEXT_SUMMARY.md** - 项目快速概览 ⭐ 建议先读
2. **git_history.md** - Git 提交历史和分支信息
3. **project_structure.md** - 完整的项目目录结构
4. **core_files.md** - 关键代码文件完整内容
5. **documents.md** - 重要文档

**总上下文规模**:
- 文件数: 5 个
- 代码行数: ~10,000 行
- 文档字数: ~50,000 字
- 预计 Token: ~70,000 tokens

---

## 🎯 评估请求

请进行以下 **7 个维度** 的深度评估：

### 1️⃣ 项目状态评估 (预计 10 分钟)

请评估：
- **整体进展**: 当前项目到什么阶段了？
- **完成质量**: 已完成工单的质量如何？
- **当前问题**: 最突出的 3 个问题是什么？
- **时间预估**: 工单 #011 需要多少时间？合理性如何？

**输出格式**:
```markdown
## 1. 项目状态评估

### 整体进展
[评分: X/10]
[详细分析]

### 完成质量
[评分: X/10]
[详细分析]

### 当前TOP 3问题
1. [问题1]
2. [问题2]
3. [问题3]

### 时间预估
- 合理时间: X 天
- 风险缓冲: X 天
```

---

### 2️⃣ 工单 #011 实施方案 (预计 30 分钟) ⭐ 最重要

请设计详细的 MT5 API 集成方案：

#### A. 架构设计
- MT5 连接池设计 (多连接、健康检查、自动重连)
- 订单执行架构 (异步处理、状态跟踪、错误处理)
- 状态管理方案 (连接状态、订单状态、仓位状态)
- 错误处理机制 (重试策略、降级方案、告警)

#### B. 具体实施步骤
请提供 **5-7 个步骤**，每个步骤包含：
- 步骤名称
- 预计时间 (天数)
- 难度 (低/中/高)
- 关键技术点
- 风险点

#### C. 代码框架设计
请提供以下文件的伪代码或实现框架：

```python
# src/mt5/connection.py
class MT5ConnectionPool:
    def __init__(self, pool_size=3):
        # 连接池初始化
        pass

    def get_connection(self):
        # 获取健康连接
        pass

    def reconnect(self, connection):
        # 重连机制
        pass

# src/mt5/order_executor.py
class OrderExecutor:
    def __init__(self, connection_pool):
        pass

    async def execute_market_order(self, symbol, volume, side):
        # 市价单执行
        pass

    async def execute_limit_order(self, symbol, volume, price, side):
        # 限价单执行
        pass

# src/mt5/position_manager.py
class PositionManager:
    def __init__(self):
        pass

    def get_current_positions(self):
        # 获取当前仓位
        pass

    def calculate_position_size(self, signal, account_balance):
        # 计算仓位大小 (集成 Kelly 公式)
        pass

# src/mt5/risk_controller.py
class RiskController:
    def __init__(self):
        pass

    def check_order_risk(self, order):
        # 订单风险检查
        pass

    def should_circuit_break(self):
        # 断路器检查
        pass
```

**输出格式**:
```markdown
## 2. 工单 #011 实施方案

### A. 架构设计
[详细设计]

### B. 实施步骤
步骤1: [名称]
- 时间: X 天
- 难度: [低/中/高]
- 关键点: [...]
- 风险: [...]

[继续其他步骤]

### C. 代码框架
[提供完整的代码框架]
```

---

### 3️⃣ 风险识别与缓解 (预计 20 分钟)

识别并提供缓解方案：

#### 技术风险 (至少 5 个)
- MT5 API 连接稳定性
- 网络中断和断线重连
- 订单执行延迟和滑点
- 内存泄漏和资源管理
- [其他你识别的风险]

#### 业务风险 (至少 3 个)
- 策略失效风险
- 资金安全风险
- 监管合规风险

#### 缓解方案
对每个风险，提供：
- 风险等级 (低/中/高/严重)
- 影响范围
- 缓解方案 (代码级 + 架构级 + 操作级)
- 监控指标

**输出格式**:
```markdown
## 3. 风险识别与缓解

### 技术风险
1. [风险名称]
   - 等级: [高]
   - 影响: [...]
   - 缓解: [具体方案]
   - 监控: [具体指标]

[继续其他风险]

### 业务风险
[同上]
```

---

### 4️⃣ 代码质量评估 (预计 15 分钟)

基于提供的核心代码文件，评估：

#### 优势 (至少 5 个)
- 当前代码做得好的地方
- 设计模式的应用
- 代码可读性
- 性能优化
- [其他优势]

#### 缺陷 (至少 5 个)
- 需要改进的地方
- 潜在的 bug
- 设计缺陷
- 性能问题
- [其他缺陷]

#### 改进方案 (优先级排序)
- 高优先级 (P0): 必须立即修复
- 中优先级 (P1): 建议短期修复
- 低优先级 (P2): 可以逐步改进

**输出格式**:
```markdown
## 4. 代码质量评估

### 优势 (评分: X/10)
1. [优势1] - [详细说明]
2. [优势2] - [详细说明]
...

### 缺陷 (评分: X/10)
1. [缺陷1] - [详细说明 + 改进建议]
2. [缺陷2] - [详细说明 + 改进建议]
...

### 改进优先级
#### P0 (必须)
- [项目1]: [改进方案]

#### P1 (建议)
- [项目2]: [改进方案]

#### P2 (可选)
- [项目3]: [改进方案]
```

---

### 5️⃣ 技术债务评估 (预计 10 分钟)

识别项目中的技术债务：

| 债务项目 | 影响程度 (低/中/高) | 偿还难度 (低/中/高) | 优先级 (P0/P1/P2) | 改进方案 |
|---------|-------------------|-------------------|-------------------|---------|
| ? | ? | ? | ? | ? |

**特别关注**:
- 代码重复
- 硬编码配置
- 缺失的错误处理
- 测试覆盖不足
- 文档过时
- 性能瓶颈

**输出格式**:
```markdown
## 5. 技术债务评估

[完整的技术债务表格]

### 偿还计划
#### 第一阶段 (本周)
- [债务1]: [偿还方案]

#### 第二阶段 (本月)
- [债务2]: [偿还方案]

#### 第三阶段 (下月)
- [债务3]: [偿还方案]
```

---

### 6️⃣ 性能优化建议 (预计 10 分钟)

针对以下方面提供优化建议：

- **特征计算性能**: 当前 Numba JIT 优化是否足够？
- **订单执行延迟**: 如何降到 < 100ms？
- **内存优化**: 大数据集处理的内存管理
- **并发处理**: 多品种并行交易的设计

**每个建议包含**:
- 当前问题
- 优化方案
- 预期提升
- 实现难度

**输出格式**:
```markdown
## 6. 性能优化建议

### 特征计算优化
- 当前状态: [...]
- 优化方案: [...]
- 预期提升: [X%]
- 难度: [低/中/高]

[继续其他方面]
```

---

### 7️⃣ 测试策略设计 (预计 10 分钟)

为 MT5 实盘系统设计全面的测试策略：

#### 单元测试
- 测试什么？
- 如何 Mock MT5 API？
- 关键测试用例

#### 集成测试
- 测试流程
- 环境配置
- 验收标准

#### 压力测试
- 测试场景 (高频交易、网络延迟、断线重连)
- 性能指标
- 通过标准

#### 实盘模拟测试
- 测试流程
- 小额测试方案
- 风险控制

**输出格式**:
```markdown
## 7. 测试策略设计

### 单元测试
[详细方案]

### 集成测试
[详细方案]

### 压力测试
[详细方案]

### 实盘模拟测试
[详细方案]
```

---

## 📊 最终输出要求

请按以下格式输出完整报告：

```markdown
# MT5-CRS 工单 #011 外部 AI 深度评估报告

**评估 AI**: [Gemini Pro / Claude / ChatGPT / 其他]
**评估时间**: [时间戳]
**上下文版本**: {self.timestamp}

---

## 🎯 执行摘要

[3-5 句话总结核心观点和建议]

**核心建议 TOP 3**:
1. [建议1]
2. [建议2]
3. [建议3]

---

## 📊 评估详情

### 1. 项目状态评估
[完整内容]

### 2. 工单 #011 实施方案 ⭐
[完整内容]

### 3. 风险识别与缓解
[完整内容]

### 4. 代码质量评估
[完整内容]

### 5. 技术债务评估
[完整内容]

### 6. 性能优化建议
[完整内容]

### 7. 测试策略设计
[完整内容]

---

## 🎓 学习建议

推荐阅读的资源：
- [资源1]
- [资源2]

---

## 📋 快速行动清单

**今天可以做**:
- [ ] [任务1]
- [ ] [任务2]

**本周完成**:
- [ ] [任务3]
- [ ] [任务4]

**本月目标**:
- [ ] [任务5]
- [ ] [任务6]

---

## 📈 成功指标

如何衡量工单 #011 的成功？

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| 订单执行成功率 | > 95% | [方法] |
| 平均订单延迟 | < 100ms | [方法] |
| Kelly 公式准确性 | 100% | [方法] |
| 系统可用性 | > 99% | [方法] |

---

## 💡 额外建议

[任何其他有价值的建议]

---

**🏆 评估完成度自评**:
- 内容覆盖: X%
- 细节深度: X%
- 实用价值: X%
```

---

## ⏱️ 预计审查时间

- **快速审查**: 30 分钟 (仅核心部分)
- **标准审查**: 60 分钟 (7 个维度基础评估)
- **深度审查**: 90 分钟 (完整详细评估) ⭐ 推荐

---

## 🔗 相关资源

### Notion 数据库
- 主知识库: [URL]
- AI Command Center: [URL]
- Issues: [URL]
- Knowledge Graph: [URL]

### GitHub
- 本地仓库: /opt/mt5-crs

---

## 💬 反馈方式

完成评估后，请：

1. **保存完整报告** - 不要省略任何部分
2. **包含代码示例** - 尽可能具体
3. **明确优先级** - P0/P1/P2 标注
4. **提供行动清单** - 今天/本周/本月

---

**感谢你的深入分析！这将对 MT5-CRS 项目的下一阶段至关重要。** 🙏

---

*生成时间: {datetime.now().isoformat()}*
*上下文版本: {self.timestamp}*

"""

        filename = f"{self.export_dir}/AI_PROMPT_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"   ✅ AI 提示词已生成: AI_PROMPT_{self.timestamp}.md")
        return prompt

    def _create_index(self, git_context, structure, core_files, docs, summary, prompt):
        """创建索引文件"""
        index = f"""# 📦 MT5-CRS 项目上下文包

**生成时间**: {datetime.now().isoformat()}
**版本**: {self.timestamp}

---

## 🎯 快速开始

### 第 1 步：选择外部 AI平台
- ✅ Gemini Pro (推荐)
- ✅ Claude (推荐)
- ✅ ChatGPT
- ✅ 其他 LLM

### 第 2 步：复制提示词
1. 打开 `AI_PROMPT_{self.timestamp}.md` ⭐
2. 复制全部内容
3. 粘贴到 AI 对话框

### 第 3 步：提供上下文文件
- 告诉 AI 你有完整的项目上下文
- AI 会引导你提供需要的文件
- 或者直接粘贴其他文件内容

### 第 4 步：获取深度评估
- 等待 60-90 分钟
- AI 会提供完整的评估报告
- 保存结果到 `exports/ai_reviews/`

---

## 📄 包内容清单

### 1. AI_PROMPT_{self.timestamp}.md ⭐ 最重要
**用途**: 复制到外部 AI 的提示词

**包含**:
- 项目背景说明
- 7 个评估维度的详细要求
- 输出格式规范
- 预计时间和成功指标

**大小**: ~15KB

---

### 2. CONTEXT_SUMMARY_{self.timestamp}.md
**用途**: 项目快速概览

**包含**:
- 项目统计数据
- 工单进度 (#008-#011)
- 技术栈完整列表
- 当前痛点与挑战
- 期望从 AI 获得的帮助

**大小**: ~8KB

---

### 3. git_history_{self.timestamp}.md
**用途**: Git 提交历史

**包含**:
- 当前分支信息
- 最近 30 条提交
- 分支列表
- 最新提交完整信息

**大小**: ~10KB

---

### 4. project_structure_{self.timestamp}.md
**用途**: 项目目录结构

**包含**:
- 完整的目录树
- 关键文件位置
- 模块组织方式

**大小**: ~8KB

---

### 5. core_files_{self.timestamp}.md
**用途**: 核心代码文件

**包含**:
- risk_manager.py (Kelly 公式)
- basic_features.py (基础特征)
- advanced_features.py (高级特征)
- labeling.py (三重障碍标签)
- nexus_with_proxy.py (AI 协同)
- gemini_review_bridge.py (Gemini 集成)
- run_backtest.py (回测系统)

**大小**: ~150KB

---

### 6. documents_{self.timestamp}.md
**用途**: 项目文档

**包含**:
- QUICK_START.md
- HOW_TO_USE_GEMINI_REVIEW.md
- WORK_ORDER_010.9_FINAL_SUMMARY.md
- GEMINI_SYSTEM_SUMMARY.md

**大小**: ~100KB

---

### 7. README.md (本文件)
**用途**: 使用说明

---

## 📊 统计信息

- **文件总数**: 7 个
- **总大小**: ~290KB
- **预计 Token**: ~70,000 tokens
- **适用性**: 适合大多数 LLM (上下文窗口 > 100K)

---

## 🚀 使用步骤

### 方案 A: 一次性传输所有上下文

1. 打开外部 AI (Gemini Pro / Claude / ChatGPT)
2. 新建对话
3. 粘贴 `AI_PROMPT_{self.timestamp}.md` 的全部内容
4. 告诉 AI: "我有完整的项目上下文文件，需要时请告诉我"
5. AI 会分析并询问需要的文件
6. 按需粘贴其他文件内容

**优点**: 最简单，AI 会引导你
**适用**: 所有 AI 平台

---

### 方案 B: 分步骤传输 (如果有 Token 限制)

1. 先发送 `AI_PROMPT_{self.timestamp}.md`
2. 等待 AI 确认理解
3. 发送 `CONTEXT_SUMMARY_{self.timestamp}.md`
4. 发送 `core_files_{self.timestamp}.md`
5. 发送 `documents_{self.timestamp}.md`
6. 按需发送其他文件

**优点**: 避免超过 Token 限制
**适用**: Token 限制较严格的平台

---

### 方案 C: 多 AI 协同 (推荐！)

同时发送给多个 AI 平台，获得不同视角：

#### Gemini Pro
- 优势: 技术深度、架构设计
- 适合: 工单实施方案、代码框架

#### Claude
- 优势: 代码质量、最佳实践
- 适合: 代码审查、重构建议

#### ChatGPT
- 优势: 实用建议、快速迭代
- 适合: 快速行动清单、测试策略

**然后综合所有反馈做决策！**

---

## 💡 最佳实践

### 1. 提供完整上下文
- 不要省略文件
- 让 AI 看到完整的代码
- 这样才能获得深度建议

### 2. 明确评估重点
- 在 AI_PROMPT 基础上
- 可以强调你最关心的部分
- 例如: "请特别关注 MT5 连接稳定性"

### 3. 要求具体建议
- 不满意抽象的建议
- 要求提供代码示例
- 要求给出实施步骤

### 4. 保存完整结果
- 将 AI 的评估完整保存
- 建议保存位置: `exports/ai_reviews/gemini_review_{datetime.now().strftime("%Y%m%d")}.md`
- 可以多次参考

---

## ⏱️ 预计时间

| 步骤 | 时间 |
|------|------|
| 准备上下文文件 | 已完成 |
| 选择 AI 平台 | 1 分钟 |
| 复制粘贴提示词 | 2 分钟 |
| 等待 AI 分析 | 60-90 分钟 |
| 保存结果 | 5 分钟 |
| **总计** | **~70-100 分钟** |

---

## 🎯 预期结果

完成后你将获得：

### 1. 完整的工单 #011 实施方案
- 详细的架构设计
- 具体的实施步骤 (5-7 步)
- 代码框架和示例
- 时间和难度估算

### 2. 全面的风险评估
- 技术风险 (5+)
- 业务风险 (3+)
- 每个风险的缓解方案
- 监控指标建议

### 3. 深入的代码质量分析
- 优势 (5+)
- 缺陷 (5+)
- 改进优先级 (P0/P1/P2)

### 4. 技术债务清单
- 完整的债务列表
- 偿还优先级
- 具体改进方案

### 5. 性能优化建议
- 特征计算优化
- 订单执行优化
- 内存优化
- 并发处理优化

### 6. 测试策略
- 单元测试方案
- 集成测试方案
- 压力测试方案
- 实盘模拟测试方案

### 7. 快速行动清单
- 今天可以做的
- 本周完成的
- 本月目标

---

## ❓ 常见问题

### Q: 为什么要手动传输？
**A**: 避免 API 限制 (429 错误)，获得更深入的分析，可以多个 AI 协同。

### Q: 需要多长时间？
**A**: 通常 60-90 分钟，取决于 AI 和你的网络速度。深度审查更有价值。

### Q: 结果准确性如何？
**A**: 基于完整的项目上下文，通常比自动 API 调用更准确和深入。

### Q: 可以重复使用吗？
**A**: 可以！多次发给不同 AI，或者项目更新后重新生成上下文包。

### Q: 如何选择 AI 平台？
**A**: 建议都试试，综合建议。Gemini Pro 和 Claude 通常更专业。

---

## 📁 保存结果

建议将 AI 的评估报告保存到：

```
exports/ai_reviews/
├── gemini_review_{datetime.now().strftime("%Y%m%d")}.md
├── claude_review_{datetime.now().strftime("%Y%m%d")}.md
└── chatgpt_review_{datetime.now().strftime("%Y%m%d")}.md
```

然后可以使用导入工具：
```bash
python3 import_ai_review.py exports/ai_reviews/gemini_review_*.md
```

---

## 🔗 相关资源

### Notion 数据库
- **主知识库**: https://www.notion.so/...
- **AI Command Center**: https://www.notion.so/...
- **Issues**: https://www.notion.so/...
- **Knowledge Graph**: https://www.notion.so/...

### 本地工具
- **生成上下文**: `python3 export_context_for_ai.py`
- **导入评估**: `python3 import_ai_review.py`
- **检查状态**: `python3 check_sync_status.py`

---

## 🏆 成功指标

完成这次外部 AI 协同后，你应该能够：

- ✅ 理解工单 #011 的完整实施方案
- ✅ 知道具体的开发步骤和时间
- ✅ 识别所有主要风险和缓解方案
- ✅ 获得代码改进的优先级清单
- ✅ 有清晰的今天/本周/本月行动清单
- ✅ 对项目的下一阶段充满信心

---

**准备好了？开始与外部 AI 深度协同吧！** 🚀

---

*生成时间: {datetime.now().isoformat()}*
*版本: {self.timestamp}*
*工具: export_context_for_ai.py*

"""

        filename = f"{self.export_dir}/README.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(index)

        print(f"   ✅ README 已生成: README.md")

if __name__ == "__main__":
    print()
    print("🤖 MT5-CRS 项目上下文导出工具")
    print("供外部 AI (Gemini Pro / Claude / ChatGPT) 深度分析")
    print()

    exporter = ContextExporter()
    export_dir = exporter.export_all()

    print(f"📂 所有文件已导出到: {export_dir}")
    print()
    print("🎯 下一步:")
    print(f"1. cd {export_dir}")
    print("2. cat README.md  # 阅读使用说明")
    print("3. 复制 AI_PROMPT_*.md 到外部 AI")
    print("4. 等待深度评估 (60-90 分钟)")
    print("5. 保存结果并开始实施！")
    print()

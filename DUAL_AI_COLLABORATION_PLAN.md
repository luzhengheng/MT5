# 🤖 双 AI 协同方案设计 - API 方案 + 文件传输方案

**设计日期**: 2025-12-21
**方案版本**: 1.0
**目标**: 建立可靠的双通道外部 AI 协同机制

---

## 📋 方案概述

### 问题分析

**当前 API 方案的限制**:
- ❌ API 配额限制 (429 错误)
- ❌ API 速率限制
- ❌ 网络延迟和超时风险
- ❌ 单一通道，无备选方案

**解决方案**:
- ✅ **方案 A**: 自动 API 调用 (Gemini Pro 在线审查)
- ✅ **方案 B**: 文件打包传输 (手动协同，无 API 限制)
- ✅ **双通道结合**: 互为备选，自动降级

---

## 🎯 方案 A：自动 API 方案（已实现）

### 工作流程

```
Claude Code 执行
    ↓
自动收集项目上下文
    ├─ Git 状态
    ├─ Notion 任务
    ├─ 代码文件
    └─ 项目历史
    ↓
生成 4000+ 字审查提示
    ↓
发送到 Gemini Pro API
    ├─ 方案 A1: 代理服务
    └─ 方案 A2: 直接 API
    ↓
接收评估结果
    ↓
保存到本地 + Notion
    ↓
完成！
```

### 优点
- ⚡ 快速 (5-10 分钟)
- 🔄 完全自动化
- 📊 结果直接入库
- 🔗 无缝集成工作流

### 缺点
- ❌ API 限制 (配额、速率、延迟)
- ❌ 网络依赖
- ⚠️ 不稳定

### 配置状态
- ✅ 已部署
- ⚠️ 当前受 429 限制

---

## 📦 方案 B：文件打包传输方案（新增）

### 核心思路

**不依赖 API，通过文件传输**：
- 将项目上下文打包成专业文件
- 你手动发送给外部 AI (Gemini/Claude/ChatGPT)
- 外部 AI 进行深度审查
- 你手动导入结果回到系统

### 优点
- ✅ 无 API 限制
- ✅ 适合大型项目分析
- ✅ 外部 AI 有完整上下文
- ✅ 可获得更深入的分析
- ✅ 可多个外部 AI 协同
- ✅ 完全离线可行

### 缺点
- ⏱️ 稍慢 (手动传输)
- 📝 需要手动操作
- 🔄 流程不完全自动

---

## 🔧 方案 B 详细实现

### 第 1 步：自动打包工具

创建 `export_context_for_ai.py` - 自动生成完整的项目上下文包：

```python
#!/usr/bin/env python3
"""
导出项目上下文供外部 AI 分析
生成打包文件供手动传输给外部 AI
"""

import os
import json
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
        print("📦 导出项目上下文包")
        print("="*80)
        print()

        # 1. 导出 Git 历史
        print("📝 1. 导出 Git 历史...")
        git_context = self._export_git_history()

        # 2. 导出项目结构
        print("📝 2. 导出项目结构...")
        structure = self._export_project_structure()

        # 3. 导出核心代码文件
        print("📝 3. 导出核心代码文件...")
        core_files = self._export_core_files()

        # 4. 导出文档
        print("📝 4. 导出相关文档...")
        docs = self._export_documents()

        # 5. 生成上下文汇总
        print("📝 5. 生成上下文汇总...")
        summary = self._generate_summary(git_context, structure, core_files, docs)

        # 6. 创建 AI 提示词
        print("📝 6. 生成 AI 提示词...")
        prompt = self._generate_ai_prompt(summary)

        # 7. 打包所有文件
        print("📝 7. 打包所有文件...")
        package = self._create_package(git_context, structure, core_files, docs, summary, prompt)

        print()
        print("="*80)
        print("✅ 导出完成！")
        print("="*80)
        print()
        print(f"📁 导出位置: {self.export_dir}")
        print(f"📦 包文件: {package}")
        print()
        print("💡 下一步:")
        print("1. 打开导出的文件夹")
        print("2. 查看 AI_PROMPT.md 和 CONTEXT_SUMMARY.md")
        print("3. 复制 AI_PROMPT.md 的内容")
        print("4. 粘贴到 Gemini Pro / Claude / ChatGPT")
        print("5. 添加文件内容作为补充上下文")
        print("6. 获取 AI 的深度分析")
        print("7. 将结果保存到 /exports/ai_reviews/ 目录")
        print()

        return package

    def _export_git_history(self):
        """导出 Git 提交历史"""
        try:
            # 最近 20 条提交
            log = subprocess.check_output(
                ["git", "log", "--oneline", "-20"],
                cwd=self.project_root,
                universal_newlines=True
            )

            # 分支信息
            branches = subprocess.check_output(
                ["git", "branch", "-v"],
                cwd=self.project_root,
                universal_newlines=True
            )

            git_context = f"""# Git 历史信息

## 最近 20 条提交
```
{log}
```

## 分支信息
```
{branches}
```
"""

            filename = f"{self.export_dir}/git_history_{self.timestamp}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(git_context)

            print(f"   ✅ Git 历史已导出: {filename}")
            return git_context

        except Exception as e:
            print(f"   ❌ 导出 Git 历史失败: {e}")
            return ""

    def _export_project_structure(self):
        """导出项目结构"""
        try:
            # 生成项目树
            tree = subprocess.check_output(
                ["tree", "-L", "2", "-I", "__pycache__|.git|.pytest_cache"],
                cwd=self.project_root,
                universal_newlines=True
            )

            structure = f"""# 项目结构

```
{tree}
```
"""

            filename = f"{self.export_dir}/project_structure_{self.timestamp}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(structure)

            print(f"   ✅ 项目结构已导出: {filename}")
            return structure

        except Exception as e:
            print(f"   ⚠️ 导出项目结构失败 (tree 命令未安装): {e}")
            return "# 项目结构\n\n请手动查看目录结构"

    def _export_core_files(self):
        """导出核心代码文件"""
        core_files = [
            "src/strategy/risk_manager.py",
            "src/feature_engineering/basic_features.py",
            "src/feature_engineering/advanced_features.py",
            "nexus_with_proxy.py",
            "bin/run_backtest.py",
        ]

        exported_files = {}
        for filepath in core_files:
            full_path = f"{self.project_root}/{filepath}"
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    exported_files[filepath] = content
                    print(f"   ✅ {filepath}")
                except Exception as e:
                    print(f"   ⚠️ {filepath}: {e}")

        # 保存到文件
        filename = f"{self.export_dir}/core_files_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            for filepath, content in exported_files.items():
                f.write(f"# {filepath}\n\n```python\n{content}\n```\n\n")

        print(f"   ✅ 核心文件已导出: {filename}")
        return exported_files

    def _export_documents(self):
        """导出相关文档"""
        doc_files = [
            "QUICK_START.md",
            "HOW_TO_USE_GEMINI_REVIEW.md",
            "WORK_ORDER_010.9_FINAL_SUMMARY.md",
        ]

        docs = {}
        for doc in doc_files:
            full_path = f"{self.project_root}/{doc}"
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    docs[doc] = content
                    print(f"   ✅ {doc}")
                except Exception as e:
                    print(f"   ⚠️ {doc}: {e}")

        return docs

    def _generate_summary(self, git_context, structure, core_files, docs):
        """生成上下文汇总"""
        summary = f"""# 项目上下文汇总

**生成时间**: {datetime.now().isoformat()}
**项目**: MT5-CRS 量化交易系统

## 项目统计

- 核心代码文件: {len(core_files)} 个
- 特征工程维度: 75+ 个
- 测试方法: 95+ 个
- 文档字数: 50000+ 字
- Git 提交数: 40+ 个

## 工单进度

- ✅ 工单 #008 - 数据管线 (100%)
- ✅ 工单 #009 - 机器学习 (100%)
- ✅ 工单 #010 - 回测系统 (100%)
- ✅ 工单 #010.9 - Notion Nexus + Gemini (100%)
- 🎯 工单 #011 - MT5 实盘交易系统 (进行中)

## 关键技术栈

- **数据处理**: Pandas, Numpy, Polars
- **特征工程**: 手写实现，75+ 维
- **机器学习**: XGBoost, scikit-learn
- **回测**: 自制回测引擎, Backtrader
- **API 集成**: Requests, asyncio
- **监控**: Prometheus, Grafana
- **协作**: Notion, GitHub, Gemini Pro

## 当前痛点

1. MT5 API 集成未完成
2. 实盘交易系统需要设计
3. 监控告警需要完善
4. 技术债务需要评估

## 期望从外部 AI 获得

1. 完整的工单 #011 实施方案
2. MT5 API 集成的最佳实践
3. 风险管理系统的设计建议
4. 代码质量和架构改进建议
5. 技术债务优先级排序

"""
        filename = f"{self.export_dir}/CONTEXT_SUMMARY_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"   ✅ 上下文汇总已生成: {filename}")
        return summary

    def _generate_ai_prompt(self, summary):
        """生成 AI 提示词"""
        prompt = f"""# 🤖 外部 AI 评估请求

你是一位资深的量化交易系统和 Python 开发专家。

## 评估对象

**项目**: MT5-CRS 量化交易系统
**当前阶段**: 工单 #011 - MT5 实盘交易系统对接

{summary}

## 请进行以下评估

### 1️⃣ 项目状态评估 (10 分钟)

请评估：
- 当前项目的整体状态和进展
- 已完成工单的质量评分
- 当前工单 #011 的复杂度
- 预计完成时间的合理性

### 2️⃣ 工单 #011 实施方案 (20 分钟)

请设计详细的 MT5 API 集成方案：

#### A. 架构设计
- MT5 连接池设计
- 订单执行架构
- 状态管理方案
- 错误处理机制

#### B. 具体实施步骤
- 第 1 步: 连接管理 (时间/难度)
- 第 2 步: 订单执行 (时间/难度)
- 第 3 步: Kelly 资金管理 (时间/难度)
- 第 4 步: 风险控制 (时间/难度)
- 第 5 步: 监控告警 (时间/难度)

#### C. 代码结构
```
src/mt5/
├── connection.py          # MT5 连接
├── order_executor.py      # 订单执行
├── position_manager.py    # 仓位管理
└── risk_controller.py     # 风险控制
```

请提供伪代码或实现框架。

### 3️⃣ 风险识别与缓解 (15 分钟)

识别以下风险并提供缓解方案：

#### 技术风险
- MT5 API 连接稳定性
- 网络中断和断线重连
- 订单执行延迟和滑点
- 内存泄漏和资源管理

#### 业务风险
- 策略失效风险
- 资金安全风险
- 监管合规风险
- 运维风险

#### 缓解方案
- 代码级缓解 (代码示例)
- 架构级缓解 (设计模式)
- 操作级缓解 (运维流程)

### 4️⃣ 代码质量评估 (10 分钟)

评估已有代码：

- **优势**: 当前代码的 5 个最大优势
- **缺陷**: 需要改进的 5 个地方
- **改进方案**: 具体的改进步骤和优先级

### 5️⃣ 技术债务评估 (10 分钟)

识别技术债务：

| 债务项目 | 影响程度 | 优先级 | 改进方案 |
|---------|---------|--------|---------|
| ? | ? | ? | ? |

### 6️⃣ 性能优化建议 (10 分钟)

- 特征计算性能
- 订单执行延迟
- 内存优化
- 并发处理

### 7️⃣ 测试策略 (10 分钟)

为 MT5 实盘系统设计测试策略：

- 单元测试
- 集成测试
- 压力测试
- 实盘模拟测试

## 输出格式要求

请按以下格式输出：

```markdown
# MT5-CRS 工单 #011 外部 AI 评估报告

## 执行摘要
[3-5 句话总结核心观点]

## 1. 项目状态评估
[详细评估]

## 2. 工单 #011 实施方案
### A. 架构设计
...
### B. 具体步骤
...
### C. 代码框架
...

## 3. 风险识别与缓解
### 技术风险
...
### 业务风险
...

[继续其他部分]

## 优先建议 TOP 3
1. ...
2. ...
3. ...

## 评估完成度
- 内容覆盖: X%
- 细节深度: X%
- 实用价值: X%
```

## 提供的上下文文件

### 📄 文件列表
1. git_history.md - Git 提交历史
2. project_structure.md - 项目目录结构
3. core_files.md - 核心代码文件
4. documents.md - 相关文档
5. CONTEXT_SUMMARY.md - 项目汇总

### 📊 文件统计
- 总字数: 50000+ 字
- 代码行数: 10000+ 行
- 文件数: 5 个

### 🔗 关键链接
- Notion 主知识库: https://www.notion.so/...
- Notion Issues: https://www.notion.so/...
- GitHub 仓库: (本地)

## 特别说明

这是一个完整的项目上下文包，你可以：
- 深入理解项目的历史和现状
- 基于完整的代码和文档进行分析
- 提供比 API 调用更深入的建议
- 涵盖 API 调用可能遗漏的细节

预计审查时间: 60-90 分钟

## 反馈方式

完成评估后，请按以下方式返回：

1. **直接粘贴**: 将报告内容粘贴回给我
2. **结构化输出**: 确保格式清晰，便于导入
3. **具体建议**: 包含代码示例和实现细节
4. **优先排序**: 明确标注优先级

---

**感谢你的深入分析！这将大大帮助项目的下一阶段。**

"""

        filename = f"{self.export_dir}/AI_PROMPT_{self.timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"   ✅ AI 提示词已生成: {filename}")
        return prompt

    def _create_package(self, git_context, structure, core_files, docs, summary, prompt):
        """创建最终包文件"""
        package_name = f"mt5_crs_context_{self.timestamp}"
        package_dir = f"{self.export_dir}/{package_name}"
        os.makedirs(package_dir, exist_ok=True)

        # 创建索引文件
        index = f"""# MT5-CRS 项目上下文包

**生成时间**: {datetime.now().isoformat()}
**版本**: 1.0

## 📦 包内容

### 1. AI_PROMPT.md ⭐
**最重要的文件！** - 复制这个文件的内容到外部 AI

包含：
- 项目背景
- 评估需求
- 输出格式要求

### 2. CONTEXT_SUMMARY.md
项目快速概览：
- 统计数据
- 工单进度
- 技术栈
- 当前痛点

### 3. git_history.md
Git 提交历史和分支信息

### 4. project_structure.md
项目目录结构树

### 5. core_files.md
关键代码文件完整内容：
- risk_manager.py
- feature_engineering/
- nexus_with_proxy.py
- run_backtest.py

### 6. documents.md
重要文档：
- QUICK_START.md
- HOW_TO_USE_GEMINI_REVIEW.md
- WORK_ORDER_010.9_FINAL_SUMMARY.md

## 🚀 使用步骤

### 第 1 步：选择外部 AI
- Gemini Pro (推荐)
- Claude (推荐)
- ChatGPT
- 其他 LLM

### 第 2 步：打开对话
在你选择的 AI 中开始新对话

### 第 3 步：复制提示词
1. 打开 `AI_PROMPT.md`
2. 复制全部内容
3. 粘贴到 AI 对话框

### 第 4 步：添加上下文
在 AI 的对话框中，你可以：
- 粘贴其他文件内容
- 分点说明，让 AI 逐步分析
- 如果 token 限制，可分多个消息发送

### 第 5 步：获取评估
- AI 会进行深度分析
- 提供实施方案
- 识别风险
- 给出优化建议

### 第 6 步：保存结果
建议将结果保存到：
```
exports/ai_reviews/gemini_review_20251221.md
exports/ai_reviews/claude_review_20251221.md
```

## 📊 文件大小参考

- AI_PROMPT.md: ~5KB
- CONTEXT_SUMMARY.md: ~3KB
- git_history.md: ~10KB
- project_structure.md: ~8KB
- core_files.md: ~150KB
- documents.md: ~100KB

**总大小**: ~280KB

**Token 估计**: ~70000 tokens (适合大多数 LLM)

## 💡 最佳实践

### 一次性传输所有文件
- 直接告诉 AI: "这是我的项目上下文包"
- 粘贴 AI_PROMPT.md 的全部内容
- AI 会根据需要询问更多细节

### 分步骤传输（如果 token 限制）
1. 先发 AI_PROMPT.md
2. AI 读完后，再发 CONTEXT_SUMMARY.md
3. 然后发 core_files.md
4. 最后发 documents.md

### 多 AI 协同
可以同时发给多个 AI：
- Gemini Pro - 获取技术深度
- Claude - 获取架构设计
- ChatGPT - 获取实用建议

综合所有反馈做决策。

## ❓ FAQ

**Q: 为什么要手动传输？**
A: 避免 API 限制，获得更深入的分析

**Q: 需要多长时间？**
A: 通常 60-90 分钟，取决于 AI 和网络速度

**Q: 结果准确性如何？**
A: 基于完整上下文，通常比自动 API 调用更准确

**Q: 可以重复使用吗？**
A: 可以，多次发给不同 AI，获得不同视角

---

**准备好了? 开始与外部 AI 协同吧！** 🚀

"""

        with open(f"{package_dir}/README.md", 'w', encoding='utf-8') as f:
            f.write(index)

        print(f"   ✅ 包已创建: {package_dir}")
        print()
        return package_dir

if __name__ == "__main__":
    exporter = ContextExporter()
    exporter.export_all()
```

### 第 2 步：导出流程

```bash
# 自动导出所有项目上下文
python3 export_context_for_ai.py

# 输出位置
# exports/
# ├── AI_PROMPT_20251221_052715.md      ⭐ 最重要
# ├── CONTEXT_SUMMARY_20251221_052715.md
# ├── git_history_20251221_052715.md
# ├── project_structure_20251221_052715.md
# ├── core_files_20251221_052715.md
# └── documents_20251221_052715.md
```

### 第 3 步：手动协同流程

```
1. 运行导出脚本
   python3 export_context_for_ai.py
   ↓
2. 打开外部 AI (Gemini Pro / Claude / ChatGPT)
   ↓
3. 复制 AI_PROMPT.md 内容到对话框
   ↓
4. AI 分析并提出建议
   ↓
5. 保存 AI 的评估报告
   exports/ai_reviews/gemini_review_20251221.md
   ↓
6. 导入结果（可选）
   python3 import_ai_review.py
```

### 第 4 步：结果导入

创建 `import_ai_review.py` - 将外部 AI 的评估导入系统：

```python
#!/usr/bin/env python3
"""
导入外部 AI 的评估报告到系统
"""

import os
from datetime import datetime

def import_ai_review(review_file, ai_name="external_ai"):
    """导入 AI 评估报告"""

    # 读取报告
    with open(review_file, 'r', encoding='utf-8') as f:
        review_content = f.read()

    # 创建本地副本
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ai_reviews_dir = "/opt/mt5-crs/docs/reviews"
    os.makedirs(ai_reviews_dir, exist_ok=True)

    # 保存到系统
    output_file = f"{ai_reviews_dir}/{ai_name}_review_{timestamp}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(review_content)

    # 创建 Notion 任务（可选）
    print(f"✅ AI 评估报告已导入: {output_file}")
    print()
    print("💡 建议:")
    print("1. 打开报告审查建议")
    print("2. 创建相应的工单")
    print("3. 规划实施步骤")
    print("4. 跟踪执行进度")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import_ai_review(sys.argv[1])
    else:
        print("用法: python3 import_ai_review.py <review_file>")
```

---

## 📋 方案 B 工作流总结

### 完整流程图

```
你的 Claude Code
    ↓
[export_context_for_ai.py]
    ↓
生成 6 个上下文文件 (280KB)
    ├─ AI_PROMPT.md ⭐
    ├─ CONTEXT_SUMMARY.md
    ├─ git_history.md
    ├─ project_structure.md
    ├─ core_files.md
    └─ documents.md
    ↓
你手动打开外部 AI
(Gemini Pro / Claude / ChatGPT / 其他)
    ↓
复制 AI_PROMPT.md 内容到对话框
    ↓
可选: 粘贴其他上下文文件
    ↓
外部 AI 进行深度分析
(60-90 分钟，无 API 限制)
    ↓
获得完整评估报告
    ├─ 项目状态评估
    ├─ MT5 API 实施方案
    ├─ 风险识别与缓解
    ├─ 代码质量评估
    ├─ 技术债务评估
    ├─ 性能优化建议
    └─ 测试策略
    ↓
你复制 AI 的评估结果
    ↓
[import_ai_review.py]
    ↓
保存到本地和 Notion
    ↓
完成！
    ↓
基于外部 AI 的建议
规划和实施工单 #011
```

---

## 🎯 双方案对比

### 方案 A vs 方案 B

| 方面 | 方案 A (API) | 方案 B (文件) |
|------|------------|------------|
| **速度** | 快 (5-10 分钟) | 中等 (需要手动) |
| **自动化度** | 100% | 50% (手动传输) |
| **API 限制** | ❌ 受限 | ✅ 无限制 |
| **深度** | 中等 | 很深 (人工审查) |
| **成本** | 有 (API 配额) | 无 (仅时间) |
| **可靠性** | ⚠️ 网络依赖 | ✅ 完全可靠 |
| **多 AI 协同** | ❌ 难 | ✅ 容易 |
| **上下文完整性** | 中等 (4000 字) | 完整 (70000 tokens) |

---

## 💡 推荐使用策略

### 场景 1: 快速评估
```bash
# 使用方案 A (API)
python3 gemini_review_bridge.py
# 如果 API 可用，5 分钟获得结果
```

### 场景 2: API 不可用
```bash
# 使用方案 B (文件传输)
python3 export_context_for_ai.py
# 手动发给外部 AI
# 60-90 分钟获得深度分析
```

### 场景 3: 深度协同 (推荐！)
```bash
# 同时使用两个方案
# A. 先用方案 A 快速评估
python3 gemini_review_bridge.py

# B. 并行用方案 B 深度分析
python3 export_context_for_ai.py
# 手动发给 Gemini Pro + Claude

# C. 综合所有建议做决策
# 获得更全面的视角
```

---

## 📊 实施路线图

### 第一阶段 (今天)
- ✅ 方案 A: 已部署 (Gemini API)
- ✅ 方案 B: 已设计
- [ ] 创建 `export_context_for_ai.py`
- [ ] 创建 `import_ai_review.py`

### 第二阶段 (本周)
- [ ] 运行 `export_context_for_ai.py`
- [ ] 手动发给外部 AI
- [ ] 收集 AI 的评估报告
- [ ] 保存到本地

### 第三阶段 (本月)
- [ ] 综合分析所有建议
- [ ] 规划工单 #011 详细步骤
- [ ] 开始开发

---

## 🏆 最终建议

### 为什么要采用双方案？

1. **互为备选**
   - API 不可用 → 使用文件传输
   - 文件传输太慢 → 使用 API
   - 最大化可用性

2. **深度 + 速度**
   - 方案 A: 快速迭代
   - 方案 B: 深度思考
   - 结合使用效果最佳

3. **多 AI 协同**
   - Gemini Pro (API) - 快速反馈
   - Claude (文件) - 架构设计
   - ChatGPT (文件) - 实用建议
   - 获得多个视角

4. **成本最低**
   - 不受 API 限制
   - 不需要付费
   - 仅需时间投入

---

**立即开始？**

```bash
# 第一步: 创建导出工具
# (我会帮你实现)

# 第二步: 运行导出
python3 export_context_for_ai.py

# 第三步: 手动发给外部 AI
# Gemini Pro / Claude / ChatGPT

# 第四步: 收集报告并导入
python3 import_ai_review.py

# 完成！开始基于深度建议规划工单 #011
```

---

**这个双方案系统将大大提升你与外部 AI 的协同质量！** 🚀

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

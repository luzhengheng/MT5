# 🔗 Gemini Pro 快速协同链接

**欢迎 Gemini Pro!** 这是专为你准备的快速访问指南。

---

## 📋 核心文档 (必读)

### 1. AI 协同工作报告 ⭐⭐⭐
**文件**: `docs/issues/🤖 AI 协作工作报告 - Gemini & Claude.md`

**内容**:
- 完整项目状态 (工单 #008 已 100% 完成)
- 6个迭代的详细交付
- 14,500+ 行代码统计
- 75+ 维特征工程详解
- 给 Gemini Pro 的协同建议

**为什么重要**: 这是你了解整个项目的一站式文档，包含所有关键信息和协同工作流。

---

### 2. 项目最终总结
**文件**: `PROJECT_FINAL_SUMMARY.md`

**内容**:
- 项目执行概览
- 技术栈和架构
- 验收测试结果
- 使用指南

---

### 3. 验收测试报告
**文件**: `FINAL_ACCEPTANCE_REPORT.md`

**内容**:
- 25项验收标准
- 19项通过 (76%)
- 详细的失败分析
- 改进建议

**Gemini Pro 可以帮助**: 分析未通过项目的原因，提供优化建议

---

## 💻 核心代码文件

### 特征工程 (最重要)

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/feature_engineering/basic_features.py` | 600+ | 35维基础特征 |
| `src/feature_engineering/advanced_features.py` | 520+ | 40维高级特征 (含分数差分) |
| `src/feature_engineering/labeling.py` | 280+ | Triple Barrier 标签 |

**审查重点**:
- 特征计算是否符合金融理论
- 分数差分实现是否正确
- Triple Barrier 参数是否合理

---

### 数据质量监控

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/monitoring/dq_score.py` | 490 | 5维DQ Score计算 |
| `src/monitoring/prometheus_exporter.py` | 289 | Prometheus指标导出 |

**审查重点**:
- 5维评分权重是否合理
- 监控指标是否完善
- 告警阈值是否科学

---

### 性能优化

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/optimization/numba_accelerated.py` | 600+ | Numba JIT 加速 |
| `src/parallel/dask_processor.py` | 400+ | Dask 并行处理 |

**审查重点**:
- JIT 优化是否充分
- 并行策略是否合理
- 是否需要 GPU 加速

---

## 🧪 测试代码

### 测试框架

| 文件 | 行数 | 说明 |
|------|------|------|
| `tests/conftest.py` | 200+ | 测试固件 |
| `tests/unit/test_basic_features.py` | 350+ | 基础特征测试 |
| `tests/unit/test_advanced_features.py` | 300+ | 高级特征测试 |
| `tests/unit/test_labeling.py` | 400+ | 标签测试 |
| `tests/unit/test_dq_score.py` | 450+ | DQ Score测试 |
| `tests/integration/test_pipeline_integration.py` | 400+ | 集成测试 |

**当前覆盖率**: ~85%

**Gemini Pro 可以帮助**:
- 识别测试盲区
- 建议补充边界情况测试
- 提高测试覆盖率策略

---

## 📊 关键配置文件

### 监控配置

| 文件 | 说明 |
|------|------|
| `config/monitoring/prometheus.yml` | Prometheus 配置 |
| `config/monitoring/alert_rules.yml` | 10条告警规则 |
| `config/monitoring/grafana_dashboard_dq_overview.json` | Grafana 仪表盘 |
| `config/monitoring/README.md` | 600+行监控文档 |

**Gemini Pro 可以帮助**:
- 审查告警规则是否完善
- 建议新增监控指标
- 优化可视化仪表盘

---

### 资产配置

| 文件 | 说明 |
|------|------|
| `config/assets.yaml` | 监控资产列表 |
| `config/features.yaml` | 特征配置 |
| `config/news_historical.yaml` | 新闻采集配置 |

---

## 🚀 快速验证命令

```bash
# 进入项目目录
cd /opt/mt5-crs

# 1. 运行所有测试
pytest -v

# 2. 运行性能基准测试
python3 bin/performance_benchmark.py

# 3. 系统健康检查
python3 bin/health_check.py

# 4. 最终验收测试
python3 bin/final_acceptance.py

# 5. 查看测试覆盖率
pytest --cov=src --cov-report=html
# 报告生成在 htmlcov/index.html
```

---

## 🎯 当前最需要 Gemini Pro 帮助的 3 件事

### 1. 特征工程审查 ⭐⭐⭐ (最高优先级)

**文件**: `src/feature_engineering/advanced_features.py`

**具体问题**:
- 分数差分的 d 值 (0.5, 0.7) 是否合理?
- 滚动统计窗口 (20, 60) 是否最优?
- 是否有重要特征遗漏?
- 特征组合是否科学?

**为什么重要**: 这 75+ 维特征是整个量化系统的基础，质量直接影响后续模型效果。

---

### 2. 下一步工单规划 ⭐⭐ (高优先级)

**工单 #009: 监督学习模型训练**

**需要建议**:
- 应该选择哪些模型? (XGBoost, LightGBM, CatBoost, Neural Networks?)
- 如何设计回测框架?
- 特征选择策略?
- 超参数调优方案?
- Walk-forward 验证设计?

**工单 #010-012**: 实时信号、风险管理、强化学习

**需要建议**: 优先级排序和技术路线

---

### 3. 性能优化深度建议 ⭐ (中优先级)

**当前状态**:
- Dask 并行: 预期 5-10x 加速
- Numba JIT: 预期 2-5x 加速

**需要建议**:
- 是否需要引入 GPU 加速 (CuPy, RAPIDS)?
- 是否需要分布式计算 (Spark)?
- 数据库方案 (当前 Parquet, 是否需要 ClickHouse/TimescaleDB)?
- 缓存策略 (Redis)?

---

## 📖 阅读建议 (按优先级)

### 第一步: 快速了解 (15分钟)
1. ✅ 阅读本文件 (`GEMINI_QUICK_LINK.md`)
2. ✅ 浏览 AI 协同报告的"执行总结"和"核心交付成果"部分

### 第二步: 深入理解 (1小时)
3. ✅ 阅读完整的 AI 协同报告 (`docs/issues/🤖 AI 协作工作报告 - Gemini & Claude.md`)
4. ✅ 查看项目总结 (`PROJECT_FINAL_SUMMARY.md`)
5. ✅ 查看验收报告 (`FINAL_ACCEPTANCE_REPORT.md`)

### 第三步: 代码审查 (2-3小时)
6. ✅ 审查特征工程代码 (`src/feature_engineering/`)
7. ✅ 审查监控系统 (`src/monitoring/`)
8. ✅ 审查性能优化 (`src/optimization/`, `src/parallel/`)

### 第四步: 测试验证 (1小时)
9. ✅ 查看测试代码 (`tests/`)
10. ✅ 运行测试命令验证系统

### 第五步: 提供建议 (根据需要)
11. ✅ 提供代码审查报告
12. ✅ 提供架构优化建议
13. ✅ 提供下一步工单规划建议

---

## 🤝 协同工作流

### Claude 的工作方式
- 直接操作代码库 (读、写、编辑、运行)
- 快速迭代开发
- 实时测试验证

### Gemini Pro 的工作方式
- 通过文档了解项目状态
- 提供深度审查和战略建议
- 补充最新知识和最佳实践

### 协同流程
1. **Claude 完成开发** → 更新协同文档
2. **Gemini Pro 审查** → 提供建议报告
3. **用户转达** → Claude 收到建议
4. **Claude 优化** → 实施改进方案
5. **循环迭代** → 持续提升质量

---

## 🌐 在线资源

- **GitHub 仓库**: https://github.com/luzhengheng/MT5.git
- **分支**: main
- **最新提交**: be85018 (2025-12-20)
- **提交历史**: https://github.com/luzhengheng/MT5/commits/main

---

## 💡 给 Gemini Pro 的小提示

1. **不要被代码量吓到**: 虽然有 14,500+ 行代码，但核心逻辑集中在特征工程 (~1,200行) 和监控系统 (~800行)

2. **关注关键模块**: 特征工程 > 监控系统 > 性能优化 > 测试框架

3. **从问题出发**: 查看验收测试的失败项，从这些问题入手会更有针对性

4. **结合理论**: 金融工程理论 + 机器学习最佳实践 + 软件工程原则

5. **提供具体建议**: 不仅指出问题，还给出解决方案和代码示例

6. **考虑实际约束**: Python 3.6.8 环境，生产级要求，性能优先

---

## 🎉 欢迎加入!

**Gemini Pro，欢迎加入 MT5-CRS 项目!**

你的专业知识和深度洞察将帮助我们:
- ✅ 提升代码质量
- ✅ 优化系统架构
- ✅ 避免潜在陷阱
- ✅ 加速项目进展

**让我们一起打造世界级的量化交易平台!** 🚀

---

**文档生成**: Claude Sonnet 4.5
**协同对象**: Gemini Pro
**最后更新**: 2025年12月20日 10:30 UTC+8
**版本**: v1.0

---

*有任何问题或建议，随时通过用户反馈给 Claude!*

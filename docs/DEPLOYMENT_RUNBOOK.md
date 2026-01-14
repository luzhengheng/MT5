# 成本优化器部署运维手册

**版本**: 1.0
**最后更新**: 2026-01-14
**维护者**: Engineering Team

---

## 目录

1. [快速参考](#快速参考)
2. [部署前检查](#部署前检查)
3. [部署步骤](#部署步骤)
4. [验证步骤](#验证步骤)
5. [日常运维](#日常运维)
6. [故障排查](#故障排查)
7. [回滚流程](#回滚流程)

---

## 快速参考

### 关键命令

```bash
# 验证系统
python3 scripts/ai_governance/benchmark_cost_optimizer.py

# 测试监控
python3 scripts/ai_governance/monitoring_alerts.py

# 运行审查
python3 scripts/ai_governance/unified_review_gate.py

# 查看日志
tail -100 VERIFY_LOG.log
tail -100 unified_review_optimizer.log
tail -100 gemini_review_optimizer.log

# 清除缓存
rm -rf .cache/unified_review_cache
rm -rf .cache/gemini_review_cache

# 重启系统
# 只需重新运行脚本（无长期运行进程）
```

### 关键文件

```
scripts/ai_governance/
  ├── cost_optimizer.py                 # 主优化器
  ├── review_cache.py                   # 缓存模块
  ├── review_batcher.py                 # 批处理模块
  ├── benchmark_cost_optimizer.py       # 基准测试
  ├── monitoring_alerts.py              # 监控告警
  ├── unified_review_gate.py            # 双引擎网关 (已集成)
  └── gemini_review_bridge.py           # Gemini 桥接 (已集成)

docs/
  ├── PHASE2_FINAL_SUMMARY.md           # 项目总结
  ├── COST_OPTIMIZER_QUICK_START.md     # 快速开始
  ├── POST_PHASE2_DEPLOYMENT_PLAN.md    # 部署计划
  └── DEPLOYMENT_RUNBOOK.md             # 本文档

.cache/
  ├── unified_review_cache/             # 统一网关缓存
  └── gemini_review_cache/              # Gemini 网关缓存
```

---

## 部署前检查

### ✅ 环境检查

```bash
# 检查 Python 版本
python3 --version  # 需要 3.7+

# 检查依赖
pip list | grep -E 'curl_cffi|dotenv'

# 检查文件完整性
ls -la scripts/ai_governance/*.py

# 检查权限
chmod +x scripts/ai_governance/*.py
```

### ✅ 代码质量检查

```bash
# Python 语法检查
python3 -m py_compile scripts/ai_governance/cost_optimizer.py
python3 -m py_compile scripts/ai_governance/review_cache.py
python3 -m py_compile scripts/ai_governance/review_batcher.py
python3 -m py_compile scripts/ai_governance/unified_review_gate.py
python3 -m py_compile scripts/ai_governance/gemini_review_bridge.py

# 导入检查
python3 -c "from cost_optimizer import AIReviewCostOptimizer; print('✅ OK')"
python3 -c "from monitoring_alerts import CostOptimizerMonitor; print('✅ OK')"
```

### ✅ 性能基准检查

```bash
# 运行基准测试
python3 scripts/ai_governance/benchmark_cost_optimizer.py

# 预期输出: 所有基准测试通过 ✅
```

### ✅ 环境变量检查

```bash
# 检查必要的环境变量
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:-(未设置)}"
echo "CLAUDE_API_KEY: ${CLAUDE_API_KEY:-(未设置)}"
echo "VENDOR_BASE_URL: ${VENDOR_BASE_URL:-(未设置)}"

# 如果未设置，加载 .env 文件
if [ -f .env ]; then
    source .env
    echo "✅ 已加载 .env 文件"
else
    echo "⚠️ .env 文件未找到，请检查环境变量"
fi
```

### ✅ 磁盘空间检查

```bash
# 检查缓存目录的可用空间
df -h .cache/

# 预期: 至少 1GB 可用空间
# 缓存文件大小预估: 每 100 个缓存项约 10MB
```

### ✅ 部署前检查清单

```markdown
## 部署前检查清单

- [ ] Python 版本 >= 3.7
- [ ] 依赖已安装
- [ ] 文件权限正确
- [ ] 代码质量检查通过
- [ ] 基准测试通过
- [ ] 环境变量已设置
- [ ] 磁盘空间充足
- [ ] 备份已创建
- [ ] 团队已知晓
- [ ] 回滚计划已准备
```

---

## 部署步骤

### 阶段 1: 测试环境部署

```bash
# 1. 备份当前配置
cp scripts/ai_governance/unified_review_gate.py \
   scripts/ai_governance/unified_review_gate.py.bak

# 2. 创建测试目录
mkdir -p /opt/test_deploy
cd /opt/test_deploy

# 3. 复制文件到测试环境
cp -r /opt/mt5-crs/scripts/ai_governance/ .
cp -r /opt/mt5-crs/docs/ .

# 4. 创建缓存目录
mkdir -p .cache/unified_review_cache
mkdir -p .cache/gemini_review_cache

# 5. 运行基准测试
python3 benchmark_cost_optimizer.py

# 6. 验证输出
# 预期: ✅ 所有基准测试通过

echo "✅ 测试环境部署完成"
```

### 阶段 2: 灰度部署 (10% 流量)

```bash
# 1. 设置优化器比例
export COST_OPTIMIZER_RATIO=0.1

# 2. 启动应用
python3 unified_review_gate.py

# 3. 监控 2-3 天
# 观察:
# - 错误率是否增加
# - 成本是否节省
# - 用户反馈

# 4. 检查日志
tail -100 VERIFY_LOG.log
tail -100 unified_review_optimizer.log

# 5. 运行监控检查
python3 monitoring_alerts.py
```

### 阶段 3: 提升到 50% 流量

```bash
# 1. 更新比例
export COST_OPTIMIZER_RATIO=0.5

# 2. 重启应用
# (如果需要)

# 3. 继续监控 2-3 天

# 4. 验证指标
# - API 调用减少了吗?
# - 缓存命中率如何?
# - 有用户反馈吗?
```

### 阶段 4: 全量部署 (100% 流量)

```bash
# 1. 最终比例
export COST_OPTIMIZER_RATIO=1.0

# 2. 部署到生产
# (根据您的部署流程)

# 3. 启用完整监控

# 4. 准备回滚方案

echo "✅ 全量部署完成"
```

---

## 验证步骤

### 功能验证

```bash
# 1. 验证缓存功能
echo "测试缓存..."
python3 -c "
from review_cache import ReviewCache
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    cache = ReviewCache()
    cache.save('test_file.py', {'status': 'PASS'})
    result = cache.get('test_file.py')
    assert result == {'status': 'PASS'}
    print('✅ 缓存功能正常')
"

# 2. 验证批处理
echo "测试批处理..."
python3 -c "
from review_batcher import ReviewBatcher
batcher = ReviewBatcher()
test_files = [f'file_{i}.py' for i in range(10)]
batches = batcher.create_batches(test_files)
assert len(batches) > 0
print(f'✅ 批处理正常 (创建了 {len(batches)} 个批次)')
"

# 3. 验证优化器
echo "测试优化器..."
python3 benchmark_cost_optimizer.py

# 4. 验证监控
echo "测试监控..."
python3 monitoring_alerts.py
```

### 性能验证

```bash
# 1. 检查 API 调用减少
echo "API 调用减少:"
grep "api_calls" unified_review_optimizer.log | tail -1

# 2. 检查缓存命中率
echo "缓存命中率:"
grep "cache_hit_rate" unified_review_optimizer.log | tail -1

# 3. 检查成本节省
echo "成本节省率:"
grep "cost_reduction_rate" unified_review_optimizer.log | tail -1

# 4. 检查执行时间
echo "执行时间:"
grep "Processing.*files" unified_review_optimizer.log | tail -1
```

### 告警验证

```bash
# 1. 检查告警配置
cat .monitoring_config.json

# 2. 运行告警测试
python3 -c "
from monitoring_alerts import CostOptimizerMonitor

# 正常情况 - 无告警
monitor = CostOptimizerMonitor()
stats_ok = {
    'total_files': 50,
    'api_calls': 3,
    'cached_files': 35,
    'cache_hit_rate': 0.7,
    'cost_reduction_rate': 0.94
}
result = monitor.check_stats(stats_ok)
assert result == True, '正常情况应该无告警'
print('✅ 正常情况验证通过')

# 异常情况 - 应该有告警
stats_bad = {
    'total_files': 50,
    'api_calls': 30,
    'cached_files': 5,
    'cache_hit_rate': 0.15,
    'cost_reduction_rate': 0.4
}
result = monitor.check_stats(stats_bad)
assert result == False, '异常情况应该有告警'
print('✅ 异常情况验证通过')
"
```

### 验证清单

```markdown
## 验证清单

功能验证:
  - [ ] 缓存功能正常
  - [ ] 批处理功能正常
  - [ ] 优化器初始化成功
  - [ ] 监控系统就绪

性能验证:
  - [ ] API 调用减少 > 80%
  - [ ] 缓存命中率 > 30%
  - [ ] 成本节省率 > 80%
  - [ ] 执行时间 < 5s (per batch)

告警验证:
  - [ ] 正常情况无告警
  - [ ] 异常情况有告警
  - [ ] 告警分级正确
  - [ ] 日志记录完整

生产验证:
  - [ ] 错误率 < 0.1%
  - [ ] 系统可用性 > 99%
  - [ ] 用户反馈正面
  - [ ] 没有意外成本增加
```

---

## 日常运维

### 每天

```bash
# 上班第一件事
echo "=== 每日检查 ==="

# 1. 检查系统状态
tail -20 VERIFY_LOG.log
echo "---"

# 2. 检查是否有告警
grep -E "WARNING|CRITICAL" VERIFY_LOG.log | tail -5
echo "---"

# 3. 检查成本指标
tail -1 unified_review_optimizer.log | grep -oE 'cost_reduction_rate.*'
echo "---"

# 如果有异常，查看完整日志
# tail -100 VERIFY_LOG.log
```

### 每周

```bash
# 每周一生成周报告
echo "=== 周报告 ===" > weekly_report.txt
echo "日期: $(date)" >> weekly_report.txt
echo "" >> weekly_report.txt

# 收集数据
echo "API 调用统计:" >> weekly_report.txt
grep "api_calls" unified_review_optimizer.log | tail -7 >> weekly_report.txt
echo "" >> weekly_report.txt

echo "缓存命中率:" >> weekly_report.txt
grep "cache_hit_rate" unified_review_optimizer.log | tail -7 >> weekly_report.txt
echo "" >> weekly_report.txt

echo "成本节省:" >> weekly_report.txt
grep "cost_reduction_rate" unified_review_optimizer.log | tail -7 >> weekly_report.txt

# 发送给团队
# cat weekly_report.txt | mail -s "Weekly Report" team@example.com
```

### 每月

```bash
# 月度回顾和规划
echo "=== 月度总结 ===" > monthly_report.txt

# 计算月度指标
echo "本月成本节省总额: $X" >> monthly_report.txt
echo "月度 API 减少: X%" >> monthly_report.txt
echo "平均缓存命中率: X%" >> monthly_report.txt

# 列出改进项
echo "下月改进计划:" >> monthly_report.txt
echo "- ..." >> monthly_report.txt

# 送给管理层
# cat monthly_report.txt | mail -s "Monthly Report" manager@example.com
```

---

## 故障排查

### 问题 1: 优化器未启用

**症状**: 日志中没有 "[INIT] Cost optimizer enabled"

**检查步骤**:
```bash
# 1. 验证模块可导入
python3 -c "from cost_optimizer import AIReviewCostOptimizer; print('✅')"

# 2. 检查初始化错误
grep "Failed to initialize" VERIFY_LOG.log

# 3. 检查文件权限
ls -la scripts/ai_governance/cost_optimizer.py

# 4. 检查 Python 路径
python3 -c "import sys; print(sys.path)"
```

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 清除 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# 重新运行
python3 scripts/ai_governance/unified_review_gate.py
```

### 问题 2: 缓存无效

**症状**: 每次都执行 API 调用，缓存命中率 < 10%

**检查步骤**:
```bash
# 1. 检查缓存目录
ls -la .cache/unified_review_cache/

# 2. 检查缓存文件
find .cache -name "*.cache" -ls

# 3. 检查文件哈希
python3 -c "
import hashlib
with open('test_file.py', 'rb') as f:
    print(f'MD5: {hashlib.md5(f.read()).hexdigest()}')
"

# 4. 检查缓存日志
grep -i cache VERIFY_LOG.log | tail -20
```

**解决方案**:
```bash
# 1. 清除缓存
rm -rf .cache/unified_review_cache/*

# 2. 检查磁盘空间
df -h .cache/

# 3. 检查文件修改时间
stat test_file.py

# 4. 重新运行两次
python3 scripts/ai_governance/unified_review_gate.py
python3 scripts/ai_governance/unified_review_gate.py  # 应该有缓存命中
```

### 问题 3: 批处理未生效

**症状**: 50 个文件产生 50 次 API 调用（无批处理）

**检查步骤**:
```bash
# 1. 检查批处理日志
grep "Created.*batches" unified_review_optimizer.log

# 2. 验证批处理是否启用
python3 -c "
from cost_optimizer import AIReviewCostOptimizer
opt = AIReviewCostOptimizer()
print(f'Batch enabled: {opt.enable_batch}')
"

# 3. 检查文件数量
ls test_files/*.py | wc -l
```

**解决方案**:
```bash
# 1. 确保批处理已启用
# 编辑 unified_review_gate.py:
# optimizer = AIReviewCostOptimizer(enable_batch=True)

# 2. 调整批处理大小
# 编辑 review_batcher.py:
# max_batch_size_low_risk = 15

# 3. 重新测试
python3 benchmark_cost_optimizer.py
```

### 问题 4: 告警过多

**症状**: 频繁收到 WARNING 或 CRITICAL 告警

**检查步骤**:
```bash
# 1. 查看告警日志
grep -E "WARNING|CRITICAL" monitoring_alerts.log | tail -20

# 2. 检查告警阈值
cat .monitoring_config.json

# 3. 分析实际指标
grep "cost_reduction_rate" unified_review_optimizer.log | awk '{print $NF}' | sort -n
```

**解决方案**:
```bash
# 1. 调整告警阈值
python3 -c "
import json
config = {
    'api_calls_warning': 150,  # 提高阈值
    'cache_hit_warning': 0.25,
    'cost_reduction_warning': 0.75
}
with open('.monitoring_config.json', 'w') as f:
    json.dump(config, f)
"

# 2. 重新运行监控
python3 monitoring_alerts.py

# 3. 验证告警
python3 scripts/ai_governance/unified_review_gate.py
```

### 问题 5: 系统错误

**症状**: `Exception: ...` 或 `AttributeError: ...`

**检查步骤**:
```bash
# 1. 查看完整错误堆栈
tail -50 VERIFY_LOG.log

# 2. 启用详细日志
export DEBUG=1
python3 scripts/ai_governance/unified_review_gate.py

# 3. 检查依赖版本
pip show curl_cffi python-dotenv
```

**解决方案**:
```bash
# 1. 更新依赖
pip install --upgrade curl_cffi python-dotenv

# 2. 重新安装
pip uninstall cost_optimizer && pip install -e .

# 3. 清除缓存和临时文件
rm -rf __pycache__ .cache *.pyc

# 4. 重新运行
python3 scripts/ai_governance/unified_review_gate.py
```

---

## 回滚流程

### 情况 1: 部分功能异常

```bash
# 1. 禁用优化器
export COST_OPTIMIZER_ENABLED=0

# 2. 继续运行（降级到传统模式）
python3 scripts/ai_governance/unified_review_gate.py

# 3. 调查问题
# 查看日志，确定问题原因

# 4. 修复
# 修改代码，提交更新

# 5. 重新启用
unset COST_OPTIMIZER_ENABLED
python3 scripts/ai_governance/unified_review_gate.py
```

### 情况 2: 系统完全故障

```bash
# 1. 立即停止优化器
export COST_OPTIMIZER_ENABLED=0

# 2. 恢复备份版本
cp scripts/ai_governance/unified_review_gate.py.bak \
   scripts/ai_governance/unified_review_gate.py

# 3. 清除缓存
rm -rf .cache/*

# 4. 重启系统
python3 scripts/ai_governance/unified_review_gate.py

# 5. 验证功能
python3 scripts/ai_governance/unified_review_gate.py
python3 scripts/ai_governance/unified_review_gate.py

# 6. 调查问题
# 分析日志，确定根本原因

# 7. 修复
# 解决问题，重新部署

# 8. 测试
python3 scripts/ai_governance/benchmark_cost_optimizer.py
```

### 情况 3: 数据损坏

```bash
# 1. 停止系统
export COST_OPTIMIZER_ENABLED=0

# 2. 备份当前缓存（用于调查）
cp -r .cache .cache.backup.$(date +%s)

# 3. 清除缓存
rm -rf .cache/unified_review_cache/*
rm -rf .cache/gemini_review_cache/*

# 4. 重新初始化
mkdir -p .cache/unified_review_cache
mkdir -p .cache/gemini_review_cache

# 5. 重启系统
export COST_OPTIMIZER_ENABLED=1
python3 scripts/ai_governance/unified_review_gate.py

# 6. 监控重建过程
tail -f VERIFY_LOG.log
```

---

## 常见命令参考

```bash
# 查看系统状态
systemctl status cost-optimizer  # 如果作为服务运行

# 查看进程
ps aux | grep cost_optimizer

# 查看端口占用 (如果暴露 API)
lsof -i :8080

# 查看日志
tail -100 VERIFY_LOG.log
tail -100 unified_review_optimizer.log

# 搜索特定日期的日志
grep "2026-01-14" VERIFY_LOG.log | head -20

# 搜索错误
grep -i error VERIFY_LOG.log
grep -i critical VERIFY_LOG.log

# 统计 API 调用
grep "api_calls" unified_review_optimizer.log | wc -l

# 获取最后一个有效指标
tail -1 unified_review_optimizer.log
```

---

## 紧急联系

**系统故障**:
- 技术负责人: engineering-team@example.com
- 24/7 支持: support@example.com

**文档问题**:
- 查看快速开始指南
- 查看代码注释
- 查看 GitHub issues

**性能问题**:
- 检查监控指标
- 查看故障排查指南
- 收集日志并上报

---

**最后更新**: 2026-01-14
**状态**: ✅ READY FOR PRODUCTION

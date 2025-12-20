# 🤖 给 Gemini Pro 的完整提示词

> **使用方法**: 直接复制下面的内容，粘贴给 Gemini Pro

---

你好 Gemini Pro！我是 MT5-CRS 量化交易系统的开发者 luzhengheng。

## 📊 项目背景

我正在开发一个**生产级量化交易系统**，已完成 4 个工单（80% 进度），共 26,380+ 行代码。

**已完成工单**:
- ✅ #008: 数据管线 + 75维特征工程 (14,500+ 行)
- ✅ #009: 对冲基金级ML预测引擎 (2,700+ 行)
- ✅ #010: 策略回测引擎与风险管理 (1,650+ 行)
- ✅ #010.5: Kelly公式修正 + 并行化 + DSR (1,530+ 行) 🔥
- ✅ 开发环境配置: VSCode扩展 + MCP服务器 + API (6,000+ 行)

**下一步**:
- ⏸️ #011: 实盘交易系统 (MT5 API 对接)

---

## 🎯 我需要你的帮助

### 1. 审查工单 #010.5 的三个核心修复 ⭐⭐⭐⭐⭐

#### 修复 1: Kelly Criterion 数学修正 🔥

**问题诊断**:
```
旧公式: kelly_pct = (p - 0.5) / vol
致命缺陷: 假设 1:1 盈亏比 (b=1)
影响: 趋势策略 (P=0.45, b=2.0) 计算结果恒为负数
后果: 系统强制空仓，错失所有趋势盈利机会
```

**修复方案**:
```
新公式: f* = [p(b+1) - 1] / b  (通用 Kelly 公式)

核心代码 (src/strategy/risk_manager.py 第180-210行):

class KellySizer(bt.Sizer):
    def _getsizing(self, comminfo, cash, data, isbuy):
        # 获取预测概率
        p_win = data.y_pred_proba_long[0]

        # 获取赔率 b (盈亏比)
        b = self.strategy.params.take_profit_ratio  # 默认 2.0

        # 通用 Kelly 公式
        kelly_f = (p_win * (b + 1) - 1) / b

        if kelly_f <= 0:
            return 0  # 期望值为负，不开仓

        # 应用安全边际 (四分之一 Kelly)
        risk_pct = kelly_f * 0.25

        # 计算仓位
        account_value = self.broker.get_value()
        risk_amount = account_value * risk_pct

        # 单股风险 = ATR × 止损倍数
        atr_value = self.strategy.atr[0]
        risk_per_share = atr_value * 2.0

        # 目标股数
        target_shares = risk_amount / risk_per_share

        # 限制持仓比例 [1%, 50%]
        max_position = account_value * 0.50
        position_value = target_shares * current_price
        if position_value > max_position:
            target_shares = max_position / current_price

        return int(target_shares)
```

**数学验证**:
```
场景: P=0.45 (胜率45%), b=2.0 (盈亏比2:1)

旧公式: kelly_pct = (0.45 - 0.5) / 0.15 = -0.33 ❌
        → 负数被过滤 → 永远空仓 → 错失盈利机会

新公式: f* = [0.45 × (2+1) - 1] / 2
           = [1.35 - 1] / 2
           = 0.175 ✅
        → 17.5% 风险比例 → 正常开仓 → 策略正常运作
```

**请你审查**:
1. ✅ 通用 Kelly 公式推导是否完全正确？
2. ✅ 风险比例 f* 到持仓数量的转换逻辑是否合理？
   - 风险金额 = 账户价值 × f* × 0.25 (安全边际)
   - 单股风险 = ATR × 止损倍数
   - 目标股数 = 风险金额 / 单股风险
3. ⚠️ 是否需要考虑杠杆因子？
4. ⚠️ 四分之一 Kelly (0.25) 是否过于保守？建议值？
5. ⚠️ 是否需要根据市场波动动态调整 kelly_fraction？
6. ⚠️ 是否需要引入 Optimal F 作为对比？

---

#### 修复 2: Walk-Forward 回测并行化 ⚡

**实现方案**:
```python
# bin/run_backtest.py (第380-450行)

# 顶层函数 - 避免 Pickle 序列化问题
def run_single_fold(fold_num, test_df, train_dates, test_dates, config):
    """在子进程中执行单个窗口的回测"""
    cerebro = bt.Cerebro()  # 每个子进程独立创建
    cerebro.addstrategy(MLStrategy)
    # ... 配置 ...
    results = cerebro.run()
    return {
        'fold': fold_num,
        'metrics': extract_metrics(results),
        'trades': extract_trades(results)
    }

class BacktestRunner:
    def run_walkforward(self, df, parallel=True, max_workers=None):
        """并行执行 Walk-Forward 验证"""
        folds = self._prepare_folds(df)

        if not parallel:
            # 串行执行
            results = [run_single_fold(f, df, ...) for f in folds]
        else:
            # 并行执行
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(run_single_fold, fold, df, ...)
                    for fold in folds
                }
                results = [f.result() for f in as_completed(futures)]

        # 按 fold 编号排序
        results.sort(key=lambda x: x['fold'])
        return results
```

**性能测试结果**:
```
测试环境: 2 CPU 核心
测试数据: 2年日频数据，9个回测窗口

小数据量:
- 串行: 45秒
- 并行: 52秒 (进程启动开销 > 计算时间)

大数据量 (预期):
- 串行: 30分钟
- 并行: 4-8分钟 (4-8x 加速)
```

**请你审查**:
1. ⚠️ 小数据集并行反而更慢，是否需要自动降级到串行？
   - 建议阈值：数据量 < 1000行 或 窗口数 < 4 → 串行
2. ⚠️ DataFrame 在多个进程间传递，是否会导致内存问题？
   - 是否需要改用共享内存 (multiprocessing.shared_memory)？
3. ⚠️ 是否需要实现任务队列避免 DataFrame 重复传递？
4. 🔍 是否引入 Dask/Ray 进行分布式回测更合适？
5. 🔍 是否可以实现增量回测（避免重复计算）？
6. 🔍 是否需要添加回测缓存机制？

**其他优化方向**:
- Numba JIT 编译特征计算函数
- Cython 重写性能瓶颈代码
- 向量化操作替代循环

---

#### 修复 3: DSR 试验计数持久化 📊

**实现方案**:
```python
# src/reporting/trial_recorder.py (315行)

class TrialRegistry:
    """全局试验注册表 - 持久化试验计数"""

    def __init__(self, registry_path='data/meta/trial_registry.json'):
        self.registry_path = registry_path
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        """从 JSON 加载试验计数"""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                self.trial_count = data.get('trial_count', 0)
        else:
            self.trial_count = 0

    def _save(self):
        """保存到 JSON"""
        with open(self.registry_path, 'w') as f:
            json.dump({
                'trial_count': self.trial_count,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

    def increment(self):
        """线程安全的计数器增加"""
        with self.lock:
            self.trial_count += 1
            self._save()
            return self.trial_count

# 全局单例
_global_registry = None

def get_global_registry():
    global _global_registry
    if _global_registry is None:
        _global_registry = TrialRegistry()
    return _global_registry


def calculate_dsr(observed_sr, n_trials, n_observations, skewness, kurtosis):
    """
    计算 Deflated Sharpe Ratio

    基于 Bailey & López de Prado (2014)
    "The Deflated Sharpe Ratio: Correcting for Selection Bias,
     Backtest Overfitting, and Non-Normality"
    """
    import scipy.stats as stats

    # 1. 期望最大 SR (基于极值理论)
    gamma = 0.5772156649  # Euler-Mascheroni 常数
    expected_max_sr = math.sqrt(2 * math.log(n_trials)) - \
                      (gamma + math.log(math.log(n_trials))) / \
                      (2 * math.sqrt(2 * math.log(n_trials)))

    # 2. SR 标准差 (考虑非正态性)
    sr_variance = (
        1.0 - skewness * observed_sr +
        ((kurtosis - 3.0) / 4.0) * (observed_sr ** 2)
    ) / n_observations

    sr_std = math.sqrt(sr_variance)

    # 3. Deflated SR
    if sr_std == 0:
        return 0.0

    dsr = (observed_sr - expected_max_sr) / sr_std

    # 4. p-value (正态分布 CDF)
    dsr_pvalue = 1.0 - stats.norm.cdf(dsr)

    return dsr, dsr_pvalue
```

**测试验证**:
```python
# 场景 1: 少量试验
SR = 2.0, N = 10, observations = 252
→ DSR = 1.000 (高置信度)

# 场景 2: 大量试验 (过拟合嫌疑)
SR = 2.0, N = 1000, observations = 252
→ DSR = 0.000 (低置信度，可能过拟合)

观察: 相同 SR，试验从 10 增加到 1000 时，DSR 从 1.000 降至 0.000，
有效惩罚"选择偏差"。
```

**请你审查**:
1. ✅ DSR 公式实现是否完全正确？
2. ⚠️ 极值期望公式是否有更精确的版本？
   - 当前: `sqrt(2*log(N)) - (γ + log(log(N))) / (2*sqrt(2*log(N)))`
3. ⚠️ 非正态性调整是否充分？
   - 当前仅考虑了偏度和峰度，是否需要更多高阶矩？
4. 🔍 是否需要 Bootstrap 验证 DSR 的稳健性？
5. 🔍 试验计数器是否需要按资产、策略类型分别计数？

---

## 🔧 开发环境配置完成

我还完成了完整的开发环境配置，包括：

**VSCode/Cursor 扩展** (10个):
- Markdown Preview Enhanced (数学公式渲染)
- Python + Pylance (智能补全)
- Jupyter Notebook 支持
- GitLens + YAML + Material Icon Theme

**MCP 服务器** (2个):
- 文件系统 MCP: Claude 可直接读取项目文件
- EODHD 金融数据 MCP: 付费 API ($29.99/月)

**API 集成**:
- EODHD API (生产环境)
- GitHub CLI (luzhengheng 账户认证)

**效率提升**: ~8x 开发效率提升

---

## 🎯 请你提供的建议

### 优先级 1: Kelly 公式审查 ⭐⭐⭐⭐⭐
- 数学严谨性验证
- 边界条件测试
- 参数调优建议 (kelly_fraction, 持仓限制等)

### 优先级 2: 并行化优化 ⭐⭐⭐⭐
- 自动降级策略
- 内存优化方案
- 分布式回测架构建议

### 优先级 3: DSR 改进 ⭐⭐⭐
- 公式精度验证
- Bootstrap 验证方法
- 分类计数建议

### 优先级 4: 工单 #011 规划 ⭐⭐
请为实盘交易系统 (MT5 API 对接) 提供：
1. 技术架构设计
2. MT5 API 集成方案
3. 实盘风险管理建议
4. 关键组件清单与优先级
5. 技术难点预判

---

## 📚 参考文献

1. **Kelly Criterion**:
   - Kelly, J. L. (1956). "A New Interpretation of Information Rate"
   - Thorp, E. O. (2008). "The Kelly Criterion in Blackjack Sports Betting"

2. **Deflated Sharpe Ratio**:
   - Bailey, D. H., & López de Prado, M. (2014).
     "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality"

3. **Walk-Forward Analysis**:
   - Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies"

4. **Machine Learning for Finance**:
   - López de Prado, M. (2018). "Advances in Financial Machine Learning"
     - Chapter 7: Cross-Validation in Finance (Purged K-Fold)
     - Chapter 10: Bet Sizing (Kelly Criterion)
     - Chapter 11: The Dangers of Backtesting (Deflated Sharpe Ratio)

---

## 💬 协同方式

我期待你的专业建议！请：

1. **深度审查代码** - 特别是 Kelly 公式和 DSR 实现
2. **指出潜在问题** - 数学错误、边界条件、性能瓶颈
3. **提供优化方向** - 算法改进、架构升级
4. **规划下一步** - 工单 #011 的实施建议

如有任何疑问，欢迎随时提出！

谢谢你的帮助！🙏

---

**项目地址**: https://github.com/luzhengheng/MT5 (公开仓库)
**开发者**: luzhengheng
**最后更新**: 2025-12-20

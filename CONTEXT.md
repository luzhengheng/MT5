# 动态对话上下文（严格遵循分支管理最佳实践）

## [A] 当前主要任务（⏳进行中）
实现中枢服务平台完整部署（阶段1核心目标）
- 目标：构建稳定可扩展的中枢服务平台，实现数据拉取、监控告警、CI/CD Runner、OSS备份
- 当前重点：Runner自启服务 + Grafana高级配置 + EODHD完整套餐数据拉取
- 验收标准：Runner在线、Grafana多数据源配置、数据每日自动拉取、钉钉告警测试通过

## [B] 上次对话关键结论（✅ 已确认）
- 三服务器架构分工明确：中枢(开发/数据/监控) + 训练(GPU) + 推理(低延迟)
- 开发战略分5阶段推进，当前重点阶段1中枢服务平台完善
- VectorBT回测框架 + ONNX推理服务作为核心技术栈
- 企业级监控告警体系：Grafana + Prometheus + 钉钉/Slack
- OSS备份使用OIDC零密钥同步，确保数据安全

## [C] 待确认的问题（❓待讨论）
1. VectorBT容器化部署的最佳实践和性能优化策略
2. 多因子模型训练数据预处理的标准化流程
3. 推理服务器ONNX模型的自动更新机制
4. 训练服务器GPU资源分配和成本控制方案

## [D] 最近截图与文件引用
- 服务器架构图：@screenshots/server_architecture.png
- 当前工单文档：
  - @docs/issues/[AI-EXEC] 迭代提升：部署 Actions Runner + Grafana 监控
  - @docs/issues/[AI-EXEC] 升级版：配置数据拉取 + OSS 备份
- 核心配置文件：
  - @configs/grafana/grafana.ini
  - @configs/grafana/provisioning/datasources/prometheus.yml
  - @scripts/deploy/pull_eodhd_full.sh
- 部署报告：@docs/reports/runner_grafana_advanced_log.md

## [E] 临时实验代码
```python
# 多因子数据预处理示例
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def preprocess_multi_factor_data(data_path: str) -> pd.DataFrame:
    """多因子数据标准化预处理"""
    df = pd.read_csv(data_path)

    # 技术指标标准化
    technical_cols = ['rsi', 'macd', 'bb_upper', 'bb_lower']
    scaler = StandardScaler()
    df[technical_cols] = scaler.fit_transform(df[technical_cols])

    # 事件标记
    df['earnings_event'] = df['news'].str.contains('earnings', case=False).astype(int)
    df['fed_event'] = df['news'].str.contains('fed|利率', case=False).astype(int)

    return df

# 测试代码
if __name__ == "__main__":
    # 待实际数据路径测试
    pass
```

## 分支管理（多线并行开发上下文 - 严格遵循最佳实践）
### 分支1：主线 - 风险管理优化（当前活跃 ★）
- 目标：在严格控制亏损（单笔风险≤1-2%，最大回撤目标<15%，总浮亏≤10-12%）的前提下，实现收益最大化。通过多指标共振信号生成（趋势跟踪 + 超买超卖过滤）、EODHD API 驱动的高级新闻/经济事件过滤器（实时事件 + 情感分析避开负面冲击）、严格杠杆控制（JustMarkets最高1:3000但EA内部有效杠杆限1:100-500）、动态仓位调整（盈利期适度放大暴露）、至少1:2风险回报比、部分平仓/追踪止损锁定利润，以及参考部分Kelly准则优化长期复利增长，确保资金曲线平稳向上，支持JustMarkets实盘长期稳定运行。
- 最新进展：
  - 已实现单笔风险不超过账户余额1-2%的固定/动态仓位计算逻辑（基于账户余额实时调整，严格控制JustMarkets高杠杆暴露）
  - 已集成总浮亏超过10%时自动暂停所有新开仓功能 + 每日最大亏损限额（当日亏损超3%暂停至次日）
  - 已添加最大同时持仓品种数限制（默认3-5个）和防重单逻辑（基于信号ID + 5分钟时间窗口）
  - 引入风险回报比≥1:2的信号过滤（潜在盈利至少是风险的2倍）
  - 已添加部分平仓机制（盈利达到50%目标时平一半仓位锁定利润）
  - 初步集成信号生成框架：MACD金叉/死叉 + RSI超买超卖过滤 + Bollinger Bands触带确认 + ADX趋势强度过滤
  - 已实现新闻过滤器原型：基于MT5内置Calendar函数 + EODHD Economic Events Calendar API + News Feed API初步集成（MQL5 WebRequest调用，检测高影响力新闻/负面情感事件，并在新闻前30分钟 + 后60分钟禁止开新仓或强制降杠杆，支持特定货币过滤）
  - 日志记录统一格式，支持风险事件、新闻事件、EODHD API调用（含响应状态）、JustMarkets账户状态、当前杠杆使用单独标记和回撤监控
  - 已接入EODHD API（当前计划：EOD Historical Data Extended + Intraday），可用Historical/Intraday数据进行信号回测，Calendar/News Data用于实时经济事件与情感过滤
  - EA已全面适配JustMarkets账户特性：支持MT5平台、低点差（优先Raw Spread/Pro账户类型）、免息Swap（适合趋势持仓过夜）、最高杠杆1:3000（内部严格限制有效杠杆，防止滥用）
- 当前问题/下一步：
  - 完善多指标共振信号生成模块：核心策略为趋势跟踪（均线交叉 + MACD确认 + ADX>25过滤强趋势）+ 震荡过滤（RSI<30买/>70卖 + Bollinger Bands下轨买/上轨卖），确保信号胜率>60%、盈亏比>1:2.5；利用EODHD Intraday/Historical Data + JustMarkets低点差环境进行参数优化和回测
  - 实现EODHD API完整集成：全面使用Economic Events Calendar API + News Feed API构建高级新闻过滤器（每分钟WebRequest查询，支持高影响力事件、特定国家/货币过滤、新闻情感分数阈值过滤负面冲击）；触发时强制降有效杠杆至1:50-100并暂停开仓；集成错误处理、重试机制、JSON解析（推荐第三方库）；添加Alert提醒即将事件
  - 实现高杠杆安全使用机制：即使JustMarkets提供1:3000杠杆，EA内部严格按1:100-500有效杠杆计算仓位；盈利期适度放大至1:300-500（参考Half-Kelly准则），连续亏损/回撤>5%/EODHD负面新闻期自动降至1:50-100；集成最大仓位上限和回撤触发降杠杆函数
  - 实现更先进的动态仓位调整：参考部分Kelly准则（Half-Kelly或Fractional Kelly），根据近期胜率和平均盈亏比自动放大/缩小仓位（盈利期适度利用JustMarkets高杠杆增加风险暴露以最大化复利，亏损期保守减仓）
  - 加入波动率适应机制（如基于ATR或EODHD Intraday数据动态调整止损距离、仓位大小和信号阈值，波动大时减小仓位）
  - 集成追踪止损（Trailing Stop）和盈亏平衡（Breakeven）功能，进一步锁定趋势利润并控制回撤
  - 增加最大回撤监控模块（回撤接近12-15%时自动减仓或暂停）
  - 探索EODHD Fundamental Data / Dividends Data辅助基本面过滤（长期趋势增强）
  - 优先在JustMarkets Raw Spread / Pro账户实盘部署（最低点差 + 无佣金 + 免息Swap），并进行至少6-12个月的模拟盘+前向测试（利用EODHD数据覆盖多品种、多周期、多次重大新闻事件），验证EODHD过滤器有效性和整体风控表现，目标夏普比率>1.5、年化收益>30%（低回撤）
- 最后更新：2025-12-16
**分支2：实验性 - VectorBT容器化优化（探索中 ⚠）**
* 目标：优化VectorBT在容器环境下的性能和资源利用率
* 最新进展：基础容器镜像构建完成，初步测试显示内存使用合理
* 当前问题/下一步：评估GPU加速选项，测试大规模回测性能，优化镜像大小
* 最后更新：2025-12-14
**分支3：开发环境发展改革分支（新建 🔥）**
* 目标：基于三服务器分工方案，完善中枢服务平台生产化配置，建立跨服务器自动化协作框架，实现开发环境效率优化，为风险管理主分支提供稳定基础
* 最新进展：改革分支计划文档已创建，包含跨服务器自动化部署、全服务器健康检查、多级别监控告警、Docker容器化服务、CI/CD工作流
* 当前问题/下一步：
  - 执行跨服务器SSH密钥自动化配置
  - 部署Docker容器化服务栈
  - 完善多级别告警规则
  - 运行全服务器健康检查验证
  - 合并分支前进行完整验收测试
* 验收标准：中枢服务99.9%可用性、跨服务器自动化协作正常、监控覆盖所有关键组件、开发效率提升30%
* 最后更新：2025-12-16
**分支4：备用方案 - 多因子模型架构设计（已搁置 ⏸）**
* 目标：设计支持价格+技术+基本面+事件的统一多因子模型框架
* 最新进展：数据预处理模板脚本完成，特征工程基本框架搭建
* 当前问题/下一步：等待改革分支完成后重启，当前优先级较低
* 最后更新：2025-12-13
**分支5：新想法 - 推理服务自动伸缩（空闲）**
* 可用于实现基于负载的自动扩容和成本优化，直接在此开启新分支

"""
回测报告生成器 - Tearsheet with Deflated Sharpe Ratio

核心功能：
1. 计算 Deflated Sharpe Ratio (DSR) - 概率调整后的夏普比率
2. 生成 HTML 交互式报告
3. 绘制关键指标图表（累计收益、回撤、月度热力图）
4. 提供详细的交易统计

参考文献：
- Bailey, D. H., & López de Prado, M. (2014). "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality"
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def calculate_deflated_sharpe_ratio(
    observed_sr: float,
    n_trials: int,
    n_observations: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    sr_std: Optional[float] = None
) -> Dict[str, float]:
    """
    计算 Deflated Sharpe Ratio (DSR)

    公式：
        DSR = Z-score[(SR - E[max(SR_i)]) / std(SR)]

    其中：
        - SR: 观测到的 Sharpe Ratio
        - E[max(SR_i)]: 在 n_trials 次试验中期望的最大 SR（随机情况下）
        - std(SR): SR 的标准差

    Args:
        observed_sr: 观测到的 Sharpe Ratio
        n_trials: 策略试验次数（调参次数）
        n_observations: 样本数量（交易天数）
        skewness: 收益率偏度
        kurtosis: 收益率峰度
        sr_std: SR 的标准差（可选，如果为 None 则自动计算）

    Returns:
        Dict: 包含 DSR 及相关统计量
            - dsr: Deflated Sharpe Ratio
            - expected_max_sr: 期望最大 SR
            - sr_std: SR 标准差
            - dsr_pvalue: DSR 的 p 值
            - is_significant: 是否显著（p < 0.05）
    """
    # 1. 计算期望最大 SR (基于极值理论)
    # 使用 Euler-Mascheroni 常数
    euler_mascheroni = 0.5772156649

    # 期望最大值公式：E[max(Z)] ≈ sqrt(2*log(N)) - (log(log(N)) + log(4π)) / (2*sqrt(2*log(N)))
    # 简化版：使用正态分布的极值期望
    expected_max_sr = np.sqrt(2 * np.log(n_trials)) - (
        (np.log(np.log(n_trials)) + np.log(4 * np.pi)) / (2 * np.sqrt(2 * np.log(n_trials)))
    )

    # 2. 计算 SR 的标准差
    if sr_std is None:
        # 考虑非正态性调整
        # std(SR) ≈ sqrt((1 + SR^2 - skew*SR + (kurtosis-3)/4 * SR^2) / N)
        sr_variance = (
            1.0
            - skewness * observed_sr
            + ((kurtosis - 3.0) / 4.0) * (observed_sr ** 2)
        ) / n_observations

        sr_std = np.sqrt(max(sr_variance, 1e-6))

    # 3. 计算 DSR
    # DSR = (SR - E[max(SR)]) / std(SR)
    dsr = (observed_sr - expected_max_sr) / (sr_std + 1e-10)

    # 4. 计算 p-value
    # DSR 服从标准正态分布
    dsr_pvalue = 1.0 - stats.norm.cdf(dsr)

    # 5. 判断显著性
    is_significant = dsr_pvalue < 0.05

    result = {
        'dsr': dsr,
        'observed_sr': observed_sr,
        'expected_max_sr': expected_max_sr,
        'sr_std': sr_std,
        'dsr_pvalue': dsr_pvalue,
        'is_significant': is_significant,
        'n_trials': n_trials,
        'n_observations': n_observations,
        'interpretation': _interpret_dsr(dsr)
    }

    return result


def _interpret_dsr(dsr: float) -> str:
    """
    解释 DSR 值

    Args:
        dsr: Deflated Sharpe Ratio

    Returns:
        str: 解释文本
    """
    if dsr >= 2.0:
        return "🟢 非常显著 - 策略表现优异，过拟合风险低"
    elif dsr >= 1.0:
        return "🟡 较为显著 - 策略表现良好，但需谨慎验证"
    elif dsr >= 0.0:
        return "🟠 轻微显著 - 策略表现一般，可能存在过拟合"
    else:
        return "🔴 不显著 - 策略表现不佳，很可能是过拟合或数据窥探的结果"


class TearSheetGenerator:
    """
    回测报告生成器

    生成包含以下内容的 HTML 报告：
    1. 策略概览（收益、风险、DSR）
    2. 累计收益曲线
    3. 回撤分析
    4. 月度收益热力图
    5. 交易统计
    6. 风险指标
    """

    def __init__(self, output_dir: str = 'backtest_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # 设置绘图风格
        sns.set_style('whitegrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10

    def generate_report(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        trades: Optional[pd.DataFrame] = None,
        n_trials: int = 100,
        strategy_name: str = "ML Strategy",
        output_filename: str = "tearsheet.html"
    ):
        """
        生成完整回测报告

        Args:
            returns: 策略日收益率序列
            benchmark_returns: 基准日收益率序列（可选）
            trades: 交易记录 DataFrame
            n_trials: 策略试验次数
            strategy_name: 策略名称
            output_filename: 输出文件名
        """
        logger.info(f"开始生成回测报告 - 策略: {strategy_name}")

        # 1. 计算核心指标
        metrics = self._calculate_metrics(returns, n_trials)

        # 2. 计算 DSR
        dsr_result = calculate_deflated_sharpe_ratio(
            observed_sr=metrics['sharpe_ratio'],
            n_trials=n_trials,
            n_observations=len(returns),
            skewness=metrics['skewness'],
            kurtosis=metrics['kurtosis']
        )

        metrics.update(dsr_result)

        # 3. 生成图表
        self._plot_cumulative_returns(returns, benchmark_returns, strategy_name)
        self._plot_drawdown(returns, strategy_name)
        self._plot_monthly_heatmap(returns, strategy_name)

        # 4. 生成 HTML 报告
        html_path = self.output_dir / output_filename
        self._generate_html_report(
            metrics=metrics,
            trades=trades,
            strategy_name=strategy_name,
            output_path=html_path
        )

        logger.info(f"✅ 报告生成完成: {html_path}")

        return metrics

    def _calculate_metrics(self, returns: pd.Series, n_trials: int) -> Dict:
        """
        计算策略指标

        Args:
            returns: 日收益率序列
            n_trials: 试验次数

        Returns:
            Dict: 指标字典
        """
        # 基础统计
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        annual_volatility = returns.std() * np.sqrt(252)

        # Sharpe Ratio
        risk_free_rate = 0.02  # 假设无风险利率 2%
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (annual_return - risk_free_rate) / downside_std if downside_std > 0 else 0

        # Maximum Drawdown
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.cummax()
        drawdown = (cum_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar Ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 高阶矩
        skewness = returns.skew()
        kurtosis = returns.kurtosis() + 3  # 转换为峰度（非超额峰度）

        # 胜率
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

        metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'win_rate': win_rate,
            'n_observations': len(returns),
            'n_trials': n_trials
        }

        return metrics

    def _plot_cumulative_returns(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series],
        strategy_name: str
    ):
        """绘制累计收益曲线"""
        fig, ax = plt.subplots(figsize=(14, 6))

        cum_returns = (1 + returns).cumprod()
        cum_returns.plot(ax=ax, label=strategy_name, linewidth=2)

        if benchmark_returns is not None:
            cum_benchmark = (1 + benchmark_returns).cumprod()
            cum_benchmark.plot(ax=ax, label='Benchmark', linewidth=2, alpha=0.7)

        ax.set_title('Cumulative Returns', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative Return')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'cumulative_returns.png', dpi=150)
        plt.close()

    def _plot_drawdown(self, returns: pd.Series, strategy_name: str):
        """绘制回撤曲线"""
        fig, ax = plt.subplots(figsize=(14, 6))

        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.cummax()
        drawdown = (cum_returns - running_max) / running_max

        drawdown.plot(ax=ax, color='red', linewidth=2, alpha=0.7)
        ax.fill_between(drawdown.index, 0, drawdown, color='red', alpha=0.3)

        ax.set_title('Drawdown', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'drawdown.png', dpi=150)
        plt.close()

    def _plot_monthly_heatmap(self, returns: pd.Series, strategy_name: str):
        """绘制月度收益热力图"""
        # 转换为月度收益
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

        # 构建年月矩阵
        monthly_returns_df = pd.DataFrame({
            'Year': monthly_returns.index.year,
            'Month': monthly_returns.index.month,
            'Return': monthly_returns.values
        })

        pivot_table = monthly_returns_df.pivot_table(
            values='Return', index='Year', columns='Month', aggfunc='first'
        )

        # 绘制热力图
        fig, ax = plt.subplots(figsize=(14, 8))

        sns.heatmap(
            pivot_table * 100,  # 转换为百分比
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            center=0,
            cbar_kws={'label': 'Monthly Return (%)'},
            ax=ax
        )

        ax.set_title('Monthly Returns Heatmap', fontsize=16, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')

        # 设置月份标签
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels(month_labels)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'monthly_heatmap.png', dpi=150)
        plt.close()

    def _generate_html_report(
        self,
        metrics: Dict,
        trades: Optional[pd.DataFrame],
        strategy_name: str,
        output_path: Path
    ):
        """生成 HTML 报告"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{strategy_name} - Backtest Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #555;
                    border-bottom: 2px solid #ddd;
                    padding-bottom: 5px;
                    margin-top: 30px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .metric-label {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    color: #333;
                    font-size: 24px;
                    font-weight: bold;
                }}
                .dsr-section {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .chart-container {{
                    background: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .chart-container img {{
                    width: 100%;
                    height: auto;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                }}
                .positive {{ color: #4CAF50; }}
                .negative {{ color: #f44336; }}
            </style>
        </head>
        <body>
            <h1>📊 {strategy_name} - 回测报告</h1>
            <p>生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="dsr-section">
                <h2 style="color: white; border: none;">🎯 Deflated Sharpe Ratio (DSR)</h2>
                <p><strong>DSR 值: {metrics['dsr']:.3f}</strong></p>
                <p>观测 Sharpe Ratio: {metrics['observed_sr']:.3f}</p>
                <p>期望最大 SR (随机情况): {metrics['expected_max_sr']:.3f}</p>
                <p>p-value: {metrics['dsr_pvalue']:.4f}</p>
                <p>显著性: {'✅ 显著 (p < 0.05)' if metrics['is_significant'] else '❌ 不显著'}</p>
                <p><strong>{metrics['interpretation']}</strong></p>
                <p style="font-size: 12px; margin-top: 10px;">
                    * DSR 考虑了多重测试、回测过拟合和收益率非正态性<br>
                    * 试验次数 (n_trials): {metrics['n_trials']}, 观测数: {metrics['n_observations']}
                </p>
            </div>

            <h2>📈 核心指标</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">总收益率</div>
                    <div class="metric-value {'positive' if metrics['total_return'] > 0 else 'negative'}">
                        {metrics['total_return']:.2%}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">年化收益率</div>
                    <div class="metric-value {'positive' if metrics['annual_return'] > 0 else 'negative'}">
                        {metrics['annual_return']:.2%}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">年化波动率</div>
                    <div class="metric-value">{metrics['annual_volatility']:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{metrics['sharpe_ratio']:.3f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sortino Ratio</div>
                    <div class="metric-value">{metrics['sortino_ratio']:.3f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">最大回撤</div>
                    <div class="metric-value negative">{metrics['max_drawdown']:.2%}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Calmar Ratio</div>
                    <div class="metric-value">{metrics['calmar_ratio']:.3f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">胜率</div>
                    <div class="metric-value">{metrics['win_rate']:.2%}</div>
                </div>
            </div>

            <h2>📉 收益曲线</h2>
            <div class="chart-container">
                <img src="cumulative_returns.png" alt="Cumulative Returns">
            </div>

            <h2>📊 回撤分析</h2>
            <div class="chart-container">
                <img src="drawdown.png" alt="Drawdown">
            </div>

            <h2>🗓️ 月度收益热力图</h2>
            <div class="chart-container">
                <img src="monthly_heatmap.png" alt="Monthly Heatmap">
            </div>

            <h2>📋 统计摘要</h2>
            <table>
                <tr>
                    <th>指标</th>
                    <th>值</th>
                </tr>
                <tr>
                    <td>偏度 (Skewness)</td>
                    <td>{metrics['skewness']:.3f}</td>
                </tr>
                <tr>
                    <td>峰度 (Kurtosis)</td>
                    <td>{metrics['kurtosis']:.3f}</td>
                </tr>
                <tr>
                    <td>观测数</td>
                    <td>{metrics['n_observations']}</td>
                </tr>
                <tr>
                    <td>试验次数</td>
                    <td>{metrics['n_trials']}</td>
                </tr>
            </table>

            <footer style="margin-top: 40px; text-align: center; color: #666; font-size: 12px;">
                <p>MT5-CRS 策略回测引擎 | Generated by TearSheetGenerator</p>
            </footer>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        logger.info(f"HTML 报告已生成: {output_path}")

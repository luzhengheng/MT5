"""
MA Parameter Sweeper - Automated Parameter Space Exploration
TASK #112: Phase 5 Alpha Generation

This module provides a high-level interface for managing MA crossover
parameter sweeps, including parameter generation, result aggregation,
and visualization.

Key Features:
- Automated parameter range generation
- Result aggregation and ranking
- Heatmap generation for visualization
- Integration with VectorBTBacktester

Author: MT5-CRS Development Team
Date: 2026-01-15
Protocol: v4.3 (Zero-Trust Edition)
"""

import logging
from typing import Tuple, Dict, List, Optional
import numpy as np
import pandas as pd
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class MAParameterSweeper:
    """
    Manager class for MA crossover parameter sweep operations.

    This class handles:
    - Parameter space definition (fast MA, slow MA ranges)
    - Sweep execution coordination
    - Result analysis and visualization
    - Artifact management

    Attributes:
        data: Input DataFrame with OHLCV data
        name: Identifier for the asset/dataset
        results_df: DataFrame containing sweep results
    """

    def __init__(
        self,
        data: pd.DataFrame,
        name: str = 'EURUSD_D1',
        output_dir: Optional[str] = None
    ):
        """
        Initialize parameter sweeper.

        Args:
            data: DataFrame with OHLCV data [timestamp, open, high, low, close, volume]
            name: Asset name/identifier (used for logging and file naming)
            output_dir: Output directory for artifacts (default: current directory)

        Raises:
            ValueError: If data is empty or missing required columns
        """
        if data.empty:
            raise ValueError("Data cannot be empty")

        required_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(data.columns):
            raise ValueError(f"Missing required columns. Need: {required_cols}")

        self.data = data
        self.name = name
        self.output_dir = output_dir or '.'
        self.results_df = None
        self.elapsed_time = None

        logger.info(f"[MAParameterSweeper] Initialized for {name} "
                   f"({len(data)} bars)")

    def generate_parameter_ranges(
        self,
        fast_range: Tuple[int, int, int] = (5, 50, 5),
        slow_range: Tuple[int, int, int] = (50, 200, 10)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate parameter ranges using np.arange.

        Args:
            fast_range: (start, stop, step) for fast MA periods
            slow_range: (start, stop, step) for slow MA periods

        Returns:
            fast_params, slow_params: Numpy arrays of parameter values

        Example:
            fast_params, slow_params = sweeper.generate_parameter_ranges(
                fast_range=(5, 50, 5),
                slow_range=(50, 200, 10)
            )
            # fast_params = [5, 10, 15, ..., 45]
            # slow_params = [50, 60, 70, ..., 190]
        """
        fast_start, fast_stop, fast_step = fast_range
        slow_start, slow_stop, slow_step = slow_range

        fast_params = np.arange(fast_start, fast_stop, fast_step)
        slow_params = np.arange(slow_start, slow_stop, slow_step)

        n_fast = len(fast_params)
        n_slow = len(slow_params)
        n_combinations = n_fast * n_slow

        logger.info(f"[MAParameterSweeper] Generated parameter ranges:")
        logger.info(f"  Fast MA: {fast_params[0]}-{fast_params[-1]} "
                   f"(step {fast_step}), count: {n_fast}")
        logger.info(f"  Slow MA: {slow_params[0]}-{slow_params[-1]} "
                   f"(step {slow_step}), count: {n_slow}")
        logger.info(f"  Total combinations: {n_combinations}")

        return fast_params, slow_params

    def validate_results(self, results_df: pd.DataFrame) -> bool:
        """
        Validate sweep results.

        Args:
            results_df: Results DataFrame from VectorBTBacktester.run()

        Returns:
            True if results are valid, False otherwise

        Checks:
            - DataFrame not empty
            - Required columns present
            - No NaN values in critical metrics
            - Valid value ranges (e.g., Sharpe ratio, returns)
        """
        if results_df is None or results_df.empty:
            logger.error("[MAParameterSweeper] Results DataFrame is empty")
            return False

        required_cols = {'fast_ma', 'slow_ma', 'sharpe_ratio', 'total_return', 'max_drawdown'}
        if not required_cols.issubset(results_df.columns):
            logger.error(f"[MAParameterSweeper] Missing columns. Need: {required_cols}")
            return False

        # Check for critical NaN values
        critical_cols = ['fast_ma', 'slow_ma', 'sharpe_ratio']
        if results_df[critical_cols].isna().any().any():
            logger.warning("[MAParameterSweeper] Found NaN values in critical columns")

        logger.info(f"[MAParameterSweeper] Validated {len(results_df)} result rows")
        return True

    def save_results_csv(self, filepath: Optional[str] = None) -> str:
        """
        Save results to CSV file.

        Args:
            filepath: Output file path (default: {name}_results.csv)

        Returns:
            Path to saved file

        Raises:
            RuntimeError: If results_df is None
        """
        if self.results_df is None:
            raise RuntimeError("No results to save. Run sweep first.")

        if filepath is None:
            filepath = os.path.join(self.output_dir, f"{self.name}_results.csv")

        self.results_df.to_csv(filepath, index=False)
        logger.info(f"[MAParameterSweeper] Saved results to {filepath}")
        return filepath

    def generate_heatmap_data(self) -> Dict:
        """
        Generate heatmap data from results for visualization.

        Returns:
            Dictionary with heatmap data suitable for plotting

        Structure:
            {
                'metric': 'sharpe_ratio',
                'data': 2D array (fast_ma_params × slow_ma_params),
                'fast_ma_values': list of fast MA values,
                'slow_ma_values': list of slow MA values,
                'min_value': float,
                'max_value': float,
            }
        """
        if self.results_df is None or self.results_df.empty:
            raise RuntimeError("No results available for heatmap generation")

        # Pivot results for heatmap
        heatmap_data = self.results_df.pivot_table(
            index='fast_ma',
            columns='slow_ma',
            values='sharpe_ratio',
            aggfunc='first'
        )

        return {
            'metric': 'sharpe_ratio',
            'data': heatmap_data.values,
            'fast_ma_values': heatmap_data.index.tolist(),
            'slow_ma_values': heatmap_data.columns.tolist(),
            'min_value': heatmap_data.min().min(),
            'max_value': heatmap_data.max().max(),
        }

    def get_top_performers(self, metric: str = 'sharpe_ratio', top_n: int = 10) -> pd.DataFrame:
        """
        Get top N parameter combinations by specified metric.

        Args:
            metric: Metric to rank by (default: 'sharpe_ratio')
            top_n: Number of top results to return

        Returns:
            DataFrame with top N results, sorted by metric descending
        """
        if self.results_df is None or self.results_df.empty:
            raise RuntimeError("No results available")

        if metric not in self.results_df.columns:
            raise ValueError(f"Metric '{metric}' not in results columns: "
                           f"{list(self.results_df.columns)}")

        return self.results_df.nlargest(top_n, metric)[
            ['fast_ma', 'slow_ma', metric, 'total_return', 'max_drawdown', 'num_trades']
        ]

    def get_summary_report(self) -> str:
        """
        Generate human-readable summary report.

        Returns:
            Formatted report string

        Includes:
            - Parameter space size
            - Performance statistics
            - Top performers
            - Execution time
        """
        if self.results_df is None:
            return "No results available"

        report = []
        report.append("=" * 80)
        report.append(f"MA Parameter Sweep Summary - {self.name}")
        report.append("=" * 80)
        report.append(f"Total combinations scanned: {len(self.results_df)}")
        if self.elapsed_time:
            report.append(f"Execution time: {self.elapsed_time:.2f} seconds")
            report.append(f"Combinations/second: {len(self.results_df) / self.elapsed_time:.1f}")

        report.append("\n" + "-" * 80)
        report.append("Performance Statistics")
        report.append("-" * 80)

        for metric in ['sharpe_ratio', 'total_return', 'max_drawdown']:
            if metric in self.results_df.columns:
                col_data = self.results_df[metric]
                report.append(f"{metric}:")
                report.append(f"  Mean:   {col_data.mean():>10.4f}")
                report.append(f"  Median: {col_data.median():>10.4f}")
                report.append(f"  Min:    {col_data.min():>10.4f}")
                report.append(f"  Max:    {col_data.max():>10.4f}")

        report.append("\n" + "-" * 80)
        report.append("Top 5 Performers (by Sharpe Ratio)")
        report.append("-" * 80)

        top_5 = self.get_top_performers('sharpe_ratio', 5)
        for idx, row in top_5.iterrows():
            report.append(f"MA({row['fast_ma']:.0f}, {row['slow_ma']:.0f}): "
                        f"Sharpe={row['sharpe_ratio']:>7.4f}, "
                        f"Return={row['total_return']:>8.2%}, "
                        f"DD={row['max_drawdown']:>7.2%}, "
                        f"Trades={row['num_trades']:>4.0f}")

        report.append("=" * 80)
        return "\n".join(report)

    def print_summary(self) -> None:
        """Print summary report to console."""
        print(self.get_summary_report())

    def generate_html_heatmap(self, filepath: Optional[str] = None) -> str:
        """
        Generate interactive HTML heatmap.

        Args:
            filepath: Output HTML file path

        Returns:
            Path to generated HTML file

        Creates an interactive heatmap showing Sharpe ratio across parameter space.
        Requires plotly library if fancy visualization is desired,
        but this version uses simple HTML table as fallback.
        """
        if self.results_df is None or self.results_df.empty:
            raise RuntimeError("No results available")

        if filepath is None:
            filepath = os.path.join(self.output_dir, f"{self.name}_heatmap.html")

        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Prepare heatmap data
            heatmap_info = self.generate_heatmap_data()

            # Create figure
            fig = go.Figure(
                data=go.Heatmap(
                    z=heatmap_info['data'],
                    x=heatmap_info['slow_ma_values'],
                    y=heatmap_info['fast_ma_values'],
                    colorscale='RdYlGn',
                    colorbar=dict(title='Sharpe Ratio'),
                    hovertemplate='Fast MA: %{y}<br>Slow MA: %{x}<br>Sharpe: %{z:.4f}<extra></extra>'
                )
            )

            fig.update_layout(
                title=f'MA Crossover Sharpe Ratio Heatmap - {self.name}',
                xaxis_title='Slow MA Period',
                yaxis_title='Fast MA Period',
                height=600,
                width=900,
            )

            fig.write_html(filepath)
            logger.info(f"[MAParameterSweeper] Generated heatmap: {filepath}")

        except ImportError:
            logger.warning("[MAParameterSweeper] Plotly not available, generating simple HTML")

            # Fallback: simple HTML table
            html_content = self._generate_simple_html_table(filepath)

        return filepath

    def _generate_simple_html_table(self, filepath: str) -> str:
        """Generate simple HTML table as fallback."""
        top_results = self.get_top_performers('sharpe_ratio', 20)

        html = """
        <html>
        <head>
            <title>MA Parameter Sweep Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>MA Crossover Parameter Sweep Results</h1>
            <h2>""" + self.name + """</h2>
        """

        # Summary stats
        html += f"""
            <div>
                <p><strong>Total Combinations:</strong> {len(self.results_df)}</p>
                <p><strong>Mean Sharpe Ratio:</strong> {self.results_df['sharpe_ratio'].mean():.4f}</p>
                <p><strong>Max Sharpe Ratio:</strong> {self.results_df['sharpe_ratio'].max():.4f}</p>
            </div>
        """

        # Results table
        html += """
            <table>
                <tr>
                    <th>Fast MA</th>
                    <th>Slow MA</th>
                    <th>Sharpe Ratio</th>
                    <th>Total Return</th>
                    <th>Max Drawdown</th>
                    <th>Num Trades</th>
                </tr>
        """

        for _, row in top_results.iterrows():
            html += f"""
                <tr>
                    <td>{row['fast_ma']:.0f}</td>
                    <td>{row['slow_ma']:.0f}</td>
                    <td>{row['sharpe_ratio']:.4f}</td>
                    <td>{row['total_return']:.2%}</td>
                    <td>{row['max_drawdown']:.2%}</td>
                    <td>{row['num_trades']:.0f}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """

        with open(filepath, 'w') as f:
            f.write(html)

        logger.info(f"[MAParameterSweeper] Generated HTML table: {filepath}")
        return filepath

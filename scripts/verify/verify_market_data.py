#!/usr/bin/env python3
"""
Market Data Validation Script

Purpose:
  Validate data integrity and detect distribution shifts before enabling
  live trading on new symbols (e.g., GBPUSD).

Usage:
  python3 scripts/verify_market_data.py --symbol GBPUSD --baseline EURUSD

Checks:
  1. Distribution Shift Detection (K-S Test)
  2. Data Quality Validation
  3. Model Confidence Analysis
  4. Feature Correlation Check
  5. Validation Report Generation

Exit Codes:
  0 - All validations passed, safe to enable live trading
  1 - Validation failed, DO NOT enable live trading
  2 - Script error (missing data, etc.)
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketDataValidator:
    """Validates market data for new trading symbols"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_lake = project_root / 'data_lake'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'UNKNOWN',
            'recommendation': '',
        }

    def load_feature_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Load feature data for a given symbol

        Args:
            symbol: Trading symbol (EURUSD, GBPUSD, etc.)
            days: Number of recent days to load

        Returns:
            DataFrame with features
        """
        # Try different feature directories
        feature_dirs = [
            self.data_lake / 'features_advanced',
            self.data_lake / 'features_daily',
            self.data_lake / 'features',
        ]

        for feature_dir in feature_dirs:
            symbol_file = feature_dir / f'{symbol}.parquet'
            if symbol_file.exists():
                logger.info(f"Loading {symbol} data from {symbol_file}")
                df = pd.read_parquet(symbol_file)

                # Filter to recent days
                if 'timestamp' in df.columns:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    df = df[pd.to_datetime(df['timestamp']) >= cutoff_date]

                logger.info(f"Loaded {len(df)} rows for {symbol}")
                return df

        raise FileNotFoundError(f"No feature data found for {symbol}")

    def check_data_quality(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Check basic data quality metrics

        Args:
            symbol: Trading symbol
            df: Feature DataFrame

        Returns:
            Dict with quality check results
        """
        logger.info(f"Checking data quality for {symbol}...")

        checks = {}

        # 1. Missing values
        missing_pct = (df.isnull().sum() / len(df)) * 100
        max_missing = missing_pct.max()
        checks['missing_values'] = {
            'max_missing_pct': float(max_missing),
            'threshold': 1.0,
            'passed': max_missing < 1.0,
            'details': missing_pct[missing_pct > 0].to_dict() if max_missing > 0 else {}
        }

        # 2. Duplicate timestamps
        if 'timestamp' in df.columns:
            n_duplicates = df['timestamp'].duplicated().sum()
            checks['duplicate_timestamps'] = {
                'count': int(n_duplicates),
                'threshold': 0,
                'passed': n_duplicates == 0
            }

        # 3. Numeric columns range check
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outliers = {}
        for col in numeric_cols:
            if col not in ['timestamp']:
                q1 = df[col].quantile(0.01)
                q99 = df[col].quantile(0.99)
                outlier_count = ((df[col] < q1) | (df[col] > q99)).sum()
                outlier_pct = (outlier_count / len(df)) * 100

                if outlier_pct > 5.0:  # More than 5% outliers
                    outliers[col] = {
                        'outlier_pct': float(outlier_pct),
                        'q01': float(q1),
                        'q99': float(q99)
                    }

        checks['outliers'] = {
            'columns_with_outliers': len(outliers),
            'threshold': 3,
            'passed': len(outliers) < 3,
            'details': outliers
        }

        # 4. Record count
        checks['record_count'] = {
            'count': len(df),
            'threshold': 100,
            'passed': len(df) >= 100
        }

        # Overall DQ score (simple average)
        passed_count = sum(1 for c in checks.values() if c.get('passed', False))
        dq_score = (passed_count / len(checks)) * 100

        return {
            'symbol': symbol,
            'dq_score': dq_score,
            'checks': checks,
            'passed': dq_score >= 80.0
        }

    def check_distribution_shift(
        self,
        baseline_symbol: str,
        target_symbol: str,
        baseline_df: pd.DataFrame,
        target_df: pd.DataFrame,
        significance: float = 0.05
    ) -> Dict:
        """
        Detect distribution shift using Kolmogorov-Smirnov test

        Args:
            baseline_symbol: Reference symbol (e.g., EURUSD)
            target_symbol: Symbol to validate (e.g., GBPUSD)
            baseline_df: Baseline feature DataFrame
            target_df: Target feature DataFrame
            significance: P-value threshold (default 0.05)

        Returns:
            Dict with distribution shift results
        """
        logger.info(f"Checking distribution shift: {baseline_symbol} vs {target_symbol}...")

        # Find common numeric columns
        baseline_numeric = set(baseline_df.select_dtypes(include=[np.number]).columns)
        target_numeric = set(target_df.select_dtypes(include=[np.number]).columns)
        common_cols = list(baseline_numeric & target_numeric - {'timestamp'})

        if not common_cols:
            return {
                'passed': False,
                'error': 'No common numeric features found'
            }

        ks_results = {}
        significant_shifts = []

        for col in common_cols:
            # Kolmogorov-Smirnov test
            baseline_values = baseline_df[col].dropna()
            target_values = target_df[col].dropna()

            if len(baseline_values) < 10 or len(target_values) < 10:
                continue  # Skip if insufficient data

            ks_stat, p_value = stats.ks_2samp(baseline_values, target_values)

            ks_results[col] = {
                'ks_statistic': float(ks_stat),
                'p_value': float(p_value),
                'shifted': p_value < significance
            }

            if p_value < significance:
                significant_shifts.append(col)

        # Calculate shift percentage
        shift_pct = (len(significant_shifts) / len(common_cols)) * 100 if common_cols else 0

        return {
            'baseline_symbol': baseline_symbol,
            'target_symbol': target_symbol,
            'features_tested': len(common_cols),
            'features_with_shift': len(significant_shifts),
            'shift_percentage': float(shift_pct),
            'threshold': 20.0,  # Allow up to 20% of features to shift
            'passed': shift_pct <= 20.0,
            'significant_shifts': significant_shifts,
            'details': ks_results
        }

    def check_feature_correlation(self, df: pd.DataFrame, threshold: float = 0.95) -> Dict:
        """
        Check for multicollinearity (highly correlated features)

        Args:
            df: Feature DataFrame
            threshold: Correlation threshold (default 0.95)

        Returns:
            Dict with correlation check results
        """
        logger.info("Checking feature correlation...")

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'timestamp' in numeric_cols:
            numeric_cols.remove('timestamp')

        if len(numeric_cols) < 2:
            return {'passed': True, 'message': 'Insufficient features for correlation check'}

        corr_matrix = df[numeric_cols].corr().abs()

        # Find highly correlated pairs
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > threshold:
                    high_corr_pairs.append({
                        'feature_1': corr_matrix.columns[i],
                        'feature_2': corr_matrix.columns[j],
                        'correlation': float(corr_matrix.iloc[i, j])
                    })

        return {
            'high_correlation_pairs': len(high_corr_pairs),
            'threshold': 5,
            'passed': len(high_corr_pairs) < 5,
            'details': high_corr_pairs[:10]  # Limit to top 10
        }

    def check_model_confidence(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Analyze model prediction confidence (if predictions exist)

        Args:
            symbol: Trading symbol
            df: Feature DataFrame

        Returns:
            Dict with confidence check results
        """
        logger.info(f"Checking model confidence for {symbol}...")

        # Look for prediction columns
        pred_cols = [c for c in df.columns if 'prediction' in c.lower() or 'confidence' in c.lower()]

        if not pred_cols:
            return {
                'passed': True,
                'message': 'No prediction columns found (acceptable for new symbols)'
            }

        # Analyze confidence distribution
        confidence_col = pred_cols[0]
        confidence_values = df[confidence_col].dropna()

        if len(confidence_values) == 0:
            return {
                'passed': True,
                'message': 'No confidence values available'
            }

        avg_confidence = confidence_values.mean()
        min_confidence = confidence_values.min()
        max_confidence = confidence_values.max()
        std_confidence = confidence_values.std()

        return {
            'avg_confidence': float(avg_confidence),
            'min_confidence': float(min_confidence),
            'max_confidence': float(max_confidence),
            'std_confidence': float(std_confidence),
            'threshold': 0.6,
            'passed': avg_confidence >= 0.6,
            'message': f'Average confidence: {avg_confidence:.3f}'
        }

    def generate_validation_report(self, output_path: Path = None) -> str:
        """
        Generate human-readable validation report

        Args:
            output_path: Optional path to save report

        Returns:
            Report text
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MARKET DATA VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {self.results['timestamp']}")
        report_lines.append(f"Overall Status: {self.results['overall_status']}")
        report_lines.append("")

        # Summary
        report_lines.append("VALIDATION SUMMARY")
        report_lines.append("-" * 80)
        for check_name, check_result in self.results['checks'].items():
            status = "✅ PASS" if check_result.get('passed', False) else "❌ FAIL"
            report_lines.append(f"{status} - {check_name}")

        report_lines.append("")
        report_lines.append("RECOMMENDATION")
        report_lines.append("-" * 80)
        report_lines.append(self.results['recommendation'])
        report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED RESULTS")
        report_lines.append("-" * 80)
        report_lines.append(json.dumps(self.results, indent=2))

        report_lines.append("")
        report_lines.append("=" * 80)

        report_text = "\n".join(report_lines)

        if output_path:
            output_path.write_text(report_text)
            logger.info(f"Report saved to {output_path}")

        return report_text

    def run_full_validation(
        self,
        target_symbol: str,
        baseline_symbol: str = 'EURUSD',
        days: int = 30
    ) -> bool:
        """
        Run complete validation workflow

        Args:
            target_symbol: Symbol to validate (e.g., GBPUSD)
            baseline_symbol: Reference symbol (e.g., EURUSD)
            days: Number of days to analyze

        Returns:
            True if all validations passed, False otherwise
        """
        logger.info(f"Starting full validation: {target_symbol} vs {baseline_symbol}")
        logger.info("=" * 80)

        try:
            # Load data
            logger.info("Step 1/5: Loading data...")
            baseline_df = self.load_feature_data(baseline_symbol, days)
            target_df = self.load_feature_data(target_symbol, days)

            # Check 1: Data Quality (Target)
            logger.info("Step 2/5: Checking data quality...")
            dq_result = self.check_data_quality(target_symbol, target_df)
            self.results['checks']['data_quality'] = dq_result

            # Check 2: Distribution Shift
            logger.info("Step 3/5: Checking distribution shift...")
            shift_result = self.check_distribution_shift(
                baseline_symbol, target_symbol, baseline_df, target_df
            )
            self.results['checks']['distribution_shift'] = shift_result

            # Check 3: Feature Correlation
            logger.info("Step 4/5: Checking feature correlation...")
            corr_result = self.check_feature_correlation(target_df)
            self.results['checks']['feature_correlation'] = corr_result

            # Check 4: Model Confidence
            logger.info("Step 5/5: Checking model confidence...")
            conf_result = self.check_model_confidence(target_symbol, target_df)
            self.results['checks']['model_confidence'] = conf_result

            # Determine overall status
            all_passed = all(
                check.get('passed', False)
                for check in self.results['checks'].values()
            )

            if all_passed:
                self.results['overall_status'] = 'PASS'
                self.results['recommendation'] = (
                    f"✅ APPROVED: {target_symbol} is safe to enable for live trading.\n"
                    f"All validation checks passed. You may set passive_mode: false."
                )
            else:
                self.results['overall_status'] = 'FAIL'
                failed_checks = [
                    name for name, check in self.results['checks'].items()
                    if not check.get('passed', False)
                ]
                self.results['recommendation'] = (
                    f"❌ REJECTED: {target_symbol} failed validation.\n"
                    f"Failed checks: {', '.join(failed_checks)}\n"
                    f"DO NOT enable live trading until issues are resolved.\n"
                    f"Consider retraining the model with {target_symbol} data."
                )

            return all_passed

        except Exception as e:
            logger.error(f"Validation failed with error: {e}", exc_info=True)
            self.results['overall_status'] = 'ERROR'
            self.results['recommendation'] = f"❌ ERROR: Validation script failed: {e}"
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate market data for new trading symbols'
    )
    parser.add_argument(
        '--symbol',
        required=True,
        help='Target symbol to validate (e.g., GBPUSD)'
    )
    parser.add_argument(
        '--baseline',
        default='EURUSD',
        help='Baseline symbol for comparison (default: EURUSD)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of recent days to analyze (default: 30)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output path for validation report'
    )

    args = parser.parse_args()

    # Initialize validator
    project_root = Path(__file__).parent.parent
    validator = MarketDataValidator(project_root)

    # Run validation
    print(f"\n🔍 Validating {args.symbol} against {args.baseline}...")
    print(f"📊 Analyzing last {args.days} days of data\n")

    passed = validator.run_full_validation(
        target_symbol=args.symbol,
        baseline_symbol=args.baseline,
        days=args.days
    )

    # Generate report
    output_path = args.output or (project_root / 'exports' / f'validation_{args.symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    report = validator.generate_validation_report(output_path)

    print(report)

    # Exit with appropriate code
    if passed:
        print("\n✅ Validation PASSED - Safe to enable live trading")
        return 0
    else:
        print("\n❌ Validation FAILED - DO NOT enable live trading")
        return 1


if __name__ == '__main__':
    sys.exit(main())

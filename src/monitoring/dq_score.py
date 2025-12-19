"""
数据质量评分系统 (DQ Score)
评估数据管道各阶段的数据质量

DQ Score = weighted_sum([
    completeness_score,
    accuracy_score,
    consistency_score,
    timeliness_score,
    validity_score
])
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DQScoreCalculator:
    """数据质量评分计算器"""

    def __init__(self, config: Dict = None):
        """
        初始化

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.weights = self.config.get('weights', {
            'completeness': 0.30,
            'accuracy': 0.25,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.10,
        })

        logger.info("初始化 DQScoreCalculator")
        logger.info(f"权重配置: {self.weights}")

    def calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """
        计算完整性得分

        指标:
        - 缺失值比例
        - 列完整性
        - 行完整性

        Args:
            df: DataFrame

        Returns:
            完整性得分 (0-100)
        """
        if df.empty:
            return 0.0

        # 1. 整体缺失率
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        missing_rate = missing_cells / total_cells

        # 2. 列级别完整性 (至少 80% 的列完整率 > 95%)
        col_completeness = (1 - df.isnull().sum() / len(df))
        good_cols_ratio = (col_completeness > 0.95).sum() / len(df.columns)

        # 3. 行级别完整性 (至少 90% 的行完整率 > 90%)
        row_completeness = (1 - df.isnull().sum(axis=1) / len(df.columns))
        good_rows_ratio = (row_completeness > 0.90).sum() / len(df)

        # 综合得分
        score = (
            (1 - missing_rate) * 50 +  # 整体完整性 50%
            good_cols_ratio * 30 +      # 列完整性 30%
            good_rows_ratio * 20        # 行完整性 20%
        )

        return min(100.0, max(0.0, score))

    def calculate_accuracy_score(self, df: pd.DataFrame) -> float:
        """
        计算准确性得分

        指标:
        - 数值范围异常
        - 无穷值检测
        - 重复记录检测

        Args:
            df: DataFrame

        Returns:
            准确性得分 (0-100)
        """
        if df.empty:
            return 0.0

        score = 100.0

        # 1. 检测无穷值
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            inf_count = np.isinf(df[numeric_cols]).sum().sum()
            total_numeric_cells = len(df) * len(numeric_cols)
            inf_rate = inf_count / total_numeric_cells if total_numeric_cells > 0 else 0
            score -= inf_rate * 30  # 无穷值扣分

        # 2. 检测重复记录
        if 'date' in df.columns and 'symbol' in df.columns:
            duplicates = df.duplicated(subset=['date', 'symbol']).sum()
            dup_rate = duplicates / len(df)
            score -= dup_rate * 30  # 重复记录扣分

        # 3. 检测异常值 (使用 IQR 方法)
        outlier_count = 0
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                outliers = ((df[col] < (Q1 - 3 * IQR)) | (df[col] > (Q3 + 3 * IQR))).sum()
                outlier_count += outliers

        outlier_rate = outlier_count / (len(df) * len(numeric_cols)) if len(numeric_cols) > 0 else 0
        score -= outlier_rate * 40  # 异常值扣分

        return min(100.0, max(0.0, score))

    def calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """
        计算一致性得分

        指标:
        - 数据类型一致性
        - 时间序列连续性
        - 命名规范一致性

        Args:
            df: DataFrame

        Returns:
            一致性得分 (0-100)
        """
        if df.empty:
            return 0.0

        score = 100.0

        # 1. 时间序列连续性 (如果有 date 列)
        if 'date' in df.columns:
            df_sorted = df.sort_values('date')
            dates = pd.to_datetime(df_sorted['date'])

            # 检查日期间隔
            date_diffs = dates.diff()
            expected_freq = pd.Timedelta(days=1)  # 假设日频数据

            # 计算非连续比例
            non_continuous = (date_diffs > expected_freq * 3).sum()  # 超过3天认为不连续
            non_continuous_rate = non_continuous / len(dates) if len(dates) > 1 else 0
            score -= non_continuous_rate * 40

        # 2. 数据类型一致性
        # 检查是否有混合类型列
        mixed_type_cols = 0
        for col in df.columns:
            if df[col].dtype == 'object':
                # 尝试转换为数值
                try:
                    pd.to_numeric(df[col], errors='coerce')
                    # 如果部分可转换,说明类型不一致
                    null_before = df[col].isnull().sum()
                    null_after = pd.to_numeric(df[col], errors='coerce').isnull().sum()
                    if null_after > null_before:
                        mixed_type_cols += 1
                except:
                    pass

        mixed_type_rate = mixed_type_cols / len(df.columns)
        score -= mixed_type_rate * 30

        # 3. 命名规范 (检查列名是否规范)
        irregular_names = 0
        for col in df.columns:
            # 检查是否包含空格或大写字母
            if ' ' in col or col != col.lower():
                irregular_names += 1

        irregular_rate = irregular_names / len(df.columns)
        score -= irregular_rate * 30

        return min(100.0, max(0.0, score))

    def calculate_timeliness_score(self, df: pd.DataFrame, expected_update_time: Optional[datetime] = None) -> float:
        """
        计算及时性得分

        指标:
        - 数据更新延迟
        - 数据覆盖期限

        Args:
            df: DataFrame
            expected_update_time: 期望的更新时间

        Returns:
            及时性得分 (0-100)
        """
        if df.empty:
            return 0.0

        score = 100.0

        # 1. 检查最新数据时间
        if 'date' in df.columns:
            latest_date = pd.to_datetime(df['date']).max()
            now = pd.Timestamp.now()

            # 计算数据延迟 (天数)
            delay_days = (now - latest_date).days

            # 根据延迟扣分
            if delay_days <= 1:
                score -= 0  # 1天内不扣分
            elif delay_days <= 3:
                score -= 10  # 1-3天扣10分
            elif delay_days <= 7:
                score -= 30  # 3-7天扣30分
            else:
                score -= 50  # 超过7天扣50分

        # 2. 检查数据覆盖范围
        if 'date' in df.columns:
            earliest_date = pd.to_datetime(df['date']).min()
            coverage_days = (latest_date - earliest_date).days

            # 至少应该有 30 天数据
            if coverage_days < 30:
                score -= 30
            elif coverage_days < 90:
                score -= 10

        return min(100.0, max(0.0, score))

    def calculate_validity_score(self, df: pd.DataFrame) -> float:
        """
        计算有效性得分

        指标:
        - 业务规则验证
        - 数值范围合理性

        Args:
            df: DataFrame

        Returns:
            有效性得分 (0-100)
        """
        if df.empty:
            return 0.0

        score = 100.0

        # 1. OHLC 逻辑验证 (如果有价格数据)
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # High >= Close >= Low
            invalid_1 = ((df['high'] < df['close']) | (df['close'] < df['low'])).sum()
            # High >= Open >= Low
            invalid_2 = ((df['high'] < df['open']) | (df['open'] < df['low'])).sum()

            invalid_rate = (invalid_1 + invalid_2) / (2 * len(df))
            score -= invalid_rate * 50

        # 2. 成交量非负验证
        if 'volume' in df.columns:
            negative_volume = (df['volume'] < 0).sum()
            negative_rate = negative_volume / len(df)
            score -= negative_rate * 30

        # 3. 情感分数范围验证 (-1 to 1)
        if 'sentiment_score' in df.columns or 'sentiment_mean' in df.columns:
            sent_col = 'sentiment_score' if 'sentiment_score' in df.columns else 'sentiment_mean'
            out_of_range = ((df[sent_col] < -1.5) | (df[sent_col] > 1.5)).sum()
            out_of_range_rate = out_of_range / len(df)
            score -= out_of_range_rate * 20

        return min(100.0, max(0.0, score))

    def calculate_dq_score(self, df: pd.DataFrame, expected_update_time: Optional[datetime] = None) -> Dict:
        """
        计算综合 DQ Score

        Args:
            df: DataFrame
            expected_update_time: 期望更新时间

        Returns:
            包含各维度得分和总分的字典
        """
        logger.info(f"计算 DQ Score: {len(df)} 行, {len(df.columns)} 列")

        # 计算各维度得分
        completeness = self.calculate_completeness_score(df)
        accuracy = self.calculate_accuracy_score(df)
        consistency = self.calculate_consistency_score(df)
        timeliness = self.calculate_timeliness_score(df, expected_update_time)
        validity = self.calculate_validity_score(df)

        # 加权计算总分
        total_score = (
            completeness * self.weights['completeness'] +
            accuracy * self.weights['accuracy'] +
            consistency * self.weights['consistency'] +
            timeliness * self.weights['timeliness'] +
            validity * self.weights['validity']
        )

        result = {
            'timestamp': datetime.now().isoformat(),
            'total_score': round(total_score, 2),
            'completeness': round(completeness, 2),
            'accuracy': round(accuracy, 2),
            'consistency': round(consistency, 2),
            'timeliness': round(timeliness, 2),
            'validity': round(validity, 2),
            'grade': self._get_grade(total_score),
            'records_count': len(df),
            'columns_count': len(df.columns),
        }

        logger.info(f"DQ Score: {result['total_score']:.2f} ({result['grade']})")
        return result

    def _get_grade(self, score: float) -> str:
        """根据得分返回等级"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def calculate_feature_dq_scores(self, features_path: str = "/opt/mt5-crs/data_lake/features_advanced") -> pd.DataFrame:
        """
        计算所有特征文件的 DQ Score

        Args:
            features_path: 特征文件路径

        Returns:
            DQ Score DataFrame
        """
        logger.info(f"计算特征文件 DQ Scores: {features_path}")

        features_path = Path(features_path)
        parquet_files = list(features_path.glob("*.parquet"))

        if not parquet_files:
            logger.warning(f"未找到特征文件: {features_path}")
            return pd.DataFrame()

        results = []

        for file_path in parquet_files:
            try:
                df = pd.read_parquet(file_path)
                symbol = file_path.stem.replace('_features_advanced', '').replace('_features', '')

                dq_result = self.calculate_dq_score(df)
                dq_result['symbol'] = symbol
                dq_result['file_path'] = str(file_path)

                results.append(dq_result)

                logger.info(f"{symbol}: DQ Score = {dq_result['total_score']:.2f}")

            except Exception as e:
                logger.error(f"处理 {file_path} 失败: {e}")

        results_df = pd.DataFrame(results)
        return results_df


def main():
    """测试代码"""
    print("="*80)
    print("DQ Score 计算器测试")
    print("="*80)

    calculator = DQScoreCalculator()

    # 测试数据
    test_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'symbol': 'TEST',
        'open': np.random.uniform(90, 110, 100),
        'high': np.random.uniform(95, 115, 100),
        'low': np.random.uniform(85, 105, 100),
        'close': np.random.uniform(90, 110, 100),
        'volume': np.random.randint(1000000, 10000000, 100),
        'sentiment_mean': np.random.uniform(-0.5, 0.5, 100),
    })

    # 添加一些缺失值
    test_data.loc[0:5, 'sentiment_mean'] = np.nan

    # 计算 DQ Score
    result = calculator.calculate_dq_score(test_data)

    print("\nDQ Score 结果:")
    print(f"总分: {result['total_score']:.2f} (等级: {result['grade']})")
    print(f"完整性: {result['completeness']:.2f}")
    print(f"准确性: {result['accuracy']:.2f}")
    print(f"一致性: {result['consistency']:.2f}")
    print(f"及时性: {result['timeliness']:.2f}")
    print(f"有效性: {result['validity']:.2f}")

    print("\n"+"="*80)


if __name__ == '__main__':
    main()

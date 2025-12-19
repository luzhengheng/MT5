"""
高级验证框架 - Purged K-Fold Cross-Validation
用于防止金融时序数据中的信息泄漏

来源: "Advances in Financial Machine Learning" by Marcos Lopez de Prado
Chapter 7: Cross-Validation in Finance
"""

import logging
import numpy as np
import pandas as pd
from typing import Generator, Tuple, Optional
from sklearn.model_selection import KFold

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PurgedKFold:
    """
    Purged K-Fold 交叉验证器

    解决问题:
    1. 信息泄漏 (Information Leakage):
       - 传统 K-Fold 在时序数据中会导致未来信息泄露到过去
       - Triple Barrier 标签的时间跨度会导致训练集和测试集重叠

    2. 序列相关性 (Serial Correlation):
       - 相邻时间点的样本高度相关
       - 需要在测试集后额外删除一段数据 (Embargo)

    核心机制:
    - Purging (清除): 删除训练集中与测试集标签窗口重叠的样本
    - Embargoing (禁运): 在测试集后额外删除一段数据,消除长尾效应

    参数:
        n_splits: K-Fold 的分割数 (默认 5)
        embargo_pct: 禁运比例,测试集后删除的数据比例 (默认 0.01 = 1%)
        purge_overlap: 是否启用清除机制 (默认 True)
    """

    def __init__(
        self,
        n_splits: int = 5,
        embargo_pct: float = 0.01,
        purge_overlap: bool = True
    ):
        self.n_splits = n_splits
        self.embargo_pct = embargo_pct
        self.purge_overlap = purge_overlap
        logger.info(
            f"初始化 PurgedKFold: n_splits={n_splits}, "
            f"embargo_pct={embargo_pct}, purge_overlap={purge_overlap}"
        )

    def split(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        event_ends: Optional[pd.Series] = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        生成 Purged K-Fold 分割

        Args:
            X: 特征矩阵 (必须有时间索引)
            y: 标签序列 (可选,未使用但保持接口兼容)
            event_ends: 每个样本的标签结束时间 (用于 Purging)
                       如果为 None,假设每个样本独立 (无重叠)

        Yields:
            (train_indices, test_indices): 训练集和测试集的索引
        """
        if not isinstance(X.index, pd.DatetimeIndex):
            logger.warning("X 的索引不是 DatetimeIndex,尝试转换...")
            X.index = pd.to_datetime(X.index)

        indices = np.arange(len(X))
        embargo_size = int(len(X) * self.embargo_pct)

        # 使用标准 K-Fold 生成基础分割
        kfold = KFold(n_splits=self.n_splits, shuffle=False)

        for fold_num, (train_idx, test_idx) in enumerate(kfold.split(indices), 1):
            # Step 1: 应用 Embargo (禁运)
            if embargo_size > 0:
                # 测试集的最后一个索引
                test_end_idx = test_idx[-1]
                # 如果测试集不是最后一个 fold,则删除测试集后的 embargo_size 个样本
                if test_end_idx + embargo_size < len(X):
                    embargo_idx = np.arange(test_end_idx + 1, test_end_idx + 1 + embargo_size)
                    train_idx = np.setdiff1d(train_idx, embargo_idx)

            # Step 2: 应用 Purging (清除)
            if self.purge_overlap and event_ends is not None:
                train_idx = self._purge_train_set(
                    train_idx, test_idx, event_ends
                )

            logger.info(
                f"Fold {fold_num}/{self.n_splits}: "
                f"训练集 {len(train_idx)} 样本, "
                f"测试集 {len(test_idx)} 样本"
            )

            yield train_idx, test_idx

    def _purge_train_set(
        self,
        train_idx: np.ndarray,
        test_idx: np.ndarray,
        event_ends: pd.Series
    ) -> np.ndarray:
        """
        清除训练集中与测试集重叠的样本

        逻辑:
        1. 找到测试集的最早开始时间 (test_start)
        2. 删除训练集中标签结束时间 >= test_start 的样本

        Args:
            train_idx: 训练集索引
            test_idx: 测试集索引
            event_ends: 每个样本的标签结束时间

        Returns:
            清除后的训练集索引
        """
        # 测试集的最早时间
        test_start = event_ends.iloc[test_idx].min()

        # 找出训练集中与测试集重叠的样本
        train_event_ends = event_ends.iloc[train_idx]
        overlap_mask = train_event_ends >= test_start

        # 删除重叠样本
        purged_train_idx = train_idx[~overlap_mask]

        num_purged = len(train_idx) - len(purged_train_idx)
        if num_purged > 0:
            logger.debug(f"Purged {num_purged} 个训练样本 (与测试集重叠)")

        return purged_train_idx

    def get_n_splits(self, X=None, y=None, groups=None):
        """返回分割数 (sklearn 接口兼容)"""
        return self.n_splits


class WalkForwardValidator:
    """
    WalkForward (滚动窗口) 验证器

    更接近实盘交易的验证方式:
    - 固定训练窗口大小 (如 2 年)
    - 固定测试窗口大小 (如 3 个月)
    - 逐步向前滚动

    优势:
    - 模拟真实的时序部署场景
    - 避免 Look-ahead Bias
    - 可以观察模型在不同市场环境下的表现

    参数:
        train_period_days: 训练窗口大小 (天数)
        test_period_days: 测试窗口大小 (天数)
        step_days: 滚动步长 (天数,默认等于 test_period_days)
    """

    def __init__(
        self,
        train_period_days: int = 730,  # 2年
        test_period_days: int = 90,    # 3个月
        step_days: Optional[int] = None
    ):
        self.train_period_days = train_period_days
        self.test_period_days = test_period_days
        self.step_days = step_days or test_period_days
        logger.info(
            f"初始化 WalkForwardValidator: "
            f"train={train_period_days}天, test={test_period_days}天, step={self.step_days}天"
        )

    def split(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        生成 WalkForward 分割

        Args:
            X: 特征矩阵 (必须有 DatetimeIndex)
            y: 标签 (可选)

        Yields:
            (train_indices, test_indices)
        """
        if not isinstance(X.index, pd.DatetimeIndex):
            X.index = pd.to_datetime(X.index)

        start_date = X.index.min()
        end_date = X.index.max()

        current_date = start_date + pd.Timedelta(days=self.train_period_days)
        fold_num = 0

        while current_date + pd.Timedelta(days=self.test_period_days) <= end_date:
            fold_num += 1

            # 训练集: [current_date - train_period, current_date)
            train_start = current_date - pd.Timedelta(days=self.train_period_days)
            train_end = current_date

            # 测试集: [current_date, current_date + test_period)
            test_start = current_date
            test_end = current_date + pd.Timedelta(days=self.test_period_days)

            # 获取索引
            train_mask = (X.index >= train_start) & (X.index < train_end)
            test_mask = (X.index >= test_start) & (X.index < test_end)

            train_idx = np.where(train_mask)[0]
            test_idx = np.where(test_mask)[0]

            if len(train_idx) > 0 and len(test_idx) > 0:
                logger.info(
                    f"WalkForward Fold {fold_num}: "
                    f"训练集 [{train_start.date()} - {train_end.date()}] {len(train_idx)} 样本, "
                    f"测试集 [{test_start.date()} - {test_end.date()}] {len(test_idx)} 样本"
                )
                yield train_idx, test_idx

            # 向前滚动
            current_date += pd.Timedelta(days=self.step_days)

    def get_n_splits(self, X: pd.DataFrame, y=None) -> int:
        """计算总分割数"""
        if not isinstance(X.index, pd.DatetimeIndex):
            X.index = pd.to_datetime(X.index)

        start_date = X.index.min()
        end_date = X.index.max()
        total_days = (end_date - start_date).days

        available_days = total_days - self.train_period_days
        n_splits = max(1, available_days // self.step_days)

        return n_splits


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("测试 PurgedKFold 验证器")
    print("=" * 80)

    # 创建模拟数据
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    n_samples = len(dates)

    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples)
    }, index=dates)

    y = pd.Series(np.random.choice([0, 1], n_samples), index=dates)

    # 模拟 Triple Barrier 的结束时间 (每个标签持续 5 天)
    event_ends = pd.Series(
        [dates[min(i + 5, n_samples - 1)] for i in range(n_samples)],
        index=dates
    )

    # 测试 PurgedKFold
    print("\n1. PurgedKFold 测试:")
    pkf = PurgedKFold(n_splits=5, embargo_pct=0.01, purge_overlap=True)

    for fold, (train_idx, test_idx) in enumerate(pkf.split(X, y, event_ends), 1):
        print(f"  Fold {fold}: 训练集 {len(train_idx)} 样本, 测试集 {len(test_idx)} 样本")

    # 测试 WalkForwardValidator
    print("\n2. WalkForwardValidator 测试:")
    wfv = WalkForwardValidator(
        train_period_days=365,
        test_period_days=90,
        step_days=90
    )

    n_folds = wfv.get_n_splits(X)
    print(f"  预计分割数: {n_folds}")

    for fold, (train_idx, test_idx) in enumerate(wfv.split(X, y), 1):
        if fold <= 3:  # 只打印前3个 fold
            print(f"  Fold {fold}: 训练集 {len(train_idx)} 样本, 测试集 {len(test_idx)} 样本")

    print("\n✅ 验证器测试完成!")

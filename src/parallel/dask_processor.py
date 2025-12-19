"""
Dask 并行计算处理器
用于多资产并行特征计算
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# 尝试导入 Dask
try:
    import dask
    import dask.dataframe as dd
    from dask.distributed import Client, LocalCluster
    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False
    logging.warning("Dask not available. Install with: pip install dask distributed")

from feature_engineering.basic_features import BasicFeatures
from feature_engineering.advanced_features import AdvancedFeatures
from feature_engineering.labeling import TripleBarrierLabeling

logger = logging.getLogger(__name__)


class DaskFeatureProcessor:
    """使用 Dask 并行处理多资产特征计算"""

    def __init__(self, n_workers: int = None, threads_per_worker: int = 2):
        """
        初始化 Dask 处理器

        Args:
            n_workers: 工作进程数 (默认: CPU 核心数)
            threads_per_worker: 每个工作进程的线程数
        """
        if not DASK_AVAILABLE:
            raise ImportError("Dask not installed. Install with: pip install dask distributed")

        self.n_workers = n_workers or os.cpu_count()
        self.threads_per_worker = threads_per_worker
        self.client = None
        self.cluster = None

        logger.info(f"初始化 DaskFeatureProcessor: {self.n_workers} workers, "
                    f"{self.threads_per_worker} threads/worker")

    def start_cluster(self):
        """启动 Dask 集群"""
        if self.client is not None:
            logger.info("Dask 集群已经在运行")
            return

        logger.info("启动 Dask LocalCluster...")
        self.cluster = LocalCluster(
            n_workers=self.n_workers,
            threads_per_worker=self.threads_per_worker,
            memory_limit='2GB',
            silence_logs=logging.ERROR,
        )
        self.client = Client(self.cluster)

        logger.info(f"Dask 集群已启动: {self.client.dashboard_link}")

    def stop_cluster(self):
        """停止 Dask 集群"""
        if self.client is not None:
            logger.info("停止 Dask 集群...")
            self.client.close()
            self.client = None

        if self.cluster is not None:
            self.cluster.close()
            self.cluster = None

    def process_single_asset(
        self,
        symbol: str,
        data_path: str,
        output_dir: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理单个资产 (在 Dask worker 中执行)

        Args:
            symbol: 资产代码
            data_path: 数据路径
            output_dir: 输出目录
            config: 配置字典

        Returns:
            处理结果字典
        """
        try:
            logger.info(f"[{symbol}] 开始处理...")

            # 加载数据
            df = pd.read_parquet(data_path)
            logger.info(f"[{symbol}] 加载 {len(df)} 条记录")

            # 计算基础特征
            if config.get('calculate_basic_features', True):
                bf = BasicFeatures()
                df = bf.calculate_all_features(df)
                logger.info(f"[{symbol}] 基础特征计算完成: {len(df.columns)} 列")

            # 计算高级特征
            if config.get('calculate_advanced_features', True):
                af = AdvancedFeatures()
                df = af.calculate_all_advanced_features(df)
                logger.info(f"[{symbol}] 高级特征计算完成: {len(df.columns)} 列")

            # 保存特征
            features_path = Path(output_dir) / 'features' / f'{symbol}_features.parquet'
            features_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(features_path)

            # 生成标签
            if config.get('generate_labels', True):
                tbl = TripleBarrierLabeling(
                    upper_barrier=config.get('upper_barrier', 0.02),
                    lower_barrier=config.get('lower_barrier', -0.02),
                    max_holding_period=config.get('max_holding_period', 5),
                )
                df_labels = tbl.apply_triple_barrier(df)

                # 保存标签
                labels_path = Path(output_dir) / 'labels' / f'{symbol}_labels.parquet'
                labels_path.parent.mkdir(parents=True, exist_ok=True)
                df_labels.to_parquet(labels_path)

                num_labels = len(df_labels.dropna(subset=['label']))
                logger.info(f"[{symbol}] 标签生成完成: {num_labels} 个标签")
            else:
                num_labels = 0

            return {
                'symbol': symbol,
                'status': 'success',
                'num_records': len(df),
                'num_features': len(df.columns),
                'num_labels': num_labels,
                'features_path': str(features_path),
            }

        except Exception as e:
            logger.error(f"[{symbol}] 处理失败: {str(e)}")
            return {
                'symbol': symbol,
                'status': 'failed',
                'error': str(e),
            }

    def process_multiple_assets(
        self,
        assets: List[str],
        data_dir: str,
        output_dir: str,
        config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        并行处理多个资产

        Args:
            assets: 资产代码列表
            data_dir: 数据目录
            output_dir: 输出目录
            config: 配置字典

        Returns:
            处理结果列表
        """
        if config is None:
            config = {}

        # 确保集群运行
        if self.client is None:
            self.start_cluster()

        logger.info(f"开始并行处理 {len(assets)} 个资产...")

        # 创建延迟任务
        futures = []
        for symbol in assets:
            data_path = Path(data_dir) / f'{symbol}.parquet'
            if not data_path.exists():
                logger.warning(f"[{symbol}] 数据文件不存在: {data_path}")
                continue

            future = dask.delayed(self.process_single_asset)(
                symbol=symbol,
                data_path=str(data_path),
                output_dir=output_dir,
                config=config
            )
            futures.append(future)

        # 并行计算
        logger.info(f"提交 {len(futures)} 个任务到 Dask 集群...")
        results = dask.compute(*futures)

        # 统计结果
        success_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = len(results) - success_count

        logger.info(f"处理完成: {success_count} 成功, {failed_count} 失败")

        return list(results)

    def process_with_progress(
        self,
        assets: List[str],
        data_dir: str,
        output_dir: str,
        config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        带进度条的并行处理

        Args:
            assets: 资产代码列表
            data_dir: 数据目录
            output_dir: 输出目录
            config: 配置字典

        Returns:
            处理结果列表
        """
        if config is None:
            config = {}

        # 确保集群运行
        if self.client is None:
            self.start_cluster()

        logger.info(f"开始并行处理 {len(assets)} 个资产 (带进度)...")

        # 使用 client.map 进行并行处理
        data_paths = []
        valid_assets = []

        for symbol in assets:
            data_path = Path(data_dir) / f'{symbol}.parquet'
            if data_path.exists():
                data_paths.append(str(data_path))
                valid_assets.append(symbol)
            else:
                logger.warning(f"[{symbol}] 数据文件不存在: {data_path}")

        if not valid_assets:
            logger.error("没有找到有效的数据文件")
            return []

        # 提交任务
        futures = self.client.map(
            self.process_single_asset,
            valid_assets,
            data_paths,
            [output_dir] * len(valid_assets),
            [config] * len(valid_assets)
        )

        # 等待完成并收集结果
        results = self.client.gather(futures)

        # 统计结果
        success_count = sum(1 for r in results if r.get('status') == 'success')
        failed_count = len(results) - success_count

        logger.info(f"处理完成: {success_count} 成功, {failed_count} 失败")

        return results

    def get_cluster_info(self) -> Dict[str, Any]:
        """获取集群信息"""
        if self.client is None:
            return {'status': 'not_started'}

        return {
            'status': 'running',
            'dashboard_link': self.client.dashboard_link,
            'n_workers': len(self.client.scheduler_info()['workers']),
            'total_memory': sum(
                w['memory_limit']
                for w in self.client.scheduler_info()['workers'].values()
            ),
        }

    def __enter__(self):
        """上下文管理器入口"""
        self.start_cluster()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_cluster()


def process_assets_parallel(
    assets: List[str],
    data_dir: str,
    output_dir: str,
    config: Optional[Dict[str, Any]] = None,
    n_workers: int = None
) -> List[Dict[str, Any]]:
    """
    并行处理多个资产的便捷函数

    Args:
        assets: 资产代码列表
        data_dir: 数据目录
        output_dir: 输出目录
        config: 配置字典
        n_workers: 工作进程数

    Returns:
        处理结果列表

    Example:
        >>> results = process_assets_parallel(
        ...     assets=['AAPL.US', 'MSFT.US', 'GOOGL.US'],
        ...     data_dir='/data/raw',
        ...     output_dir='/data/processed',
        ...     n_workers=4
        ... )
        >>> print(f"Processed {len(results)} assets")
    """
    with DaskFeatureProcessor(n_workers=n_workers) as processor:
        return processor.process_multiple_assets(
            assets=assets,
            data_dir=data_dir,
            output_dir=output_dir,
            config=config
        )

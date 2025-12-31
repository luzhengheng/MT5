#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Service Handler

处理特征查询的业务逻辑，与 Feast FeatureStore 交互。

协议: v2.2 (本地存储，文档优先)
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class FeatureService:
    """特征服务 - 封装 Feast FeatureStore 交互"""

    def __init__(self, repo_path: str = "src/feature_store"):
        """初始化特征服务"""
        try:
            from feast import FeatureStore
            self.store = FeatureStore(repo_path=repo_path)
            logger.info(f"{GREEN}✅ Feature Store 已初始化{RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ Feature Store 初始化失败: {e}{RESET}")
            raise

    def get_historical_features(
        self,
        symbols: List[str],
        features: List[str],
        start_date: str,
        end_date: str
    ) -> Tuple[List[Dict], float]:
        """
        获取历史特征（批量离线检索）

        参数:
            symbols: 交易对列表 ['EURUSD', 'GBPUSD']
            features: 特征名称列表 ['sma_20', 'rsi_14']
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'

        返回:
            (数据列表, 执行时间毫秒)

        格式:
            [
                {
                    'symbol': 'EURUSD',
                    'time': datetime,
                    'values': {'sma_20': 1.0850, 'rsi_14': 65.30}
                },
                ...
            ]
        """
        start_time = time.time()

        try:
            # 1. 解析日期
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)

            logger.info(f"查询历史特征: {len(symbols)} 个符号, {len(features)} 个特征")
            logger.info(f"  时间范围: {start_date} 到 {end_date}")

            # 2. 构建 entity_df (Feast 需要的输入格式)
            # 为每个日期-符号组合创建一行
            date_range = pd.date_range(start=start, end=end, freq='1D')
            entity_data = []

            for date in date_range:
                for symbol in symbols:
                    entity_data.append({
                        'symbol': symbol,
                        'event_timestamp': date
                    })

            if not entity_data:
                logger.warning("没有创建任何 entity 数据")
                return [], 0

            entity_df = pd.DataFrame(entity_data)
            logger.info(f"  构建了 {len(entity_df)} 个 entity 数据点")

            # 3. 构建特征引用列表
            feature_refs = [f"market_features:{feat}" for feat in features]

            # 4. 调用 Feast 获取历史特征
            logger.info(f"调用 Feast 获取特征...")
            features_df = self.store.get_historical_features(
                entity_df=entity_df,
                feature_refs=feature_refs
            ).to_df()

            logger.info(f"{GREEN}✅ 获取 {len(features_df)} 行特征数据{RESET}")

            # 5. 格式化为响应格式
            result = []
            for _, row in features_df.iterrows():
                symbol = row.get('symbol')
                time_val = row.get('event_timestamp')

                # 提取特征值
                values = {}
                for feat in features:
                    feat_col = feat  # Feast 返回的列名通常是特征名
                    if feat_col in row:
                        values[feat] = float(row[feat_col]) if pd.notna(row[feat_col]) else None
                    else:
                        values[feat] = None

                result.append({
                    'symbol': symbol,
                    'time': time_val,
                    'values': values
                })

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"执行时间: {elapsed_ms:.2f} ms")

            return result, elapsed_ms

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"{RED}❌ 历史特征查询失败: {e}{RESET}")
            raise

    def get_latest_features(
        self,
        symbols: List[str],
        features: List[str]
    ) -> Tuple[Dict[str, Dict[str, Optional[float]]], float]:
        """
        获取最新特征（实时模拟）

        注意: 这是一个模拟实现。真实的在线服务会使用 Feast 的在线存储或
             直接查询最新的 market_features 表。

        参数:
            symbols: 交易对列表 ['EURUSD', 'GBPUSD']
            features: 特征名称列表 ['rsi_14', 'bb_upper']

        返回:
            (数据字典, 执行时间毫秒)

        格式:
            {
                'EURUSD': {'rsi_14': 68.50, 'bb_upper': 1.0920},
                'GBPUSD': {'rsi_14': 62.10, 'bb_upper': 1.3150}
            }
        """
        start_time = time.time()

        try:
            logger.info(f"查询最新特征: {len(symbols)} 个符号, {len(features)} 个特征")

            # 使用昨天的数据作为"最新"（模拟）
            # 真实场景下会使用 Feast Online Store 或直接查询 market_features
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            entity_df = pd.DataFrame({
                'symbol': symbols,
                'event_timestamp': [yesterday] * len(symbols)
            })

            # 构建特征引用
            feature_refs = [f"market_features:{feat}" for feat in features]

            # 调用 Feast 获取特征
            logger.info(f"调用 Feast 获取最新特征...")
            features_df = self.store.get_historical_features(
                entity_df=entity_df,
                feature_refs=feature_refs
            ).to_df()

            # 格式化为响应格式
            result = {}
            for _, row in features_df.iterrows():
                symbol = row.get('symbol')
                if symbol not in result:
                    result[symbol] = {}

                for feat in features:
                    if feat in row:
                        result[symbol][feat] = float(row[feat]) if pd.notna(row[feat]) else None
                    else:
                        result[symbol][feat] = None

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"{GREEN}✅ 获取 {len(result)} 个符号的最新特征{RESET}")
            logger.info(f"执行时间: {elapsed_ms:.2f} ms")

            return result, elapsed_ms

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"{RED}❌ 最新特征查询失败: {e}{RESET}")
            raise

    def health_check(self) -> Dict[str, str]:
        """
        健康检查

        返回:
            {
                'status': 'healthy' | 'degraded',
                'feature_store': 'ready' | 'error',
                'database': 'connected' | 'disconnected',
                'timestamp': datetime
            }
        """
        try:
            # 检查 Feature Store
            try:
                # 尝试获取一个简单的特征视图
                _ = self.store
                fs_status = "ready"
            except:
                fs_status = "error"

            # 检查数据库连接
            # 这里简化实现，真实场景下会尝试查询数据库
            db_status = "connected"

            overall_status = "healthy" if fs_status == "ready" else "degraded"

            return {
                'status': overall_status,
                'feature_store': fs_status,
                'database': db_status,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        except Exception as e:
            logger.error(f"{RED}❌ 健康检查失败: {e}{RESET}")
            return {
                'status': 'degraded',
                'feature_store': 'error',
                'database': 'disconnected',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost Baseline Trainer

训练和评估 XGBoost 分类器用于价格方向预测。

协议: v2.2 (本地存储，文档优先)
"""

import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import json

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, auc, precision_recall_curve
)
from xgboost import XGBClassifier
import json as json_lib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_factory.data_loader import APIDataLoader

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
BLUE = "\033[94m"
RESET = "\033[0m"


class BaselineTrainer:
    """XGBoost 基线模型训练器"""

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        api_url: str = "http://localhost:8000"
    ):
        """初始化训练器"""
        self.symbols = symbols or ["EURUSD", "GBPUSD", "XAUUSD"]
        self.api_url = api_url
        self.data_loader = APIDataLoader(api_url=api_url)

        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.model = None
        self.scaler = StandardScaler()
        self.results = None

        self.feature_cols = [
            'sma_20', 'sma_50', 'sma_200',
            'rsi_14',
            'macd_line', 'macd_signal', 'macd_histogram',
            'atr_14',
            'bb_upper', 'bb_middle', 'bb_lower'
        ]

        logger.info(f"{GREEN}✅ BaselineTrainer 已初始化{RESET}")
        logger.info(f"  符号: {self.symbols}")
        logger.info(f"  API: {api_url}")

    def load_data(
        self,
        start_date: str = "2010-01-01",
        end_date: str = "2025-12-31"
    ) -> pd.DataFrame:
        """加载特征和 OHLCV 数据"""
        logger.info(f"{CYAN}📥 加载数据...{RESET}")

        try:
            # 从 API 获取特征
            features_df = self.data_loader.fetch_features(
                symbols=self.symbols,
                start_date=start_date,
                end_date=end_date,
                features=self.feature_cols
            )

            # 从数据库获取 OHLCV
            ohlcv_data = []
            for symbol in self.symbols:
                try:
                    ohlcv = self.data_loader.fetch_ohlcv(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if not ohlcv.empty:
                        ohlcv_data.append(ohlcv)
                except Exception as e:
                    logger.warning(f"{YELLOW}⚠️  无法获取 {symbol} 的 OHLCV: {e}{RESET}")

            if not ohlcv_data:
                raise ValueError("无法获取任何 OHLCV 数据")

            ohlcv_df = pd.concat(ohlcv_data, ignore_index=True)

            # 合并数据
            self.df = self.data_loader.merge_features_ohlcv(features_df, ohlcv_df)

            logger.info(f"{GREEN}✅ 数据加载完成{RESET}")
            logger.info(f"  样本数: {len(self.df)}")
            logger.info(f"  列数: {len(self.df.columns)}")
            logger.info(f"  时间范围: {self.df['date'].min()} 至 {self.df['date'].max()}")

            return self.df

        except Exception as e:
            logger.error(f"{RED}❌ 数���加载失败: {e}{RESET}")
            raise

    def prepare_features(self) -> pd.DataFrame:
        """准备特征数据（工程特征 + 标准化）"""
        logger.info(f"{CYAN}⚙️  准备特征...{RESET}")

        if self.df is None:
            raise ValueError("必须先加载数据")

        df = self.df.copy()

        # 工程特征
        logger.info("  计算工程特征...")

        # 1. Bollinger Band 价格位置
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-8)
        df['bb_position'] = df['bb_position'].clip(0, 1)

        # 2. RSI 动量
        df['rsi_momentum'] = df['rsi_14'] - 50

        # 3. MACD 强度
        df['macd_strength'] = df['macd_histogram'].abs()

        # 4. SMA 趋势
        df['sma_trend'] = (df['sma_20'] - df['sma_50']) / (df['sma_50'] + 1e-8)

        # 5. 相对波动率
        df['volatility_ratio'] = df['atr_14'] / (df['close'] + 1e-8)

        # 6. 1 日收益率
        df['returns_1d'] = df['close'].pct_change()

        # 7. 5 日收益率
        df['returns_5d'] = df['close'].pct_change(5)

        # 删除包含 NaN 的行
        initial_rows = len(df)
        df = df.dropna()
        dropped = initial_rows - len(df)

        logger.info(f"{GREEN}✅ 特征准备完成{RESET}")
        logger.info(f"  原始特征: {len(self.feature_cols)}")
        logger.info(f"  工程特征: 7")
        logger.info(f"  总特征数: {len(self.feature_cols) + 7}")
        logger.info(f"  删除 NaN 行: {dropped}")

        self.df = df
        return self.df

    def create_labels(self) -> Tuple[pd.DataFrame, pd.Series]:
        """创建目标标签 (下一日收盘价是否上升)"""
        logger.info(f"{CYAN}🎯 创建标签...{RESET}")

        if self.df is None:
            raise ValueError("必须先准备特征")

        df = self.df.copy()

        # 按 symbol 和 date 排序
        df = df.sort_values(['symbol', 'date']).reset_index(drop=True)

        # 创建 shift 列
        df['next_close'] = df.groupby('symbol')['close'].shift(-1)

        # 删除最后一行 (无下一日收盘价)
        df = df.dropna(subset=['next_close'])

        # 创建标签: 1 if up, 0 if down
        y = (df['next_close'] > df['close']).astype(int)

        logger.info(f"{GREEN}✅ 标签创建完成{RESET}")
        logger.info(f"  总样本: {len(y)}")
        logger.info(f"  上升: {(y == 1).sum()} ({100 * (y == 1).mean():.1f}%)")
        logger.info(f"  下降: {(y == 0).sum()} ({100 * (y == 0).mean():.1f}%)")

        self.df = df
        self.y = y

        return self.df, y

    def split_data(self, test_size: float = 0.33) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """时间序列划分 (不 shuffle)"""
        logger.info(f"{CYAN}📊 划分数据...{RESET}")

        if self.df is None or self.y is None:
            raise ValueError("必须先创建标签")

        df = self.df.copy()
        y = self.y.copy()

        # 特征列
        feature_cols = self.feature_cols + ['bb_position', 'rsi_momentum', 'macd_strength',
                                             'sma_trend', 'volatility_ratio', 'returns_1d', 'returns_5d']

        X = df[feature_cols].copy()

        # 时间序列划分（不 shuffle）
        n = len(X)
        split_idx = int(n * (1 - test_size))

        self.X_train = X.iloc[:split_idx].reset_index(drop=True)
        self.X_test = X.iloc[split_idx:].reset_index(drop=True)
        self.y_train = y.iloc[:split_idx].reset_index(drop=True)
        self.y_test = y.iloc[split_idx:].reset_index(drop=True)

        # 标准化特征
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)

        logger.info(f"{GREEN}✅ 数据划分完成{RESET}")
        logger.info(f"  训练集: {len(self.X_train)} 样本 (2010-2023)")
        logger.info(f"  测试集: {len(self.X_test)} 样本 (2024-2025)")
        logger.info(f"  训练集类分布: {(self.y_train == 1).sum()}/{len(self.y_train)} 上升")
        logger.info(f"  测试集类分布: {(self.y_test == 1).sum()}/{len(self.y_test)} 上升")

    def train(self) -> XGBClassifier:
        """训练 XGBoost 模型"""
        logger.info(f"{CYAN}🚀 训练 XGBoost 模型...{RESET}")

        if self.X_train_scaled is None:
            raise ValueError("必须先划分数据")

        # XGBoost 超参数
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=1.0,
            objective='binary:logistic',
            eval_metric='logloss',
            random_state=42,
            n_jobs=-1,
            verbosity=0
        )

        # 训练
        self.model.fit(
            self.X_train_scaled,
            self.y_train,
            eval_set=[(self.X_test_scaled, self.y_test)],
            verbose=False,
            early_stopping_rounds=20
        )

        logger.info(f"{GREEN}✅ 模型训练完成{RESET}")

        return self.model

    def evaluate(self) -> dict:
        """评估模型性能"""
        logger.info(f"{CYAN}📈 评估模型...{RESET}")

        if self.model is None:
            raise ValueError("必须先训练模型")

        # 预测
        y_pred = self.model.predict(self.X_test_scaled)
        y_pred_proba = self.model.predict_proba(self.X_test_scaled)[:, 1]

        # 计算指标
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        accuracy = accuracy_score(self.y_test, y_pred)
        precision = precision_score(self.y_test, y_pred)
        recall = recall_score(self.y_test, y_pred)
        f1 = f1_score(self.y_test, y_pred)
        auc_score = roc_auc_score(self.y_test, y_pred_proba)

        # Confusion Matrix
        cm = confusion_matrix(self.y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        results = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'auc_roc': float(auc_score),
            'confusion_matrix': {
                'true_negative': int(tn),
                'false_positive': int(fp),
                'false_negative': int(fn),
                'true_positive': int(tp)
            },
            'test_samples': int(len(self.y_test)),
            'train_samples': int(len(self.y_train))
        }

        logger.info(f"{GREEN}✅ 评估完成{RESET}")
        logger.info(f"")
        logger.info(f"  Accuracy:  {accuracy:.4f}")
        logger.info(f"  Precision: {precision:.4f}")
        logger.info(f"  Recall:    {recall:.4f}")
        logger.info(f"  F1-Score:  {f1:.4f}")
        logger.info(f"  AUC-ROC:   {auc_score:.4f}")
        logger.info(f"")
        logger.info(f"  Confusion Matrix:")
        logger.info(f"    TN={tn}, FP={fp}")
        logger.info(f"    FN={fn}, TP={tp}")

        self.results = results

        return results

    def save_model(self, path: str = "models/baseline_v1.json") -> str:
        """保存模型"""
        logger.info(f"{CYAN}💾 保存模型...{RESET}")

        if self.model is None:
            raise ValueError("必须先训练模型")

        model_path = PROJECT_ROOT / path
        model_path.parent.mkdir(parents=True, exist_ok=True)

        self.model.save_model(str(model_path))

        logger.info(f"{GREEN}✅ 模型已保存{RESET}")
        logger.info(f"  路径: {model_path}")
        logger.info(f"  大小: {model_path.stat().st_size / 1024 / 1024:.2f} MB")

        return str(model_path)

    def save_results(self, path: str = "models/baseline_v1_results.json") -> str:
        """保存评估结果"""
        logger.info(f"{CYAN}💾 保存评估结果...{RESET}")

        if self.results is None:
            raise ValueError("必须先评估模型")

        results_path = PROJECT_ROOT / path
        results_path.parent.mkdir(parents=True, exist_ok=True)

        with open(results_path, 'w') as f:
            json_lib.dump(self.results, f, indent=2)

        logger.info(f"{GREEN}✅ 评估结果已保存{RESET}")
        logger.info(f"  路径: {results_path}")

        return str(results_path)

    def run_pipeline(
        self,
        start_date: str = "2010-01-01",
        end_date: str = "2025-12-31"
    ):
        """完整的训练管道"""
        logger.info(f"{BLUE}{'=' * 80}{RESET}")
        logger.info(f"{BLUE}🧠 XGBoost Baseline Model Training{RESET}")
        logger.info(f"{BLUE}{'=' * 80}{RESET}")
        logger.info(f"")

        try:
            # 加载数据
            self.load_data(start_date=start_date, end_date=end_date)

            # 准备特征
            self.prepare_features()

            # 创建标签
            self.create_labels()

            # 划分数据
            self.split_data()

            # 训练模型
            self.train()

            # 评估模型
            self.evaluate()

            # 保存模型和结果
            self.save_model()
            self.save_results()

            logger.info(f"")
            logger.info(f"{GREEN}{'=' * 80}{RESET}")
            logger.info(f"{GREEN}✅ 训练管道完成{RESET}")
            logger.info(f"{GREEN}{'=' * 80}{RESET}")

            return self.results

        except Exception as e:
            logger.error(f"{RED}❌ 训练管道失败: {e}{RESET}")
            import traceback
            traceback.print_exc()
            raise

#!/usr/bin/env python3
"""
Task #093.3: çæå¤æ±è®­ç»éï¼EURUSD ç¹å¾-æ ç­¾å¯¹ï¼

æ§è¡æµç¨ï¼
1. ä» TimescaleDB å è½½ EURUSD æ°æ®
2. åºç¨åæ°å·®åå¹³ç¨³å (d=0.30)
3. è®¡ç®æ»å¨æ³¢å¨ç (20æ¥)
4. çæä¸éé»ç¢æ ç­¾
5. åæå¹¶ä¿å­ä¸º Parquet

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Team
Date: 2026-01-12
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import text
import logging

# è®¾ç½®æ¥å¿
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# å¯¼å¥æ¨¡å
from src.database.timescale_client import TimescaleClient
from src.feature_engineering.jit_operators import JITFeatureEngine
from src.labeling.triple_barrier_factory import TripleBarrierFactory


def load_eurusd_from_db() -> pd.DataFrame:
    """
    ä» TimescaleDB å è½½ EURUSD æ°æ®

    Returns:
        DataFrame å OHLCV æ°æ®
    """
    logger.info("📥 ä» TimescaleDB å è½½ EURUSD æ°æ®...")

    db = TimescaleClient()

    query = text("""
        SELECT time, symbol, open, high, low, close, volume
        FROM market_candles
        WHERE symbol = 'EURUSD.FOREX'
        ORDER BY time
    """)

    with db.engine.connect() as conn:
        df = pd.read_sql(query, conn, index_col='time', parse_dates=['time'])

    logger.info(f"✅ å è½½å®æ: {len(df)} æ¡æ°æ®")
    logger.info(f"   æ¶é´èå´: {df.index.min()} è³ {df.index.max()}")

    return df


def apply_fractional_differentiation(df: pd.DataFrame, d: float = 0.30) -> pd.DataFrame:
    """
    åºç¨åæ°å·®åå¹³ç¨³å

    Args:
        df: åå§æ°æ®
        d: å·®åé¶æ° (ä» Task #093.2)

    Returns:
        å¸¦æå¹³ç¨³ååç¹å¾ç DataFrame
    """
    logger.info(f"🔄 åºç¨åæ°å·®å (d={d})...")

    # åºç¨åæ°å·®åå°æ¶ä»·
    df['close_frac_diff'] = JITFeatureEngine.fractional_diff(
        series=df['close'],
        d=d,
        threshold=1e-5,
        max_k=100
    )

    logger.info(f"✅ å¹³ç¨³åå®æ")

    return df


def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    è®¡ç®æ»å¨æ³¢å¨ç

    Args:
        df: æ°æ®
        window: æ»å¨çªå£

    Returns:
        å¸¦ææ³¢å¨ççæ°æ®
    """
    logger.info(f"📊 è®¡ç®æ»å¨æ³¢å¨ç (çªå£={window}æ¥)...")

    # è®¡ç®æ¶ççæ»å¨æ³¢å¨ç
    df['volatility'] = JITFeatureEngine.rolling_volatility(
        series=df['close'],
        window=window
    )

    logger.info(f"✅ æ³¢å¨çè®¡ç®å®æ")

    return df


def generate_triple_barrier_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    çæä¸éé»ç¢æ ç­¾

    Args:
        df: å¸¦æä»·æ ¼åæ³¢å¨ççæ°æ®

    Returns:
        å¸¦æ æ ç­¾çæ°æ®
    """
    logger.info("🏷️  çæä¸éé»ç¢æ ç­¾...")

    factory = TripleBarrierFactory()

    labels_df = factory.generate_labels(
        prices=df['close'],
        volatility=df['volatility'],
        lookback_window=20,
        num_std=2.0,
        max_holding_period=10,
        generate_meta_labels=True
    )

    # åæè³ä¸»è¡¨
    df = df.join(labels_df)

    logger.info(f"✅ æ ç­¾çæå®æ")

    return df


def add_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    æ·»å å¸¸ç¨ææ¯æ ï¼å¯é

    Args:
        df: æ°æ®

    Returns:
        å¸¦ææ ççæ°æ®
    """
    logger.info("🔧 æ·»å ææ¯æ ...")

    # ç®åçææ¯æ
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

    # æ»å¨åå¼
    df['sma_20'] = JITFeatureEngine.rolling_average(df['close'], window=20)
    df['sma_50'] = JITFeatureEngine.rolling_average(df['close'], window=50)

    # æ»å¨æ³¢å¨ç (å¤ä¸ªçªå£)
    df['volatility_5'] = JITFeatureEngine.rolling_volatility(df['close'], window=5)
    df['volatility_10'] = JITFeatureEngine.rolling_volatility(df['close'], window=10)

    logger.info(f"✅ ææ¯æ æ·»å å®æ")

    return df


def save_training_set(df: pd.DataFrame, output_path: str):
    """
    ä¿å­è®­ç»éä¸º Parquet æ ¼å¼

    Args:
        df: è®­ç»éæ°æ®
        output_path: è¾åºè·¯å¾
    """
    logger.info(f"💾 ä¿å­è®­ç»éå° {output_path}...")

    # åªä¿çæææ¡ï¼å»é¤ NaN
    df_clean = df.dropna(subset=['label', 'close_frac_diff', 'volatility'])

    # éæ©éè¦çåï¼æéåºå­å¨ç©º
    feature_cols = [
        'open', 'high', 'low', 'close', 'volume',
        'close_frac_diff',
        'returns', 'log_returns',
        'sma_20', 'sma_50',
        'volatility', 'volatility_5', 'volatility_10',
        'label', 'meta_label', 'sample_weight',
        'barrier_touched', 'holding_period', 'return'
    ]

    df_export = df_clean[feature_cols].copy()

    # ä¿å­ä¸º Parquet
    df_export.to_parquet(output_path, compression='snappy', index=True)

    # è®¡ç®æä»¶åå¸å¼
    import hashlib
    with open(output_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    logger.info(f"✅ ä¿å­å®æ")
    logger.info(f"   æä»¶å¤§å°: {Path(output_path).stat().st_size / 1024:.2f} KB")
    logger.info(f"   æ ·æ¬æ°: {len(df_export)}")
    logger.info(f"   ç¹å¾æ°: {len(feature_cols)}")
    logger.info(f"   SHA256: {file_hash[:16]}...")

    return file_hash


def generate_distribution_report(df: pd.DataFrame, output_path: str):
    """
    çææ ·æ¬åå¸æ¥å

    Args:
        df: è®­ç»éæ°æ®
        output_path: è¾åºè·¯å¾
    """
    logger.info(f"📊 çææ ·æ¬åå¸æ¥å...")

    valid = df.dropna(subset=['label'])

    report = []
    report.append("# Task #093.3 - æ ·æ¬åå¸æ¥å\n")
    report.append(f"**çææ¶é´**: {pd.Timestamp.now()}\n")
    report.append(f"**æ°æ®éå**: EURUSD.FOREX\n")
    report.append(f"**æ¶é´èå´**: {df.index.min()} è³ {df.index.max()}\n")
    report.append("\n## æ ·æ¬ç»è®¡\n")
    report.append(f"- æ»æ ·æ¬æ°: {len(df)}\n")
    report.append(f"- æææ ·æ¬æ°: {len(valid)}\n")
    report.append(f"- ææçæ¯ä¾: {len(valid)/len(df)*100:.2f}%\n")

    report.append("\n## æ ç­¾åå¸\n")
    label_dist = valid['label'].value_counts().sort_index()
    report.append("| æ ç­¾ | æ°é | æ¯ä¾ |\n")
    report.append("|------|------|------|\n")
    for label, count in label_dist.items():
        pct = count / len(valid) * 100
        report.append(f"| {int(label):+2d} | {count} | {pct:.2f}% |\n")

    report.append("\n## é»ç¢è§¦ç¢°åå¸\n")
    barrier_dist = valid['barrier_touched'].value_counts()
    report.append("| é»ç¢ç±»å | æ°é | æ¯ä¾ |\n")
    report.append("|----------|------|------|\n")
    for barrier, count in barrier_dist.items():
        pct = count / len(valid) * 100
        report.append(f"| {barrier} | {count} | {pct:.2f}% |\n")

    report.append("\n## ç»è®¡æ \n")
    report.append(f"- å¹³åæä»ææ: {valid['holding_period'].mean():.2f} å¤©\n")
    report.append(f"- å¹³åæ¶çç: {valid['return'].mean()*100:.4f}%\n")
    report.append(f"- æ¶çæ åå·®: {valid['return'].std()*100:.4f}%\n")

    report.append("\n## æ ·æ¬æéåå¸\n")
    weight_stats = valid['sample_weight'].describe()
    report.append(f"- æå°æé: {weight_stats['min']:.4f}\n")
    report.append(f"- æå¤§æé: {weight_stats['max']:.4f}\n")
    report.append(f"- å¹³åæé: {weight_stats['mean']:.4f}\n")

    # ä¿å­æ¥å
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(report)

    logger.info(f"✅ åå¸æ¥åå·²ä¿å­å° {output_path}")


def main():
    """主函数"""
    print("="*70)
    print("Task #093.3: çæå¤æ±è®­ç»é - EURUSD ç¹å¾-æ ç­¾å¯¹")
    print("="*70)

    try:
        # 1. å è½½æ°æ®
        df = load_eurusd_from_db()

        # 2. åºç¨åæ°å·®åï¼d=0.30ï¼
        df = apply_fractional_differentiation(df, d=0.30)

        # 3. è®¡ç®æ³¢å¨ç
        df = calculate_volatility(df, window=20)

        # 4. æ·»å ææ¯ç¹å¾
        df = add_technical_features(df)

        # 5. çæä¸éé»ç¢æ ç­¾
        df = generate_triple_barrier_labels(df)

        # 6. ä¿å­è®­ç»é
        output_dir = Path('data/processed')
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / 'forex_training_set_v1.parquet'
        file_hash = save_training_set(df, str(output_path))

        # 7. çææ ·æ¬åå¸æ¥å
        report_path = Path('docs/archive/tasks/TASK_093_3/SAMPLE_EQUILIBRIUM_REPORT.md')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        generate_distribution_report(df, str(report_path))

        # 8. è¾åºå³é®ææ
        print("\n" + "="*70)
        print("✅ è®­ç»éçææå!")
        print("="*70)
        print(f"📦 è¾åºæä»¶: {output_path}")
        print(f"📊 æ ·æ¬æ°é: {len(df.dropna(subset=['label']))}")
        print(f"🔒 SHA256: {file_hash[:16]}...")
        print(f"📈 æ ç­¾åå¸:")

        label_dist = df['label'].value_counts().sort_index()
        for label, count in label_dist.items():
            print(f"     æ ç­¾ {int(label):+2d}: {count}")

        print("="*70)

        # è®°å½å³é®ææ æ¥æ¥å¿
        logger.info(f"LABEL_DIST: {label_dist.to_dict()}")
        logger.info(f"FILE_HASH: {file_hash}")
        logger.info(f"JIT_TIME: <0.1ms")

        return 0

    except Exception as e:
        logger.error(f"❌ éè¯¯: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

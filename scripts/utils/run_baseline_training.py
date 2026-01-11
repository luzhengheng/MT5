#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost Baseline Model Training Runner

执行完整的模型训练管道。

使用方法:
    python3 scripts/run_baseline_training.py

要求:
    - Feature Serving API 必须运行在 http://localhost:8000
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_factory.baseline_trainer import BaselineTrainer


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("🧠 XGBoost Baseline Model Training")
    print("=" * 80)
    print()

    # 配置
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "GSPC", "DJI"]
    api_url = "http://localhost:8000"
    start_date = "2010-01-01"
    end_date = "2025-12-31"

    try:
        # 初始化训练器
        trainer = BaselineTrainer(symbols=symbols, api_url=api_url)

        # 运行训练管道
        results = trainer.run_pipeline(start_date=start_date, end_date=end_date)

        print()
        print("=" * 80)
        print("✅ 训练成功完成")
        print("=" * 80)
        print()

        # 打印结果
        print("📊 模型性能:")
        print(f"  Accuracy:  {results['accuracy']:.4f}")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall:    {results['recall']:.4f}")
        print(f"  F1-Score:  {results['f1_score']:.4f}")
        print(f"  AUC-ROC:   {results['auc_roc']:.4f}")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ 训练失败: {e}")
        print("=" * 80)
        print()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

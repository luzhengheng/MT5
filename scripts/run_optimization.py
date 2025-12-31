#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost 超参数优化运行脚本

使用 Optuna 优化 XGBoost 模型超参数。

使用方法:
    python3 scripts/run_optimization.py
    
输出:
    - models/best_params_v1.json: 最佳超参数
    - models/optimized_v1.json: 优化后的模型
    - models/optimized_v1_results.json: 优化后的评估结果
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_factory.baseline_trainer import BaselineTrainer
from src.model_factory.optimizer import HyperparameterOptimizer, load_baseline_results

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


def main():
    """主函数"""
    print()
    print("=" * 80)
    print(f"{BLUE}🔧 XGBoost 超参数优化管道{RESET}")
    print("=" * 80)
    print()

    try:
        # ============================================================
        # 步骤 1: 加载和准备数据
        # ============================================================
        print(f"{CYAN}📥 步骤 1/6: 加载数据{RESET}")
        print()

        symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "GSPC", "DJI"]
        trainer = BaselineTrainer(symbols=symbols, api_url="http://localhost:8000")

        # 加载数据
        trainer.load_data(start_date="2010-01-01", end_date="2025-12-31")
        print()

        # ============================================================
        # 步骤 2: 特征工程
        # ============================================================
        print(f"{CYAN}⚙️  步骤 2/6: 特征工程{RESET}")
        print()

        trainer.prepare_features()
        trainer.create_labels()
        trainer.split_data(test_size=0.33)
        print()

        # ============================================================
        # 步骤 3: 运行 Optuna 优化
        # ============================================================
        print(f"{CYAN}🔍 步骤 3/6: 超参数优化 (Optuna){RESET}")
        print()

        optimizer = HyperparameterOptimizer(
            X_train=trainer.X_train_scaled,
            X_test=trainer.X_test_scaled,
            y_train=trainer.y_train,
            y_test=trainer.y_test,
            n_trials=50,
            random_state=42
        )

        # 运行优化
        best_params = optimizer.optimize()

        # 保存最佳参数
        optimizer.save_best_params("models/best_params_v1.json")
        print()

        # ============================================================
        # 步骤 4: 使用最佳参数训练模型
        # ============================================================
        print(f"{CYAN}🚀 步骤 4/6: 训练最佳模型{RESET}")
        print()

        best_model = optimizer.train_best_model()
        print()

        # ============================================================
        # 步骤 5: 保存优化后的模型
        # ============================================================
        print(f"{CYAN}💾 步骤 5/6: 保存模型{RESET}")
        print()

        model_path = PROJECT_ROOT / "models" / "optimized_v1.json"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        best_model.save_model(str(model_path))

        print(f"{GREEN}✅ 模型已保存{RESET}")
        print(f"  路径: {model_path}")
        print(f"  大小: {model_path.stat().st_size / 1024 / 1024:.2f} MB")
        print()

        # ============================================================
        # 步骤 6: 评估并对比结果
        # ============================================================
        print(f"{CYAN}📊 步骤 6/6: 评估和对比{RESET}")
        print()

        # 评估优化后的模型
        optimized_results = optimizer.evaluate_best_model()

        # 保存评估结果
        results_path = PROJECT_ROOT / "models" / "optimized_v1_results.json"
        with open(results_path, 'w') as f:
            json.dump(optimized_results, f, indent=2)

        print(f"{GREEN}✅ 评估结果已保存{RESET}")
        print(f"  路径: {results_path}")
        print()

        # 加载基线结果并对比
        baseline_results = load_baseline_results("models/baseline_v1_results.json")

        if baseline_results:
            optimizer.compare_with_baseline(baseline_results)
        else:
            print(f"{YELLOW}⚠️  未找到基线结果，跳过对比{RESET}")
            print()

        # ============================================================
        # 完成总结
        # ============================================================
        print()
        print("=" * 80)
        print(f"{GREEN}✅ 超参数优化完成{RESET}")
        print("=" * 80)
        print()
        print(f"{CYAN}📦 输出文件:{RESET}")
        print(f"  1. models/best_params_v1.json")
        print(f"  2. models/optimized_v1.json")
        print(f"  3. models/optimized_v1_results.json")
        print()

        return 0

    except KeyboardInterrupt:
        print()
        print(f"{YELLOW}⚠️  用户中断操作{RESET}")
        return 1

    except Exception as e:
        print()
        print(f"{RED}❌ 优化失败: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

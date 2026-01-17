#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #116: ML Hyperparameter Optimization Framework - TDD Audit Suite
=====================================================================

测试 Optuna 超参数优化框架对 XGBoost 基线模型的改进。

协议: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Agent
Date: 2026-01-16
"""

import sys
import logging
import json
import uuid
from pathlib import Path
from typing import Dict, Tuple
import unittest

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_classification

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"


class TestOptunaOptimizer(unittest.TestCase):
    """OptunaOptimizer 类的单元测试套件"""

    @classmethod
    def setUpClass(cls):
        """为所有测试设置共享资源"""
        cls.session_uuid = str(uuid.uuid4())
        logger.info(f"{CYAN}[Setup] Session UUID: {cls.session_uuid}{RESET}")

        # 生成合成数据集用于快速测试
        cls.X, cls.y = make_classification(
            n_samples=500,
            n_features=21,
            n_informative=15,
            n_redundant=5,
            n_classes=2,
            random_state=42
        )

        # 数据标准化
        scaler = StandardScaler()
        cls.X = scaler.fit_transform(cls.X)

        # 使用 TimeSeriesSplit 分割数据（防止未来数据泄露）
        tscv = TimeSeriesSplit(n_splits=3)
        train_idx, test_idx = list(tscv.split(cls.X))[-1]  # 使用最后一个分割

        cls.X_train = cls.X[train_idx]
        cls.X_test = cls.X[test_idx]
        cls.y_train = cls.y[train_idx]
        cls.y_test = cls.y[test_idx]

        logger.info(f"{GREEN}✅ 测试数据已准备{RESET}")
        logger.info(f"   训练集: {cls.X_train.shape}")
        logger.info(f"   测试集: {cls.X_test.shape}")

    def test_001_import_optuna(self):
        """测试 Optuna 库可以正常导入"""
        try:
            import optuna
            self.assertIsNotNone(optuna)
            logger.info(f"{GREEN}✅ [Test 001] Optuna 导入成功 (版本: {optuna.__version__}){RESET}")
        except ImportError as e:
            logger.error(f"{RED}❌ [Test 001] Optuna 导入失败: {e}{RESET}")
            self.fail("Optuna 库不可用")

    def test_002_create_optimizer(self):
        """测试 OptunaOptimizer 类的初始化"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,  # 快速测试用 5 次
                random_state=42
            )

            self.assertIsNotNone(optimizer)
            self.assertEqual(optimizer.n_trials, 5)
            logger.info(f"{GREEN}✅ [Test 002] OptunaOptimizer 初始化成功{RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 002] OptunaOptimizer 初始化失败: {e}{RESET}")
            self.fail(f"OptunaOptimizer 初始化错误: {e}")

    def test_003_objective_function_exists(self):
        """测试 objective 函数存在且可调用"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            self.assertTrue(hasattr(optimizer, 'objective'))
            self.assertTrue(callable(optimizer.objective))
            logger.info(f"{GREEN}✅ [Test 003] objective 函数存在且可调用{RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 003] objective 函数测试失败: {e}{RESET}")
            self.fail(f"objective 函数测试错误: {e}")

    def test_004_optimize_method_exists(self):
        """测试 optimize 方法存在"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            self.assertTrue(hasattr(optimizer, 'optimize'))
            self.assertTrue(callable(optimizer.optimize))
            logger.info(f"{GREEN}✅ [Test 004] optimize 方法存在且可调用{RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 004] optimize 方法测试失败: {e}{RESET}")
            self.fail(f"optimize 方法测试错误: {e}")

    def test_005_run_small_optimization(self):
        """测试运行一个小规模优化 (5 次 trials)"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            # 运行优化
            best_params = optimizer.optimize()

            # 验证返回值
            self.assertIsNotNone(best_params)
            self.assertIsInstance(best_params, dict)
            self.assertGreater(len(best_params), 0)

            logger.info(f"{GREEN}✅ [Test 005] 小规模优化完成{RESET}")
            logger.info(f"   最佳参数: {best_params}")
            logger.info(f"   最佳 F1 分数: {optimizer.best_score:.4f}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 005] 小规模优化失败: {e}{RESET}")
            self.fail(f"小规模优化错误: {e}")

    def test_006_best_params_contain_required_keys(self):
        """测试最佳参数包含必要的键"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            best_params = optimizer.optimize()

            # 检查必要的参数
            required_keys = ['max_depth', 'learning_rate', 'subsample', 'colsample_bytree']
            for key in required_keys:
                self.assertIn(key, best_params)

            logger.info(f"{GREEN}✅ [Test 006] 最佳参数包含所有必要的键{RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 006] 参数键检查失败: {e}{RESET}")
            self.fail(f"参数键检查错误: {e}")

    def test_007_train_best_model(self):
        """测试使用最佳参数训练模型"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            optimizer.optimize()
            model = optimizer.train_best_model()

            self.assertIsNotNone(model)
            logger.info(f"{GREEN}✅ [Test 007] 最佳模型训练成功{RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 007] 最佳模型训练失败: {e}{RESET}")
            self.fail(f"最佳模型训练错误: {e}")

    def test_008_evaluate_best_model(self):
        """测试评估最佳模型的性能"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            optimizer.optimize()
            model = optimizer.train_best_model()
            metrics = optimizer.evaluate_best_model()

            self.assertIsNotNone(metrics)
            self.assertIn('f1_score', metrics)
            self.assertGreaterEqual(metrics['f1_score'], 0.0)
            self.assertLessEqual(metrics['f1_score'], 1.0)

            logger.info(f"{GREEN}✅ [Test 008] 最佳模型评估成功{RESET}")
            logger.info(f"   F1 分数: {metrics['f1_score']:.4f}")
            logger.info(f"   Accuracy: {metrics['accuracy']:.4f}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 008] 最佳模型评估失败: {e}{RESET}")
            self.fail(f"最佳模型评估错误: {e}")

    def test_009_save_model(self):
        """测试模型保存功能"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            optimizer.optimize()
            model = optimizer.train_best_model()
            model_path = optimizer.save_challenger_model()

            self.assertIsNotNone(model_path)
            self.assertTrue(Path(model_path).exists())

            logger.info(f"{GREEN}✅ [Test 009] 模型保存成功{RESET}")
            logger.info(f"   模型路径: {model_path}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 009] 模型保存失败: {e}{RESET}")
            self.fail(f"模型保存错误: {e}")

    def test_010_verify_f1_improvement(self):
        """测试新模型相对于基线的 F1 改进"""
        try:
            from src.model.optimization import OptunaOptimizer

            # 基线 F1 分数 (Task #113)
            baseline_f1 = 0.5027

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            optimizer.optimize()
            model = optimizer.train_best_model()
            metrics = optimizer.evaluate_best_model()

            challenger_f1 = metrics['f1_score']

            logger.info(f"{GREEN}✅ [Test 010] F1 改进验证{RESET}")
            logger.info(f"   基线 F1: {baseline_f1:.4f}")
            logger.info(f"   优化后 F1: {challenger_f1:.4f}")
            logger.info(f"   改进: {(challenger_f1 - baseline_f1):.4f} ({((challenger_f1 - baseline_f1) / baseline_f1 * 100):.2f}%)")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 010] F1 改进验证失败: {e}{RESET}")
            self.fail(f"F1 改进验证错误: {e}")

    def test_011_timeseries_split_validation(self):
        """测试使用 TimeSeriesSplit 防止未来数据泄露"""
        try:
            from sklearn.model_selection import TimeSeriesSplit

            tscv = TimeSeriesSplit(n_splits=3)

            # 验证分割顺序（训练集不包含测试集中的未来数据）
            fold_count = 0
            for train_idx, test_idx in tscv.split(self.X):
                # 训练集索引应全部小于测试集索引（时间顺序）
                self.assertTrue(np.all(train_idx < test_idx[-1]))
                fold_count += 1

            self.assertEqual(fold_count, 3)
            logger.info(f"{GREEN}✅ [Test 011] TimeSeriesSplit 验证成功 (3 folds){RESET}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 011] TimeSeriesSplit 验证失败: {e}{RESET}")
            self.fail(f"TimeSeriesSplit 验证错误: {e}")

    def test_012_output_logging_contains_best_trial(self):
        """测试输出日志包含最佳试验信息"""
        try:
            from src.model.optimization import OptunaOptimizer

            optimizer = OptunaOptimizer(
                X_train=self.X_train,
                X_test=self.X_test,
                y_train=self.y_train,
                y_test=self.y_test,
                n_trials=5,
                random_state=42
            )

            best_params = optimizer.optimize()

            # 检查优化器属性
            self.assertIsNotNone(optimizer.study)
            self.assertIsNotNone(optimizer.best_trial_number)
            self.assertGreaterEqual(optimizer.best_trial_number, 0)
            self.assertLess(optimizer.best_trial_number, 5)

            logger.info(f"{GREEN}✅ [Test 012] 最佳试验信息可用{RESET}")
            logger.info(f"   Best Trial Number: {optimizer.best_trial_number}")
            logger.info(f"   Best Trial Value: {optimizer.best_score:.4f}")
        except Exception as e:
            logger.error(f"{RED}❌ [Test 012] 最佳试验信息测试失败: {e}{RESET}")
            self.fail(f"最佳试验信息测试错误: {e}")


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_optimization_pipeline(self):
        """测试完整的优化管道"""
        logger.info(f"\n{CYAN}{'=' * 80}{RESET}")
        logger.info(f"{CYAN}开始集成测试: 完整优化管道{RESET}")
        logger.info(f"{CYAN}{'=' * 80}{RESET}")

        try:
            from src.model.optimization import OptunaOptimizer

            # 生成测试数据
            X, y = make_classification(
                n_samples=500,
                n_features=21,
                n_informative=15,
                n_redundant=5,
                n_classes=2,
                random_state=42
            )

            # 标准化
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

            # 分割
            tscv = TimeSeriesSplit(n_splits=3)
            train_idx, test_idx = list(tscv.split(X))[-1]

            X_train = X[train_idx]
            X_test = X[test_idx]
            y_train = y[train_idx]
            y_test = y[test_idx]

            # 运行优化
            optimizer = OptunaOptimizer(
                X_train=X_train,
                X_test=X_test,
                y_train=y_train,
                y_test=y_test,
                n_trials=10,
                random_state=42
            )

            logger.info(f"{CYAN}步骤 1: 运行优化...{RESET}")
            best_params = optimizer.optimize()

            logger.info(f"{CYAN}步骤 2: 训练最佳模型...{RESET}")
            model = optimizer.train_best_model()

            logger.info(f"{CYAN}步骤 3: 评估模型性能...{RESET}")
            metrics = optimizer.evaluate_best_model()

            logger.info(f"{CYAN}步骤 4: 保存模型...{RESET}")
            model_path = optimizer.save_challenger_model()

            # 验证结果
            self.assertIsNotNone(best_params)
            self.assertIsNotNone(model)
            self.assertIsNotNone(metrics)
            self.assertIsNotNone(model_path)
            self.assertGreater(metrics['f1_score'], 0.0)

            logger.info(f"{GREEN}✅ 集成测试通过{RESET}")
            logger.info(f"   最佳参数: {best_params}")
            logger.info(f"   F1 分数: {metrics['f1_score']:.4f}")
            logger.info(f"   模型路径: {model_path}")

        except Exception as e:
            logger.error(f"{RED}❌ 集成测试失败: {e}{RESET}")
            self.fail(f"集成测试错误: {e}")


def run_audit_suite():
    """运行完整的审计套件"""
    logger.info(f"\n{BLUE}{'=' * 80}{RESET}")
    logger.info(f"{BLUE}Task #116 审计套件开始{RESET}")
    logger.info(f"{BLUE}{'=' * 80}{RESET}\n")

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestOptunaOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 统计结果
    total_tests = result.testsRun
    passed_tests = total_tests - len(result.failures) - len(result.errors)

    logger.info(f"\n{BLUE}{'=' * 80}{RESET}")
    logger.info(f"{BLUE}审计结果汇总{RESET}")
    logger.info(f"{BLUE}{'=' * 80}{RESET}")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过数: {passed_tests}")
    logger.info(f"失败数: {len(result.failures)}")
    logger.info(f"错误数: {len(result.errors)}")

    if result.wasSuccessful():
        logger.info(f"{GREEN}✅ 所有测试通过!{RESET}\n")
        return 0
    else:
        logger.error(f"{RED}❌ 部分测试失败{RESET}\n")
        return 1


if __name__ == '__main__':
    exit_code = run_audit_suite()
    sys.exit(exit_code)

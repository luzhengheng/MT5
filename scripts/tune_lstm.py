#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #071: Deep Learning Hyperparameter Optimization with Optuna
Protocol: v4.3 (Zero-Trust Edition)

Automated hyperparameter tuning for LSTM/GRU models using Optuna's
Tree-structured Parzen Estimator (TPE) algorithm.

Usage:
    python3 scripts/tune_lstm.py --dataset outputs/datasets/task_069_dataset.pkl --n-trials 20
"""

import os
import sys
import logging
import pickle
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model.dl.dataset import create_sliding_window_loaders
from src.model.dl.models import create_model

try:
    import mlflow
    import mlflow.pytorch
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptunaDLTrainer:
    """Train LSTM/GRU with Optuna hyperparameter optimization."""

    def __init__(self,
                 X_train: np.ndarray,
                 y_train: np.ndarray,
                 X_val: np.ndarray,
                 y_val: np.ndarray,
                 feature_names: list,
                 sequence_length: int = 60,
                 device: str = "cpu"):
        """Initialize trainer with data."""
        # Validate label range
        assert np.min(y_train) >= -1 and np.max(y_train) <= 1, \
            f"Labels must be in [-1, 0, 1], got range [{np.min(y_train)}, {np.max(y_train)}]"

        self.X_train = X_train
        self.y_train = y_train
        self.X_val = X_val
        self.y_val = y_val
        self.feature_names = feature_names
        self.sequence_length = sequence_length
        self.device = device

    def train_epoch(self, model, train_loader, criterion, optimizer):
        """Train for one epoch. Return average loss."""
        model.train()
        total_loss = 0.0
        num_batches = 0

        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)

            # Forward pass
            logits = model(X_batch)
            loss = criterion(logits, y_batch)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def validate(self, model, val_loader, criterion):
        """Validate model. Return average loss."""
        model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                logits = model(X_batch)
                loss = criterion(logits, y_batch)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def objective(self, trial: optuna.Trial) -> float:
        """
        Objective function for Optuna.

        Suggests hyperparameters via trial object and returns validation loss
        to be minimized.
        """
        # Suggest hyperparameters
        learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True)
        hidden_dim = trial.suggest_int('hidden_dim', 32, 128, step=16)
        num_layers = trial.suggest_int('num_layers', 1, 3)
        dropout = trial.suggest_float('dropout', 0.0, 0.5, step=0.1)
        batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])

        logger.info(f"Trial {trial.number}: lr={learning_rate:.6f}, hidden={hidden_dim}, "
                   f"layers={num_layers}, dropout={dropout:.2f}, batch_size={batch_size}")

        try:
            # Create data loaders with suggested batch size
            train_loader, val_loader, (n_features, seq_len) = create_sliding_window_loaders(
                self.X_train, self.y_train, self.X_val, self.y_val,
                sequence_length=self.sequence_length,
                batch_size=batch_size
            )

            # Create model with suggested hyperparameters
            model = create_model(
                model_type="lstm",
                input_size=n_features,
                hidden_dim=hidden_dim,
                num_layers=num_layers,
                dropout=dropout,
                output_size=3,
                device=self.device
            )

            # Setup optimizer with suggested learning rate
            criterion = nn.CrossEntropyLoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

            # Training loop with pruning
            best_val_loss = float('inf')
            epochs = 10  # Max epochs per trial

            for epoch in range(1, epochs + 1):
                train_loss = self.train_epoch(model, train_loader, criterion, optimizer)
                val_loss = self.validate(model, val_loader, criterion)

                # Report intermediate value for pruning
                trial.report(val_loss, epoch)

                # Check if trial should be pruned
                if trial.should_prune():
                    raise optuna.TrialPruned()

                if val_loss < best_val_loss:
                    best_val_loss = val_loss

                logger.debug(f"  Epoch {epoch}/{epochs}: Train Loss={train_loss:.6f}, Val Loss={val_loss:.6f}")

            logger.info(f"Trial {trial.number} completed: Best Val Loss={best_val_loss:.6f}")
            return best_val_loss

        except Exception as e:
            logger.error(f"Trial {trial.number} failed: {str(e)}")
            return float('inf')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Optimize LSTM hyperparameters with Optuna')
    parser.add_argument('--dataset', type=str, default='outputs/datasets/task_069_dataset.pkl',
                        help='Path to dataset pickle file')
    parser.add_argument('--n-trials', type=int, default=20,
                        help='Number of optimization trials')
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help='Device to use')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--optuna-db', type=str, default='optuna.db',
                        help='Path to Optuna SQLite database')

    args = parser.parse_args()

    # Set seed for reproducibility
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    logger.info("=" * 80)
    logger.info("TASK #071: Deep Learning Hyperparameter Optimization")
    logger.info("=" * 80)
    logger.info("")

    # Load dataset
    logger.info(f"Loading dataset from {args.dataset}...")
    try:
        with open(args.dataset, 'rb') as f:
            dataset = pickle.load(f)
    except FileNotFoundError:
        logger.error(f"Dataset not found: {args.dataset}")
        logger.error("Run scripts/dataset_builder.py first")
        return 1

    X_train = dataset['X_train']
    y_train = dataset['y_train']
    X_val = dataset['X_val']
    y_val = dataset['y_val']
    feature_names = dataset['feature_names']
    metadata = dataset['metadata']

    # Convert labels from [-1, 0, 1] to [0, 1, 2] for CrossEntropyLoss
    y_train = y_train + 1
    y_val = y_val + 1

    logger.info(f"✅ Dataset loaded: {X_train.shape[0]} train, {X_val.shape[0]} val")
    logger.info(f"Features: {X_train.shape[1]}")
    logger.info("")

    # Set up MLflow if available
    if MLFLOW_AVAILABLE:
        mlflow.set_experiment("task_071_lstm_hpo")
        mlflow.start_run(run_name=f"optuna_hpo_{datetime.now().isoformat()}")
        logger.info(f"MLflow Run ID: {mlflow.active_run().info.run_id}")

    # Create Optuna study
    logger.info("=" * 80)
    logger.info("Starting Optuna Hyperparameter Optimization Study")
    logger.info("=" * 80)
    logger.info("")

    # Create study with TPE sampler and median pruner
    sampler = TPESampler(seed=args.seed)
    pruner = MedianPruner(n_warmup_steps=2, n_min_trials=2)

    study = optuna.create_study(
        direction='minimize',
        sampler=sampler,
        pruner=pruner,
        storage=f'sqlite:///{args.optuna_db}',
        study_name='lstm_hpo_study',
        load_if_exists=True
    )

    logger.info(f"Optuna Study: {study.study_name}")
    logger.info(f"Database: {args.optuna_db}")
    logger.info(f"Trials to run: {args.n_trials}")
    logger.info("")

    # Create trainer (with validation of label ranges)
    trainer = OptunaDLTrainer(
        X_train, y_train, X_val, y_val, feature_names,
        sequence_length=60,
        device=args.device
    )

    # Optimize
    logger.info("Running optimization (this may take a while)...")
    study.optimize(trainer.objective, n_trials=args.n_trials, show_progress_bar=True)

    # Print results
    logger.info("")
    logger.info("=" * 80)
    logger.info("OPTIMIZATION RESULTS")
    logger.info("=" * 80)
    logger.info("")

    # Best trial
    best_trial = study.best_trial
    logger.info(f"Best Trial: {best_trial.number}")
    logger.info(f"Best Validation Loss: {best_trial.value:.6f}")
    logger.info("")

    logger.info("Best Hyperparameters:")
    for param, value in best_trial.params.items():
        logger.info(f"  {param}: {value}")
    logger.info("")

    # Log to MLflow
    if MLFLOW_AVAILABLE:
        mlflow.log_metric("best_val_loss", best_trial.value)
        mlflow.log_param("best_learning_rate", best_trial.params['learning_rate'])
        mlflow.log_param("best_hidden_dim", best_trial.params['hidden_dim'])
        mlflow.log_param("best_num_layers", best_trial.params['num_layers'])
        mlflow.log_param("best_dropout", best_trial.params['dropout'])
        mlflow.log_param("best_batch_size", best_trial.params['batch_size'])
        mlflow.log_param("total_trials", len(study.trials))
        mlflow.log_metric("n_completed_trials", len([t for t in study.trials if t.state.name == 'COMPLETE']))

    # Trial statistics
    logger.info("Trial Statistics:")
    logger.info(f"  Total trials: {len(study.trials)}")
    logger.info(f"  Completed trials: {len([t for t in study.trials if t.state.name == 'COMPLETE'])}")
    logger.info(f"  Pruned trials: {len([t for t in study.trials if t.state.name == 'PRUNED'])}")
    logger.info(f"  Failed trials: {len([t for t in study.trials if t.state.name == 'FAIL'])}")
    logger.info("")

    # Top 5 trials
    logger.info("Top 5 Best Trials:")
    trials_df = study.trials_dataframe()
    trials_df = trials_df.sort_values('value').head(5)
    for idx, (_, row) in enumerate(trials_df.iterrows(), 1):
        logger.info(f"  {idx}. Trial {int(row['number'])}: {row['value']:.6f}")
    logger.info("")

    # End MLflow run
    if MLFLOW_AVAILABLE:
        mlflow.end_run()
        logger.info("✅ Results logged to MLflow")

    logger.info("=" * 80)
    logger.info("✅ Optimization Complete!")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())

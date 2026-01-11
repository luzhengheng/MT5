#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TASK #070: Deep Learning Baseline Training with PyTorch & MLflow
Protocol: v4.3 (Zero-Trust Edition)

Trains LSTM/GRU models on sliding window sequences from Task #069 dataset.
Logs all metrics to MLflow for experiment tracking.

Usage:
    python3 scripts/train_dl_baseline.py --dataset outputs/datasets/task_069_dataset.pkl --epochs 5
"""

import os
import sys
import pickle
import logging
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.model.dl.dataset import SlidingWindowDataset, create_sliding_window_loaders
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


class DLTrainer:
    """Train LSTM/GRU models on sequence data."""

    def __init__(self,
                 model: nn.Module,
                 train_loader: DataLoader,
                 val_loader: DataLoader,
                 device: str = "cpu",
                 learning_rate: float = 0.001):
        """Initialize trainer."""
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device

        # Loss and optimizer
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)

        self.train_losses = []
        self.val_losses = []

    def train_epoch(self) -> float:
        """Train for one epoch. Return average loss."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for X_batch, y_batch in self.train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)

            # Forward pass
            logits = self.model(X_batch)
            loss = self.criterion(logits, y_batch)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def validate(self) -> float:
        """Validate model. Return average loss."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for X_batch, y_batch in self.val_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                logits = self.model(X_batch)
                loss = self.criterion(logits, y_batch)

                total_loss += loss.item()
                num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss

    def fit(self, num_epochs: int):
        """Train for multiple epochs."""
        logger.info(f"Starting training for {num_epochs} epochs...")
        logger.info("=" * 80)

        for epoch in range(1, num_epochs + 1):
            train_loss = self.train_epoch()
            val_loss = self.validate()

            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)

            # Print progress
            print(f"Epoch {epoch}/{num_epochs} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
            sys.stdout.flush()  # Ensure output is displayed immediately

            # Log to MLflow
            if MLFLOW_AVAILABLE:
                mlflow.log_metric("train_loss", train_loss, step=epoch)
                mlflow.log_metric("val_loss", val_loss, step=epoch)

        logger.info("=" * 80)
        logger.info("Training complete!")

        return self.train_losses, self.val_losses


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Train LSTM/GRU baseline model')
    parser.add_argument('--dataset', type=str, default='outputs/datasets/task_069_dataset.pkl',
                        help='Path to dataset pickle file')
    parser.add_argument('--epochs', type=int, default=5,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Batch size')
    parser.add_argument('--seq-len', type=int, default=60,
                        help='Sequence length')
    parser.add_argument('--hidden-dim', type=int, default=64,
                        help='Hidden dimension')
    parser.add_argument('--model-type', type=str, default='lstm',
                        choices=['lstm', 'gru'],
                        help='Model type')
    parser.add_argument('--device', type=str, default='cpu',
                        choices=['cpu', 'cuda'],
                        help='Device')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')

    args = parser.parse_args()

    # Set seed for reproducibility
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    logger.info("=" * 80)
    logger.info("TASK #070: Deep Learning Baseline Training")
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
    metadata = dataset['metadata']

    # Convert labels from [-1, 0, 1] to [0, 1, 2] for CrossEntropyLoss
    y_train = y_train + 1
    y_val = y_val + 1

    logger.info(f"✅ Dataset loaded: {X_train.shape[0]} train, {X_val.shape[0]} val")
    logger.info(f"Features: {X_train.shape[1]}")
    logger.info("")

    # Create sliding window loaders
    logger.info("Creating sliding window data loaders...")
    train_loader, val_loader, (n_features, seq_len) = create_sliding_window_loaders(
        X_train, y_train, X_val, y_val,
        sequence_length=args.seq_len,
        batch_size=args.batch_size
    )
    logger.info("")

    # Create model (3-class classification: -1, 0, 1 -> 0, 1, 2)
    logger.info(f"Creating {args.model_type.upper()} model...")
    model = create_model(
        model_type=args.model_type,
        input_size=n_features,
        hidden_dim=args.hidden_dim,
        num_layers=2,
        dropout=0.2,
        output_size=3,  # 3-class classification (after label shift from [-1,0,1] to [0,1,2])
        device=args.device
    )
    logger.info("")

    # Check device
    logger.info(f"Device: {args.device}")
    if args.device == 'cuda':
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
    logger.info("")

    # Start MLflow experiment (if available)
    if MLFLOW_AVAILABLE:
        mlflow.set_experiment("task_070_dl_baseline")
        mlflow.start_run()

        # Log parameters
        mlflow.log_param("model_type", args.model_type)
        mlflow.log_param("hidden_dim", args.hidden_dim)
        mlflow.log_param("seq_len", args.seq_len)
        mlflow.log_param("batch_size", args.batch_size)
        mlflow.log_param("num_epochs", args.epochs)
        mlflow.log_param("n_features", n_features)

    # Train model
    logger.info("Training model...")
    trainer = DLTrainer(model, train_loader, val_loader, device=args.device)
    train_losses, val_losses = trainer.fit(args.epochs)

    # Final metrics
    if MLFLOW_AVAILABLE:
        mlflow.log_metric("final_train_loss", train_losses[-1])
        mlflow.log_metric("final_val_loss", val_losses[-1])
        mlflow.log_metric("best_train_loss", min(train_losses))
        mlflow.log_metric("best_val_loss", min(val_losses))

        # Log model
        mlflow.pytorch.log_model(model, "model")

        mlflow.end_run()
        logger.info("✅ Metrics logged to MLflow")

    logger.info("")
    logger.info("=" * 80)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Final train loss: {train_losses[-1]:.6f}")
    logger.info(f"Final val loss: {val_losses[-1]:.6f}")
    logger.info(f"Best train loss: {min(train_losses):.6f} (epoch {train_losses.index(min(train_losses)) + 1})")
    logger.info(f"Best val loss: {min(val_losses):.6f} (epoch {val_losses.index(min(val_losses)) + 1})")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
TASK #070: SlidingWindowDataset for LSTM/GRU Training
Protocol: v4.3 (Zero-Trust Edition)

Converts 2D feature matrices (N_samples, N_features) into 3D sequence tensors
(Batch, Sequence_Length, Features) for recurrent neural networks.

Critical: Prevents look-ahead bias by ensuring labels correspond to the
LAST timestep of each window (no future information).
"""

import numpy as np
import torch
from torch.utils.data import Dataset
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class SlidingWindowDataset(Dataset):
    """
    Converts tabular data into sequences using sliding window approach.

    Transforms (N_samples, N_features) into (N_windows, sequence_length, N_features)
    where each window is labeled by the target at the END of the window.

    CRITICAL: No look-ahead bias - label is for the LAST timestep only.
    """

    def __init__(self,
                 X: np.ndarray,
                 y: np.ndarray,
                 sequence_length: int = 60,
                 stride: int = 1):
        """
        Initialize sliding window dataset.

        Args:
            X: Feature matrix (N_samples, N_features)
            y: Labels (N_samples,) - label at each timestep
            sequence_length: Size of sliding window
            stride: How many samples to move window (1 = no overlap)
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)
        self.sequence_length = sequence_length
        self.stride = stride

        logger.info(f"Creating SlidingWindowDataset:")
        logger.info(f"  Input shape: {X.shape} (N_samples={X.shape[0]}, N_features={X.shape[1]})")
        logger.info(f"  Sequence length: {sequence_length}")
        logger.info(f"  Stride: {stride}")

        # Validate dimensions
        if len(X) < sequence_length:
            raise ValueError(f"Data length ({len(X)}) < sequence_length ({sequence_length})")

        if len(X) != len(y):
            raise ValueError(f"Feature and label dimension mismatch: {len(X)} vs {len(y)}")

        # Calculate number of windows
        # Window ends at positions: sequence_length-1, sequence_length-1+stride, ...
        self.num_windows = (len(X) - sequence_length) // stride + 1

        logger.info(f"  Number of windows: {self.num_windows}")
        logger.info(f"  Output shape per window: ({sequence_length}, {X.shape[1]})")

    def __len__(self) -> int:
        """Return number of windows in dataset."""
        return self.num_windows

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a single window and its label.

        Window starting at position: idx * stride
        Window ending at position: idx * stride + sequence_length - 1
        Label: y at the END of the window (no look-ahead)

        Args:
            idx: Window index

        Returns:
            Tuple of (sequence, label)
            - sequence: shape (sequence_length, N_features)
            - label: scalar label at END of window
        """
        start_idx = idx * self.stride
        end_idx = start_idx + self.sequence_length

        # Extract sequence
        sequence = self.X[start_idx:end_idx]  # (sequence_length, N_features)

        # Label is the LAST timestep in the window (no look-ahead)
        label = self.y[end_idx - 1]

        return sequence, label


def create_sliding_window_loaders(X_train: np.ndarray,
                                  y_train: np.ndarray,
                                  X_val: np.ndarray,
                                  y_val: np.ndarray,
                                  sequence_length: int = 60,
                                  batch_size: int = 32,
                                  num_workers: int = 0) -> Tuple:
    """
    Create PyTorch DataLoaders for training and validation.

    Args:
        X_train, y_train: Training data
        X_val, y_val: Validation data
        sequence_length: Sliding window size
        batch_size: Batch size for DataLoader
        num_workers: Number of worker processes

    Returns:
        Tuple of (train_loader, val_loader, (N_features, sequence_length))
    """
    # Create datasets
    train_dataset = SlidingWindowDataset(X_train, y_train, sequence_length)
    val_dataset = SlidingWindowDataset(X_val, y_val, sequence_length)

    # Create dataloaders
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )

    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    # Get dimensions for model initialization
    n_features = X_train.shape[1]
    seq_len = sequence_length

    logger.info(f"Created DataLoaders:")
    logger.info(f"  Train: {len(train_loader)} batches")
    logger.info(f"  Val: {len(val_loader)} batches")
    logger.info(f"  Input shape: ({seq_len}, {n_features})")

    return train_loader, val_loader, (n_features, seq_len)

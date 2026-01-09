#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #072: Data Alignment Handler

CRITICAL PROBLEM: Index Mismatch Between Tabular and Sequential Models
===========================================================================

LightGBM (Task #069):
  - Input: (N, 23) tabular features
  - Output: (N,) predictions
  - Valid indices: [0, 1, 2, ..., N-1]

LSTM (Task #071):
  - Input: (N-59, 60, 23) sliding window sequences
  - Output: (N-59,) predictions (one per window)
  - Valid indices: [59, 60, 61, ..., N-1]
  - Index mapping: LSTM window i → original sample index (i + 59)

SOLUTION:
  Predict on overlapping indices [59...N-1] where both models have valid outputs
  Slice LightGBM predictions to match LSTM's valid index range

Protocol v4.3 (Zero-Trust Edition)
"""

import numpy as np
import logging
from typing import Tuple, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAlignmentHandler:
    """
    Handle index mapping and alignment between tabular (LightGBM) and
    sequential (LSTM) model predictions

    The core problem: LightGBM makes predictions on all samples [0...N-1],
    but LSTM can only make predictions on samples where a complete 60-day
    sliding window exists, i.e., [59...N-1].

    This handler ensures both predictions are aligned to the same index space.
    """

    def __init__(self, sequence_length: int = 60, stride: int = 1):
        """
        Initialize alignment handler

        Args:
            sequence_length: Sliding window length (default: 60)
            stride: Stride for sliding windows (default: 1)
        """
        self.sequence_length = sequence_length
        self.stride = stride
        logger.info(
            f"DataAlignmentHandler initialized: "
            f"sequence_length={sequence_length}, stride={stride}"
        )

    def get_valid_indices(self, N_samples: int) -> np.ndarray:
        """
        Get indices valid for both LightGBM and LSTM predictions

        LightGBM: [0...N-1]
        LSTM: [sequence_length-1...N-1]
        Overlap: [sequence_length-1...N-1]

        Args:
            N_samples: Total number of samples in dataset

        Returns:
            Array of valid indices
        """
        valid_start = self.sequence_length - 1
        valid_end = N_samples
        return np.arange(valid_start, valid_end)

    def create_index_mapping(self, N_samples: int) -> Dict:
        """
        Create mapping from LSTM output index to original sample index

        For a sliding window dataset with sequence_length=60 and stride=1:
        - Window 0: samples [0...59] → label at sample 59
        - Window 1: samples [1...60] → label at sample 60
        - Window i: samples [i...i+59] → label at sample i+59

        Therefore: LSTM output index i maps to original index (i + sequence_length - 1)

        Args:
            N_samples: Total number of samples in original dataset

        Returns:
            Dictionary containing:
            {
                'lstm_to_original': array mapping LSTM output indices to original indices,
                'valid_indices': array of valid sample indices,
                'N_windows': number of LSTM windows,
                'N_samples': total samples in dataset
            }
        """
        # Calculate number of windows
        N_windows = (N_samples - self.sequence_length) // self.stride + 1

        # Create mapping: LSTM window i → original sample i + (sequence_length - 1)
        lstm_to_original = np.arange(
            self.sequence_length - 1,
            self.sequence_length - 1 + N_windows * self.stride,
            self.stride
        )

        return {
            "lstm_to_original": lstm_to_original,
            "valid_indices": self.get_valid_indices(N_samples),
            "N_windows": N_windows,
            "N_samples": N_samples,
        }

    def align_predictions(
        self, lgb_proba: np.ndarray, lstm_proba: np.ndarray, N_samples: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Align LightGBM and LSTM predictions to same index space

        Selects only the valid indices from LightGBM predictions where LSTM
        also has valid predictions, ensuring both arrays have the same shape.

        Args:
            lgb_proba: LightGBM predictions shape (N, 3)
            lstm_proba: LSTM predictions shape (N-59, 3) or (N_windows, 3)
            N_samples: Original dataset size (N)

        Returns:
            Tuple of:
            - lgb_aligned: LightGBM predictions at valid indices (N_windows, 3)
            - lstm_aligned: LSTM predictions (N_windows, 3)
            - valid_idx: Array of valid indices used
        """
        try:
            # Get index mapping
            mapping = self.create_index_mapping(N_samples)
            valid_idx = mapping["valid_indices"]
            N_windows = mapping["N_windows"]

            # Validate input shapes
            assert lgb_proba.shape[0] == N_samples, (
                f"LightGBM predictions shape {lgb_proba.shape[0]} "
                f"doesn't match dataset size {N_samples}"
            )
            assert lgb_proba.shape[1] == 3, f"Expected 3 classes, got {lgb_proba.shape[1]}"

            assert lstm_proba.shape[0] == N_windows, (
                f"LSTM predictions shape {lstm_proba.shape[0]} "
                f"doesn't match expected windows {N_windows}"
            )
            assert lstm_proba.shape[1] == 3, f"Expected 3 classes, got {lstm_proba.shape[1]}"

            # Select valid indices from LightGBM
            lgb_aligned = lgb_proba[valid_idx]  # (N_windows, 3)

            # LSTM already at correct indices
            lstm_aligned = lstm_proba  # (N_windows, 3)

            # Final validation
            assert (
                lgb_aligned.shape[0] == lstm_aligned.shape[0]
            ), f"Shape mismatch after alignment: {lgb_aligned.shape[0]} vs {lstm_aligned.shape[0]}"

            logger.info(
                f"Predictions aligned successfully: "
                f"LGB {lgb_proba.shape} → {lgb_aligned.shape}, "
                f"LSTM {lstm_proba.shape} → {lstm_aligned.shape}"
            )

            return lgb_aligned, lstm_aligned, valid_idx

        except Exception as e:
            logger.error(f"Error aligning predictions: {e}")
            raise

    def get_alignment_info(self, N_samples: int) -> str:
        """
        Get human-readable alignment information

        Args:
            N_samples: Total number of samples

        Returns:
            Formatted string describing the alignment
        """
        mapping = self.create_index_mapping(N_samples)
        N_windows = mapping["N_windows"]
        N_lost = self.sequence_length - 1

        info = f"""
        ╔════════════════════════════════════════════════════════╗
        ║          Data Alignment Information                    ║
        ╚════════════════════════════════════════════════════════╝

        Dataset Statistics:
          Total samples: {N_samples}
          Sequence length: {self.sequence_length}
          Stride: {self.stride}

        LSTM Windows:
          Number of windows: {N_windows}
          Samples lost to windowing: {N_lost}

        Index Ranges:
          LightGBM valid indices: [0...{N_samples-1}]
          LSTM valid indices: [{self.sequence_length-1}...{N_samples-1}]
          Overlapping indices: [{self.sequence_length-1}...{N_samples-1}]

        Alignment:
          Both models predict on {N_windows} samples
          Index range: [{self.sequence_length-1}...{N_samples-1}]
        """
        return info


if __name__ == "__main__":
    # Test alignment handler
    logger.info("Testing DataAlignmentHandler...")

    try:
        # Test with realistic dataset size
        N_samples = 1000
        handler = DataAlignmentHandler(sequence_length=60, stride=1)

        # Get alignment info
        info = handler.get_alignment_info(N_samples)
        logger.info(info)

        # Create dummy predictions
        lgb_proba = np.random.dirichlet([1, 1, 1], N_samples).astype(np.float32)
        N_windows = (N_samples - 60) + 1  # Number of windows
        lstm_proba = np.random.dirichlet([1, 1, 1], N_windows).astype(np.float32)

        logger.info(f"LGB predictions shape: {lgb_proba.shape}")
        logger.info(f"LSTM predictions shape: {lstm_proba.shape}")

        # Align predictions
        lgb_aligned, lstm_aligned, valid_idx = handler.align_predictions(
            lgb_proba, lstm_proba, N_samples
        )

        logger.info(f"✓ Aligned LGB shape: {lgb_aligned.shape}")
        logger.info(f"✓ Aligned LSTM shape: {lstm_aligned.shape}")
        logger.info(f"✓ Valid indices range: [{valid_idx[0]}...{valid_idx[-1]}]")
        logger.info(f"✓ Both shapes match: {lgb_aligned.shape == lstm_aligned.shape}")

    except Exception as e:
        logger.error(f"Test failed: {e}")

    logger.info("DataAlignmentHandler tests complete!")

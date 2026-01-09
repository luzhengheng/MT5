"""
TASK #070: LSTM/GRU Models for Sequence Learning
Protocol: v4.3 (Zero-Trust Edition)

Implements recurrent neural network architectures for financial time-series
prediction using LSTMs or GRUs with proper initialization.
"""

import torch
import torch.nn as nn
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class LSTMModel(nn.Module):
    """
    LSTM-based sequence model for binary classification.

    Architecture:
    Input -> LSTM (num_layers) -> Dropout -> Linear -> Output (logits)

    LSTM processes sequences and outputs final hidden state.
    Linear layer produces binary classification logits.
    """

    def __init__(self,
                 input_size: int,
                 hidden_dim: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 output_size: int = 2):
        """
        Initialize LSTM model.

        Args:
            input_size: Number of features per timestep
            hidden_dim: Hidden state dimension
            num_layers: Number of LSTM layers
            dropout: Dropout probability
            output_size: Number of output classes (2 for binary)
        """
        super(LSTMModel, self).__init__()

        self.input_size = input_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.output_size = output_size

        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Dropout layer
        self.dropout = nn.Dropout(dropout)

        # Output layer
        self.fc = nn.Linear(hidden_dim, output_size)

        # Initialize weights
        self._init_weights()

        logger.info(f"Created LSTMModel:")
        logger.info(f"  Input size: {input_size}")
        logger.info(f"  Hidden dim: {hidden_dim}")
        logger.info(f"  Num layers: {num_layers}")
        logger.info(f"  Dropout: {dropout}")
        logger.info(f"  Output size: {output_size}")

    def _init_weights(self):
        """Initialize weights using Xavier/Kaiming initialization."""
        for name, param in self.named_parameters():
            if 'weight' in name:
                if 'lstm' in name:
                    # LSTM weights - orthogonal initialization
                    nn.init.orthogonal_(param)
                elif 'fc' in name:
                    # Linear layer - Xavier
                    nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                # Biases - zero
                nn.init.constant_(param, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through LSTM.

        Args:
            x: Input tensor (batch_size, sequence_length, input_size)

        Returns:
            Output logits (batch_size, output_size)
        """
        # LSTM: returns (output, (h_n, c_n))
        # output: (batch_size, sequence_length, hidden_dim)
        # h_n: (num_layers, batch_size, hidden_dim) - final hidden state
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Use final hidden state (h_n[-1]) as feature representation
        # h_n[-1]: (batch_size, hidden_dim)
        last_hidden = h_n[-1]

        # Apply dropout
        dropped = self.dropout(last_hidden)

        # Linear output layer
        logits = self.fc(dropped)

        return logits

    def get_num_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class GRUModel(nn.Module):
    """
    GRU-based sequence model for binary classification.

    Similar to LSTM but with fewer parameters (no cell state).

    Architecture:
    Input -> GRU (num_layers) -> Dropout -> Linear -> Output (logits)
    """

    def __init__(self,
                 input_size: int,
                 hidden_dim: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 output_size: int = 2):
        """
        Initialize GRU model.

        Args:
            input_size: Number of features per timestep
            hidden_dim: Hidden state dimension
            num_layers: Number of GRU layers
            dropout: Dropout probability
            output_size: Number of output classes (2 for binary)
        """
        super(GRUModel, self).__init__()

        self.input_size = input_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.output_size = output_size

        # GRU layer
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Dropout layer
        self.dropout = nn.Dropout(dropout)

        # Output layer
        self.fc = nn.Linear(hidden_dim, output_size)

        # Initialize weights
        self._init_weights()

        logger.info(f"Created GRUModel:")
        logger.info(f"  Input size: {input_size}")
        logger.info(f"  Hidden dim: {hidden_dim}")
        logger.info(f"  Num layers: {num_layers}")
        logger.info(f"  Dropout: {dropout}")
        logger.info(f"  Output size: {output_size}")

    def _init_weights(self):
        """Initialize weights using Xavier/Kaiming initialization."""
        for name, param in self.named_parameters():
            if 'weight' in name:
                if 'gru' in name:
                    # GRU weights - orthogonal
                    nn.init.orthogonal_(param)
                elif 'fc' in name:
                    # Linear layer - Xavier
                    nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                # Biases - zero
                nn.init.constant_(param, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GRU.

        Args:
            x: Input tensor (batch_size, sequence_length, input_size)

        Returns:
            Output logits (batch_size, output_size)
        """
        # GRU: returns (output, h_n)
        # output: (batch_size, sequence_length, hidden_dim)
        # h_n: (num_layers, batch_size, hidden_dim) - final hidden state
        gru_out, h_n = self.gru(x)

        # Use final hidden state (h_n[-1])
        # h_n[-1]: (batch_size, hidden_dim)
        last_hidden = h_n[-1]

        # Apply dropout
        dropped = self.dropout(last_hidden)

        # Linear output layer
        logits = self.fc(dropped)

        return logits

    def get_num_parameters(self) -> int:
        """Return total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_model(model_type: str = "lstm",
                 input_size: int = 23,
                 hidden_dim: int = 64,
                 num_layers: int = 2,
                 dropout: float = 0.2,
                 output_size: int = 2,
                 device: str = "cpu") -> nn.Module:
    """
    Factory function to create LSTM or GRU model.

    Args:
        model_type: 'lstm' or 'gru'
        input_size: Number of input features
        hidden_dim: Hidden dimension
        num_layers: Number of layers
        dropout: Dropout rate
        output_size: Number of output classes (default: 2 for binary)
        device: 'cpu' or 'cuda'

    Returns:
        Initialized model on specified device
    """
    if model_type.lower() == "lstm":
        model = LSTMModel(input_size, hidden_dim, num_layers, dropout, output_size)
    elif model_type.lower() == "gru":
        model = GRUModel(input_size, hidden_dim, num_layers, dropout, output_size)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

    model = model.to(device)

    num_params = model.get_num_parameters()
    logger.info(f"Model created on device '{device}' with {num_params:,} parameters")

    return model

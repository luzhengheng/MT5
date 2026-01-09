# Task #070 Quick Start Guide

## Running the Deep Learning Baseline

### Prerequisites
```bash
# Ensure PyTorch is installed
pip install torch>=2.0.0

# Verify PyTorch installation
python3 -c "import torch; print(torch.__version__)"
```

### Quick Start

```bash
# 1. Generate or load dataset from Task #069
python3 scripts/dataset_builder.py --symbol AAPL.US

# 2. Run training
python3 scripts/train_dl_baseline.py \
  --dataset outputs/datasets/task_069_dataset.pkl \
  --epochs 5 \
  --model-type lstm

# 3. View results in MLflow
mlflow ui
# Navigate to http://localhost:5000
```

### Configuration

Edit `config/ml_training_config.yaml` under `deep_learning:` section:

```yaml
deep_learning:
  sequence_length: 60      # Sliding window size
  batch_size: 32          # Batch size
  model_type: "lstm"      # Choose between 'lstm' or 'gru'
  hidden_dim: 64          # Hidden state dimension
  num_layers: 2           # Number of RNN layers
  dropout: 0.2            # Dropout rate
  learning_rate: 0.001    # Adam optimizer LR
  num_epochs: 5           # Training epochs
  device: "cpu"           # Use "cuda" if GPU available
```

### Expected Output

```
Epoch 1/5 | Train Loss: 1.099187 | Val Loss: 1.098704
Epoch 2/5 | Train Loss: 1.092886 | Val Loss: 1.098907
Epoch 3/5 | Train Loss: 1.085296 | Val Loss: 1.100994
Epoch 4/5 | Train Loss: 1.072679 | Val Loss: 1.112594
Epoch 5/5 | Train Loss: 1.055366 | Val Loss: 1.122719
```

### Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'torch'`
**Solution:** Run `pip install torch>=2.0.0`

**Issue:** `FileNotFoundError: outputs/datasets/task_069_dataset.pkl`
**Solution:** Run `python3 scripts/dataset_builder.py` first to create the dataset

**Issue:** Dataset builder fails with PostgreSQL connection error
**Solution:** This is expected if PostgreSQL is not running. Use the synthetic dataset generator for testing.

## Architecture Overview

```
Raw Data (Task #069)
    ↓
Sliding Window (60 timesteps)
    ↓
LSTM/GRU Network
    ↓
Classification Head (3 classes)
    ↓
MLflow Tracking
    ↓
Model Artifact
```

## Performance Tips

- Use CUDA (`device: "cuda"`) if GPU available - 10-20x faster
- Increase `batch_size` to 64 or 128 if memory permits
- Try `model_type: "gru"` for faster training (fewer parameters)
- Experiment with `hidden_dim` between 32 and 128

## References

- Main training script: `scripts/train_dl_baseline.py`
- Dataset loader: `src/model/dl/dataset.py`
- Model definitions: `src/model/dl/models.py`
- Configuration: `config/ml_training_config.yaml`

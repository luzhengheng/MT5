# Task #072: Ensemble Inference Engine - Quick Start Guide

## Installation

```bash
# Install dependencies (if not already installed)
pip install mlflow lightgbm torch scikit-learn

# Verify ensemble module imports
python3 -c "from src.model.ensemble.loader import ModelLoader; print('✓ Ensemble module ready')"
```

## Quick Execution

### Option 1: Run Full Evaluation Pipeline

```bash
# Evaluate LightGBM, LSTM, and Ensemble models
python3 scripts/eval_ensemble.py

# Expected output:
# ✓ Models loaded from MLflow
# ✓ Predictions generated
# ✓ Metrics computed
# ✓ Results logged to MLflow experiment
```

### Option 2: Manual Model Loading

```python
from src.model.ensemble.loader import ModelLoader
from src.model.ensemble.predictors import LGBPredictor, LSTMPredictor
from src.model.ensemble.alignment import DataAlignmentHandler
from src.model.ensemble.ensemble import EnsemblePredictor

# Load models from MLflow
models = ModelLoader.load_both_models()
lgb_model = models['lgb_model']
lstm_model = models['lstm_model']

# Create wrappers and ensemble
lgb_pred = LGBPredictor(lgb_model)
lstm_pred = LSTMPredictor(lstm_model)
alignment = DataAlignmentHandler(sequence_length=60)
ensemble = EnsemblePredictor(lgb_pred, lstm_pred, alignment, weights=(0.5, 0.5))

# Get predictions
X_tabular = ...  # (N, 23) features
X_sequential = ...  # (N-59, 60, 23) sequences
ensemble_proba = ensemble.predict_proba(X_tabular, X_sequential)
```

## Configuration

### Adjust Ensemble Weights

```python
# Different weight distributions
ensemble = EnsemblePredictor(
    lgb_pred, lstm_pred, alignment,
    weights=(0.3, 0.7),  # Favor LSTM 70%
    use_stacking=False
)
```

### Enable Stacking Meta-Learner

```python
ensemble = EnsemblePredictor(
    lgb_pred, lstm_pred, alignment,
    weights=(0.5, 0.5),
    use_stacking=True  # Enable meta-learner
)

# Train on training data
ensemble.fit_meta_learner(X_train_tabular, X_train_sequential, y_train)

# Evaluate on test data
ensemble_proba = ensemble.predict_proba(X_test_tabular, X_test_sequential)
```

### Customize Alignment

```python
# Different sliding window settings
alignment = DataAlignmentHandler(
    sequence_length=60,  # 60-day windows
    stride=1  # Non-overlapping windows (stride=1 = overlapping by 59)
)
```

## Troubleshooting

### Issue: "No runs found in experiment"

**Problem**: MLflow experiments not found

**Solution**:
- Verify Task #069 and #071 completed successfully
- Check MLflow experiments: `mlflow experiments list`
- Run baseline training first: `python3 scripts/train_baseline.py`

### Issue: "Shape mismatch in alignment"

**Problem**: LSTM window count doesn't match formula

**Solution**:
- Check dataset size: `len(X_val)`
- Expected windows: `(N_samples - 60) + 1`
- Verify sequence_length=60 matches LSTM training

### Issue: "Index out of bounds"

**Problem**: Trying to predict on sample indices [0...58]

**Solution**:
- Valid prediction indices: [59...N-1]
- Use `alignment.get_valid_indices(N_samples)` to get valid range
- Only first 59 samples don't have valid LSTM windows

## Performance Tips

1. **Use GPU for LSTM**: `lstm_pred = LSTMPredictor(lstm_model, device='cuda')`
2. **Batch predictions**: Process entire validation set at once
3. **Profile bottleneck**:
   ```bash
   python3 -m cProfile -s cumtime scripts/eval_ensemble.py | head -20
   ```

## Testing

```bash
# Run embedded unit tests
python3 src/model/ensemble/loader.py      # Test MLflow loading
python3 src/model/ensemble/predictors.py  # Test prediction wrappers
python3 src/model/ensemble/alignment.py   # Test index alignment
python3 src/model/ensemble/ensemble.py    # Test ensemble logic
```

## Integration with MLflow

View ensemble results:

```bash
# Start MLflow server
mlflow server --backend-store-uri=sqlite:///mlflow.db

# Navigate to http://localhost:5000
# View experiment: task_072_ensemble
# Compare runs, metrics, parameters
```

## API Reference

### ModelLoader

```python
# Load best LightGBM model
lgb_model, lgb_run_id = ModelLoader.load_best_lgb_model(
    experiment_name="task_069_baseline"
)

# Load best LSTM model
lstm_model, lstm_run_id = ModelLoader.load_best_lstm_model(
    experiment_name="task_071_lstm_hpo",
    input_size=23
)

# Load both
models = ModelLoader.load_both_models()
```

### LGBPredictor & LSTMPredictor

```python
# Unified predict_proba interface
proba = predictor.predict_proba(X)  # Returns (N, 3)
labels = predictor.predict(X)  # Returns (N,)
confidence = predictor.predict_confidence(X)  # Returns (N,)
```

### DataAlignmentHandler

```python
# Get valid indices
valid_idx = alignment.get_valid_indices(N_samples)

# Create mapping
mapping = alignment.create_index_mapping(N_samples)

# Align predictions
lgb_aligned, lstm_aligned, valid_idx = alignment.align_predictions(
    lgb_proba, lstm_proba, N_samples
)
```

### EnsemblePredictor

```python
# Weighted average (default)
proba = ensemble.predict_proba(X_tabular, X_sequential)  # (N-59, 3)

# With stacking
ensemble.fit_meta_learner(X_train, X_train_seq, y_train)
proba = ensemble.predict_proba(X_test, X_test_seq)

# Confidence scores
confidence = ensemble.predict_confidence(X_tabular, X_sequential)
```

## Examples

### Example 1: Compare Models

```python
from sklearn.metrics import accuracy_score

# Get predictions
lgb_pred_labels = lgb_pred.predict(X_val)
lstm_pred_labels = lstm_pred.predict(torch.FloatTensor(X_val_windows))
ensemble_labels = ensemble.predict(X_val, torch.FloatTensor(X_val_windows))

# Get accuracy (on valid indices)
valid_idx = alignment.get_valid_indices(len(y_val))
y_val_aligned = y_val[valid_idx]

acc_lgb = accuracy_score(y_val_aligned, lgb_pred_labels[valid_idx])
acc_lstm = accuracy_score(y_val_aligned, lstm_pred_labels)
acc_ensemble = accuracy_score(y_val_aligned, ensemble_labels)

print(f"LGB Accuracy: {acc_lgb:.4f}")
print(f"LSTM Accuracy: {acc_lstm:.4f}")
print(f"Ensemble Accuracy: {acc_ensemble:.4f}")
```

### Example 2: Analyze Predictions

```python
# Get ensemble probabilities
proba = ensemble.predict_proba(X_val, torch.FloatTensor(X_val_windows))

# Analyze class distribution
print(f"Class 0 (short): {(np.argmax(proba, axis=1) == 0).sum()}")
print(f"Class 1 (hold):  {(np.argmax(proba, axis=1) == 1).sum()}")
print(f"Class 2 (long):  {(np.argmax(proba, axis=1) == 2).sum()}")

# Find uncertain predictions
max_proba = np.max(proba, axis=1)
uncertain_idx = max_proba < 0.4
print(f"Uncertain predictions: {uncertain_idx.sum()}")
```

---

**Quick Start Guide Version**: 1.0
**Last Updated**: 2026-01-10
**Protocol**: v4.3 (Zero-Trust Edition)

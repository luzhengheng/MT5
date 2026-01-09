# Task #073: Quick Start Guide
## Train & Register Stacking Meta-Learner

---

## 5-Minute Quick Start

### Prerequisites

```bash
# Ensure MLflow is running
mlflow server --backend-store-uri sqlite:///mlflow.db &

# Verify imports
python3 -c "import mlflow, torch, sklearn; print('✓ All imports OK')"
```

### Run the Pipeline

```bash
# 1. Train and register stacking model (5 minutes)
python3 scripts/register_production_model.py

# 2. Verify model quality
python3 scripts/verify_stacking.py

# 3. View in MLflow UI
open http://localhost:5000
# Look for experiment: task_073_stacking
# Model Registry: stacking_ensemble_task_073 (Stage: Staging)
```

---

## Module Usage Guide

### 1. OOF Prediction Generator

```python
from src.model.ensemble.oof_generator import OOFPredictionGenerator
from src.model.ensemble.predictors import LGBPredictor, LSTMPredictor
from src.model.ensemble.loader import ModelLoader

# Load pre-trained models
models = ModelLoader.load_both_models()
lgb_pred = LGBPredictor(models['lgb_model'], models['feature_names'])
lstm_pred = LSTMPredictor(models['lstm_model'], device='cpu')

# Create OOF generator
oof_gen = OOFPredictionGenerator()

# Generate OOF predictions
lgb_oof, lstm_oof, valid_idx = oof_gen.generate_oof_predictions(
    lgb_pred, lstm_pred,
    X_tabular,      # (N, 23)
    X_sequential,   # (N-59, 60, 23)
    y_train         # (N,)
)

# Output shapes
print(f"LGB OOF: {lgb_oof.shape}")      # (N, 3)
print(f"LSTM OOF: {lstm_oof.shape}")    # (N-59, 3)
print(f"Valid indices: {len(valid_idx)}")  # [59...N-1]
```

### 2. Meta-Learner Training

```python
from src.model.ensemble.meta_learner import StackingMetaLearner

# Create meta-learner
meta_trainer = StackingMetaLearner()

# Train on OOF predictions
meta_learner = meta_trainer.train(
    lgb_oof,        # (N, 3)
    lstm_oof,       # (N-59, 3)
    y_train,        # (N,)
    valid_idx       # Indices [59...N-1]
)

# Make predictions
ensemble_proba = meta_trainer.predict_proba(
    lgb_test_proba,    # (M, 3)
    lstm_test_proba    # (M, 3)
)

print(f"Ensemble predictions: {ensemble_proba.shape}")  # (M, 3)

# Save meta-learner
meta_trainer.save("meta_learner.pkl")

# Load later
loaded = StackingMetaLearner.load("meta_learner.pkl")
```

### 3. MLflow Model Registration

```python
import mlflow
from src.model.ensemble.mlflow_model import (
    StackingEnsembleMLflowModel,
    create_mlflow_model_artifacts
)

# Prepare artifacts
artifacts = create_mlflow_model_artifacts(
    lgb_model_path="path/to/lgb.txt",
    lstm_model_path="path/to/lstm.pt",
    lstm_config={'input_size': 23, 'hidden_dim': 96, ...},
    meta_learner=trained_lr_model,
    feature_names=feature_names,
    artifact_dir="mlflow_artifacts"
)

# Register to MLflow
with mlflow.start_run():
    mlflow.log_param('cv_splits', 5)
    mlflow.log_metric('val_accuracy', 0.5412)

    mlflow.pyfunc.log_model(
        artifact_path="ensemble_model",
        python_model=StackingEnsembleMLflowModel(),
        artifacts=artifacts,
        registered_model_name="stacking_ensemble_task_073"
    )

# Transition to Staging
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="stacking_ensemble_task_073",
    version="1",
    stage="Staging"
)
```

### 4. Model Inference

```python
import pandas as pd
import numpy as np

# Load model
model = mlflow.pyfunc.load_model(
    "models:/stacking_ensemble_task_073/Staging"
)

# Prepare input
input_data = pd.DataFrame({
    'X_tabular': [np.random.randn(23).astype(np.float32) for _ in range(10)],
    'X_sequential': [np.random.randn(60, 23).astype(np.float32) for _ in range(10)]
})

# Predict
predictions = model.predict(input_data)
print(predictions.shape)  # (10, 3)
# Columns: ['class_0_prob', 'class_1_prob', 'class_2_prob']
```

---

## Configuration Options

### OOF Generation

```python
from src.models.validation import PurgedKFold
from src.model.ensemble.alignment import DataAlignmentHandler

oof_gen = OOFPredictionGenerator(
    cv_splitter=PurgedKFold(n_splits=5, embargo_pct=0.01),
    alignment_handler=DataAlignmentHandler(sequence_length=60)
)
```

**Parameters**:
- `n_splits`: Number of CV folds (default: 5)
- `embargo_pct`: Embargo percentage (default: 0.01 = 1%)
- `sequence_length`: Sliding window size (default: 60)

### Meta-Learner

```python
from src.model.ensemble.meta_learner import StackingMetaLearner

meta_learner = StackingMetaLearner()
# Default: LogisticRegression(
#     penalty='l2', C=1.0, max_iter=1000,
#     solver='lbfgs', random_state=42
# )
```

**Parameters**:
- `C`: Inverse regularization strength (default: 1.0, lower = stronger regularization)
- `max_iter`: Maximum iterations (default: 1000)
- `solver`: Optimization algorithm (default: 'lbfgs')

---

## Verification

### Check OOF Quality

```python
# Verify shapes
assert lgb_oof.shape == (N, 3)
assert lstm_oof.shape == (N-59, 3)

# Verify probabilities sum to 1
assert np.allclose(lgb_oof.sum(axis=1), 1.0)
assert np.allclose(lstm_oof.sum(axis=1), 1.0)

# Check for NaN
assert not np.isnan(lgb_oof).any()
assert not np.isnan(lstm_oof).any()
```

### Check Model Registration

```python
import mlflow

client = mlflow.tracking.MlflowClient()

# List registered models
models = client.search_registered_models()
for model in models:
    print(f"{model.name}: {model.latest_versions}")

# Get specific model
model = client.get_registered_model("stacking_ensemble_task_073")
print(f"Model: {model.name}")
print(f"Versions: {[v.version for v in model.latest_versions]}")
print(f"Stages: {[v.current_stage for v in model.latest_versions]}")
```

### Run Verification Suite

```bash
# Run all verification tests
python3 scripts/verify_stacking.py --verbose

# Expected output:
# ✓ OOF Shapes
# ✓ OOF Probabilities
# ✓ Data Leakage Check
# ✓ Meta-learner Improvement
# ✓ MLflow Registration
# ✓ MLflow Model Loading
```

---

## Troubleshooting

### Issue: "No runs found in experiment"

**Problem**: ModelLoader can't find Task #069 or #071 models

**Solution**:
```bash
# Check MLflow experiments
mlflow experiments list

# Check runs in experiment
mlflow runs list --experiment-name task_069_baseline

# Verify models were trained in Task #069 and #071
```

### Issue: "Shape mismatch after alignment"

**Problem**: LSTM OOF shape doesn't match expected (N_windows, 3)

**Solution**:
```python
# Verify sliding window calculation
N_samples = 1000
sequence_length = 60
expected_windows = N_samples - sequence_length + 1
print(f"Expected windows: {expected_windows}")  # 941

# Check actual LSTM OOF shape
print(f"Actual LSTM OOF shape: {lstm_oof.shape}")
# Should be (941, 3)
```

### Issue: "Meta-learner probabilities don't sum to 1"

**Problem**: Output probabilities are not normalized

**Solution**: The model uses LogisticRegression.predict_proba() which automatically normalizes. If issue persists:

```python
# Manual normalization
ensemble_proba_norm = ensemble_proba / ensemble_proba.sum(axis=1, keepdims=True)
```

### Issue: "MLflow model loading fails"

**Problem**: Model can't load artifacts

**Solution**:
```bash
# Check artifact paths
mlflow artifacts list -r <run_id>

# Verify artifact directory exists
ls -la mlruns/task_073_stacking/

# Check MLflow logging
mlflow runs info <run_id>
```

---

## Performance Tuning

### Improve Ensemble Accuracy

```python
# 1. Adjust meta-learner regularization
# Less regularization (allows more complex decision boundaries)
meta_trainer.meta_model.C = 0.1  # default is 1.0

# 2. Use different CV strategy
from src.models.validation import WalkForward
oof_gen = OOFPredictionGenerator(
    cv_splitter=WalkForward(n_folds=3, train_size=500, test_size=100)
)

# 3. Adjust base model weights
ensemble.weights = (0.6, 0.4)  # More weight to LGB
```

### Reduce Inference Latency

```python
# Pre-load model
model = mlflow.pyfunc.load_model("models:/stacking_ensemble_task_073/Production")

# Batch predictions
import pandas as pd
batch_size = 100

predictions = []
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    pred = model.predict(batch)
    predictions.append(pred)

result = pd.concat(predictions)
```

---

## API Reference

### OOFPredictionGenerator

```python
class OOFPredictionGenerator:
    def __init__(self, cv_splitter=None, alignment_handler=None)

    def generate_oof_predictions(
        lgb_predictor, lstm_predictor,
        X_tabular, X_sequential, y_train
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]

    # Returns: (lgb_oof, lstm_oof, valid_indices)
```

### StackingMetaLearner

```python
class StackingMetaLearner:
    def __init__(self, alignment_handler=None, meta_model=None)

    def train(
        lgb_oof, lstm_oof, y_train, valid_indices
    ) -> LogisticRegression

    def predict_proba(
        lgb_proba, lstm_proba
    ) -> np.ndarray  # Shape (N, 3)

    def predict(
        lgb_proba, lstm_proba
    ) -> np.ndarray  # Shape (N,)

    def save(filepath: str)

    @classmethod
    def load(filepath: str) -> StackingMetaLearner
```

### StackingEnsembleMLflowModel

```python
class StackingEnsembleMLflowModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context)

    def predict(self, context, model_input) -> pd.DataFrame
    # Input DataFrame columns: ['X_tabular', 'X_sequential']
    # Output DataFrame columns: ['class_0_prob', 'class_1_prob', 'class_2_prob']
```

---

## Example: Complete Pipeline

```python
#!/usr/bin/env python3
"""Complete example of Task #073 pipeline"""

import numpy as np
from src.model.ensemble.loader import ModelLoader
from src.model.ensemble.predictors import LGBPredictor, LSTMPredictor
from src.model.ensemble.oof_generator import OOFPredictionGenerator
from src.model.ensemble.meta_learner import StackingMetaLearner

# 1. Load models
models = ModelLoader.load_both_models()
lgb_pred = LGBPredictor(models['lgb_model'], models['feature_names'])
lstm_pred = LSTMPredictor(models['lstm_model'])

# 2. Generate OOF
oof_gen = OOFPredictionGenerator()
lgb_oof, lstm_oof, valid_idx = oof_gen.generate_oof_predictions(
    lgb_pred, lstm_pred, X_train, X_seq, y_train
)

# 3. Train meta-learner
meta = StackingMetaLearner()
meta.train(lgb_oof, lstm_oof, y_train, valid_idx)

# 4. Predict on test set
lgb_test = lgb_pred.predict_proba(X_test)
lstm_test = lstm_pred.predict_proba(X_seq_test)
ensemble_preds = meta.predict_proba(lgb_test[valid_idx], lstm_test)

print(f"✓ Ensemble predictions: {ensemble_preds.shape}")
```

---

## Next Steps

1. **Verify Model Quality**
   ```bash
   python3 scripts/verify_stacking.py
   ```

2. **Promote to Production**
   - Open MLflow UI: http://localhost:5000
   - Navigate to Models → stacking_ensemble_task_073
   - Select latest version, click "Transition" → "Production"

3. **Deploy Model**
   ```bash
   mlflow models serve \
       -m models:/stacking_ensemble_task_073/Production \
       --port 5001
   ```

4. **Monitor Performance**
   - Track inference latency
   - Monitor prediction quality
   - Set up automated retraining triggers

---

## Support

For issues or questions:
- Check COMPLETION_REPORT.md for detailed architecture
- Review inline code documentation
- Run `python3 scripts/verify_stacking.py --verbose` for diagnostics

---

**Last Updated**: 2026-01-10
**Protocol**: Zero-Trust v4.3

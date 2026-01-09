# Task #071: Optuna Hyperparameter Optimization - Quick Start Guide

## Prerequisites

```bash
# 1. Ensure Task #070 dataset exists
ls -lh outputs/datasets/task_069_dataset.pkl

# 2. Install dependencies (if not already installed)
pip install optuna==4.6.0 torch mlflow

# 3. Verify installation
python3 -c "import optuna, torch, mlflow; print('✓ All dependencies OK')"
```

## Quick Execution

### Run 10-Trial Optimization Study

```bash
python3 scripts/tune_lstm.py \
    --dataset outputs/datasets/task_069_dataset.pkl \
    --n-trials 10 \
    --device cpu \
    --seed 42
```

**Expected runtime**: ~5-10 minutes on CPU (depends on dataset size)

### Run 20-Trial Study (More Thorough)

```bash
python3 scripts/tune_lstm.py \
    --dataset outputs/datasets/task_069_dataset.pkl \
    --n-trials 20 \
    --device cpu \
    --seed 42
```

### Run on GPU (Faster)

```bash
python3 scripts/tune_lstm.py \
    --dataset outputs/datasets/task_069_dataset.pkl \
    --n-trials 20 \
    --device cuda \
    --seed 42
```

## View Results

### Via Terminal

```bash
# Load and print best trial
python3 << 'EOF'
import optuna

study = optuna.load_study(
    study_name='lstm_hpo_study',
    storage='sqlite:///optuna.db'
)

best = study.best_trial
print(f"\n{'='*60}")
print(f"Best Trial: #{best.number}")
print(f"Best Validation Loss: {best.value:.6f}")
print(f"{'='*60}\n")
print("Best Hyperparameters:")
for key, value in best.params.items():
    print(f"  {key:20s}: {value}")
print(f"\n{'='*60}")

# Show top 5 trials
print(f"\nTop 5 Trials:")
trials_df = study.trials_dataframe().sort_values('value').head(5)
for idx, (_, row) in enumerate(trials_df.iterrows(), 1):
    print(f"  {idx}. Trial {int(row['number']):2d}: Loss={row['value']:.6f}")
EOF
```

### Via MLflow UI

```bash
# Start MLflow server
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns

# Open in browser
# http://localhost:5000
```

Then navigate to experiment `task_071_lstm_hpo` to see:
- All trial parameters in table view
- Metrics (best_val_loss, cv_mean_score)
- Feature importance plots
- Hyperparameter correlation matrix

## Configuration Reference

### Command-Line Arguments

```
--dataset PATH                Path to dataset pickle file
                              Default: outputs/datasets/task_069_dataset.pkl
--n-trials N                  Number of optimization trials
                              Default: 20
--device {cpu,cuda}           Device to use for training
                              Default: cpu
--seed N                      Random seed for reproducibility
                              Default: 42
--optuna-db PATH              Path to Optuna SQLite database
                              Default: optuna.db
```

### Hyperparameter Search Space

| Parameter | Type | Range | Default (Task #070) |
|-----------|------|-------|-----|
| `learning_rate` | float | [1e-5, 1e-2] log scale | 0.001 |
| `hidden_dim` | int | [32, 128] step 16 | 64 |
| `num_layers` | int | [1, 3] | 2 |
| `dropout` | float | [0.0, 0.5] step 0.1 | 0.2 |
| `batch_size` | categorical | [16, 32, 64] | 32 |

### Pruning Configuration

- **Pruner Type**: Median-based (early stopping)
- **Warmup Steps**: 2 (don't prune until epoch 2)
- **Min Trials**: 2 (at least 2 completed trials before comparing)
- **Effect**: Automatically stops unpromising trials, saving computation

## Troubleshooting

### Issue: "FileNotFoundError: Dataset not found"
```bash
# Solution: Run Task #070 first to generate the dataset
python3 scripts/train_dl_baseline.py --dataset outputs/datasets/task_069_dataset.pkl
```

### Issue: "torch.cuda.OutOfMemoryError" on GPU
```bash
# Solution 1: Reduce batch size manually
# Edit scripts/tune_lstm.py and change:
# batch_size = trial.suggest_categorical('batch_size', [8, 16, 32])

# Solution 2: Use CPU instead
python3 scripts/tune_lstm.py --device cpu
```

### Issue: "No such table: studies" when loading optuna.db
```bash
# Solution: Delete corrupted database and start fresh
rm optuna.db
python3 scripts/tune_lstm.py --dataset outputs/datasets/task_069_dataset.pkl --n-trials 5
```

### Issue: Trials keep getting pruned early
```bash
# Solution: Adjust pruning strategy in tune_lstm.py
# Change line 251 to:
pruner = MedianPruner(n_warmup_steps=4, n_min_trials=3)
# This gives trials more time before comparing to median
```

## Understanding Trial Results

### Trial Status
- ✓ **COMPLETE**: Trial finished training (useful or not)
- ⊘ **PRUNED**: Trial stopped early due to poor performance
- ✗ **FAIL**: Trial crashed (exception raised)

### Efficiency Metrics

```python
# Calculate pruning efficiency
total_trials = 10
completed_trials = 7
pruned_trials = 3
failed_trials = 0

pruning_efficiency = (pruned_trials / total_trials) * 100
print(f"Pruning saved ~{pruned_trials * 10} epochs of training")
# Output: Pruning saved ~30 epochs of training
```

## Integration with Task #070 Baseline

### Compare Best Trial with Task #070

```bash
# Best Trial #1 from Task #071:
# Loss: 1.0977, lr=0.00397, hidden=96, layers=3, dropout=0.0

# Task #070 Baseline (best epoch):
# Loss: 1.1227, lr=0.001, hidden=64, layers=2, dropout=0.2

# Improvement: 2.2% (1.1227 -> 1.0977)
```

### Use Best Hyperparameters in Production

```python
# In your training script:
import optuna

# Load best trial
study = optuna.load_study(
    study_name='lstm_hpo_study',
    storage='sqlite:///optuna.db'
)

best_params = study.best_trial.params

# Create model with optimal hyperparameters
from src.model.dl.models import create_model

model = create_model(
    model_type='lstm',
    input_size=23,
    hidden_dim=best_params['hidden_dim'],
    num_layers=best_params['num_layers'],
    dropout=best_params['dropout'],
    output_size=3,
    device='cuda'
)

# Train with optimal learning rate
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=best_params['learning_rate']
)
```

## Advanced: Custom Hyperparameter Ranges

To search different hyperparameter ranges, edit `scripts/tune_lstm.py` lines 126-130:

```python
def objective(self, trial: optuna.Trial) -> float:
    # Modify these ranges:
    learning_rate = trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True)  # ← Wider range
    hidden_dim = trial.suggest_int('hidden_dim', 32, 256, step=32)  # ← Larger models
    num_layers = trial.suggest_int('num_layers', 1, 5)  # ← More layers
    dropout = trial.suggest_float('dropout', 0.0, 0.7, step=0.1)  # ← More regularization
    batch_size = trial.suggest_categorical('batch_size', [8, 16, 32, 64])  # ← More options
```

Then run:
```bash
python3 scripts/tune_lstm.py --n-trials 50  # More trials for wider search space
```

## Performance Tips

1. **GPU Training**: Use `--device cuda` for 5-10x speedup
2. **Parallel Trials**: Optuna supports parallel optimization (see `sampler.n_jobs`)
3. **Larger Search**: Increase `--n-trials` for 50+ for production
4. **Early Stopping**: Tune pruning parameters for your dataset size

## Next Steps

- **Task #072**: Use best hyperparameters to train final model
- **Task #073**: Ensemble multiple models trained with different random seeds
- **Production**: Deploy model using discovered hyperparameters with A/B testing

---

**Document Version**: v1.0
**Last Updated**: 2026-01-09
**Protocol**: v4.3 (Zero-Trust Edition)

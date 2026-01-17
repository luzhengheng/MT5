#!/usr/bin/env python3
"""
Quick training script to create XGBoost model matching Task #113 features
"""

import pandas as pd
import pickle
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

print("Loading training data...")
df = pd.read_parquet('/opt/mt5-crs/data_lake/ml_training_set.parquet')

print(f"Data shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Separate features and label
X = df.drop('label', axis=1)
y = df['label']

print(f"\nFeatures: {X.shape[1]}")
print(f"Samples: {len(y)}")

# Train test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=False
)

print(f"\nTraining samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")

# Train model
print("\nTraining XGBoost model...")
model = XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import accuracy_score, f1_score

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"\nModel Performance:")
print(f"  Accuracy: {accuracy:.4f}")
print(f"  F1-Score: {f1:.4f}")

# Save model
output_path = '/opt/mt5-crs/data/models/xgboost_task_114.pkl'
with open(output_path, 'wb') as f:
    pickle.dump(model, f)

print(f"\n✅ Model saved to: {output_path}")
print(f"   Features: {model.n_features_in_}")

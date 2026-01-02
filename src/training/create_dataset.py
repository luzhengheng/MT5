#!/usr/bin/env python3
"""
Dataset Creation Script
Loads features from parquet and creates training dataset
"""
import pandas as pd

def main():
    # Load existing feature data
    df = pd.read_parquet('data/sample_features.parquet')
    print(f"📊 Loaded features: {len(df)} rows")

    # Sort by timestamp
    df = df.sort_values('event_timestamp')

    # Generate target: future 1-period return
    df['target'] = df.groupby('ticker')['sma_7'].shift(-1) - df['sma_7']

    # Drop NaN rows
    df = df.dropna()

    # Save training dataset
    df.to_parquet('data/training_set.parquet', index=False)
    print(f"✅ Dataset created: {len(df)} rows, {len(df.columns)} columns")
    print(f"   Saved to: data/training_set.parquet")

if __name__ == '__main__':
    main()

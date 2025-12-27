#!/usr/bin/env python3
"""Monitor H1 training progress."""

import os
import time
import subprocess
from pathlib import Path

def check_training_status():
    """Check if H1 training is running and show model size."""
    # Check if process is running
    result = subprocess.run(
        "ps aux | grep 'python3 scripts/run_deep_training_h1' | grep -v grep",
        shell=True,
        capture_output=True,
        text=True
    )

    is_running = len(result.stdout.strip()) > 0

    model_file = Path("/opt/mt5-crs/data/models/production_v1.pkl")

    print("=" * 70)
    print("🔍 H1 Training Monitor")
    print("=" * 70)
    print()

    # Check training status
    if is_running:
        print("✅ Training Status: RUNNING")
        # Get memory usage
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'python3' in line:
                parts = line.split()
                if len(parts) > 5:
                    rss = parts[5]  # RSS memory
                    print(f"   Memory: {rss} KB")
    else:
        print("❌ Training Status: COMPLETED or NOT RUNNING")

    print()

    # Check model file
    if model_file.exists():
        size_mb = model_file.stat().st_size / 1024 / 1024
        mtime = model_file.stat().st_mtime
        import datetime
        mod_time = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

        print(f"✅ Model File: {model_file.name}")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"   Last modified: {mod_time}")
        print()

        if size_mb > 15:
            print("✅ Model size indicates successful training!")
        else:
            print("ℹ️  Model may still be training...")
    else:
        print("⏳ Model File: Not yet created (training in progress)")

    print()
    print("=" * 70)

    return is_running

if __name__ == "__main__":
    check_training_status()

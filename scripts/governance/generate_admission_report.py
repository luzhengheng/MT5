#!/usr/bin/env python3
"""
Generate Live Trading Admission Report (Task #118)
Reads shadow mode data and comparison reports, then generates GO/NO-GO decision.

Protocol: v4.3 (Zero-Trust Edition)
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from analytics.shadow_autopsy import ShadowAutopsy


def load_json_file(filepath: str) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"✅ Loaded: {filepath}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in {filepath}: {e}")
        sys.exit(1)


def main():
    """Main execution function."""
    logger.info("🔐 Shadow Autopsy Engine - Live Trading Admission Report Generator")
    logger.info("=" * 70)

    # Step 1: Load shadow mode records
    shadow_records_path = Path("data/outputs/audit/shadow_records.json")
    logger.info(f"📖 Loading shadow records from: {shadow_records_path}")

    if not shadow_records_path.exists():
        logger.error(f"❌ Shadow records not found: {shadow_records_path}")
        logger.info("   Hint: Task #117 should have generated this file")
        sys.exit(1)

    shadow_data = load_json_file(str(shadow_records_path))

    # Step 2: Load model comparison report
    comparison_report_path = Path(
        "docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json"
    )
    logger.info(f"📊 Loading comparison report from: {comparison_report_path}")

    if not comparison_report_path.exists():
        logger.error(f"❌ Comparison report not found: {comparison_report_path}")
        logger.info("   Hint: Task #117 should have generated this file")
        sys.exit(1)

    comparison_report = load_json_file(str(comparison_report_path))

    # Step 3: Create Shadow Autopsy instance
    logger.info("🔬 Initializing Shadow Autopsy Engine...")
    autopsy = ShadowAutopsy(shadow_data, comparison_report)

    # Step 4: Generate gatekeeping decision
    logger.info("🚦 Generating gatekeeping decision...")
    decision = autopsy.generate_gatekeeping_decision()

    logger.info("=" * 70)
    logger.info(f"📋 Decision: {'✅ GO' if decision.is_approved else '❌ NO-GO'}")
    logger.info(f"   Confidence: {decision.approval_confidence * 100:.1f}%")
    logger.info(f"   P99 Latency: {decision.p99_latency_ms:.2f}ms")
    logger.info(f"   Drift Events (24h): {decision.drift_events_24h}")
    logger.info(f"   Critical Errors: {decision.critical_errors}")

    if decision.rejection_reasons:
        logger.warning("⚠️ Rejection Reasons:")
        for reason in decision.rejection_reasons:
            logger.warning(f"   - {reason}")

    # Step 5: Generate markdown report
    logger.info("📝 Generating markdown admission report...")
    report = autopsy.generate_admission_report(decision)

    # Step 6: Write report to file
    output_dir = Path("docs/archive/tasks/TASK_118")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "LIVE_TRADING_ADMISSION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"✅ Report written to: {report_path}")

    # Step 7: Write decision metadata
    decision_metadata = {
        "timestamp": decision.timestamp,
        "decision": "GO" if decision.is_approved else "NO-GO",
        "approval_confidence": decision.approval_confidence,
        "critical_errors": decision.critical_errors,
        "p95_latency_ms": decision.p95_latency_ms,
        "p99_latency_ms": decision.p99_latency_ms,
        "drift_events_24h": decision.drift_events_24h,
        "pnl_net_return": decision.pnl_net_return,
        "diversity_index": decision.diversity_index,
        "rejection_reasons": decision.rejection_reasons,
        "decision_hash": decision.decision_hash
    }

    metadata_path = output_dir / "ADMISSION_DECISION_METADATA.json"
    with open(metadata_path, 'w') as f:
        json.dump(decision_metadata, f, indent=2)

    logger.info(f"✅ Metadata written to: {metadata_path}")

    logger.info("=" * 70)
    logger.info("🎯 Shadow Autopsy Analysis Complete")
    logger.info(f"   Final Decision: {'✅ GO FOR LIVE TRADING' if decision.is_approved else '❌ BLOCKED - DO NOT PROCEED'}")
    logger.info(f"   Hash: {decision.decision_hash}")

    # Return exit code based on decision
    return 0 if decision.is_approved else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

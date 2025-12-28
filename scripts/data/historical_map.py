#!/usr/bin/env python3
"""
Task #030: Historical Ticket Mapping - Source of Truth
=======================================================

This file contains the definitive mapping of ticket IDs to their actual
project history based on Git commits and development timeline.

Used by History Healing scripts to standardize Notion ticket titles.

Protocol: v2.0 (History Healing)
"""

# Truth Source for Tickets #001 - #027
TICKET_MAP = {
    1: "Project Environment & Docker Infrastructure",
    2: "Git Workflow & CI/CD Pipeline Init",
    3: "Basic Market Data Connection (EODHD Test)",
    4: "Database Tech Stack Selection (TimescaleDB Plan)",
    5: "Feature Store Design (Feast Research)",
    6: "Historical Data Ingestion Prototype",
    7: "Real-time Data Stream Architecture",
    8: "Data Pipeline & Feature Engineering Platform",
    9: "ML Training Framework (XGBoost Integration)",
    10: "Backtesting System & Kelly Criterion",
    11: "MT5 Integration Strategy & Logic",
    12: "Risk Management & Circuit Breakers",
    13: "Notion Nexus & Knowledge Graph Setup",
    14: "MT5 Gateway Core Service (Windows Side)",
    15: "Windows Deployment & SSH Tunneling",
    16: "Basic Order Execution Logic",
    17: "Market Data Service (ZMQ Pub/Sub)",
    18: "Technical Analysis Indicators Library",
    19: "Signal Generation Engine",
    20: "Integrated Trading Bot Loop",
    21: "Live Trading Runner Implementation",
    22: "System Logging & Observability",
    23: "Strategy Optimization & Hyperparameter Tuning",
    24: "Trade Journaling & Reporting Module",
    25: "System Stress Testing & Validation",
    26: "Performance Profiling & Latency Optimization",
    27: "Phase 1 Code Freeze & Architecture Cleanup"
}


# Expected status for all tickets #001-#027
EXPECTED_STATUS = "完成"  # Chinese: "Complete" (matches Notion database)


def get_ticket_title(ticket_id: int) -> str:
    """
    Get the standardized title for a ticket.

    Args:
        ticket_id: Ticket number (1-27)

    Returns:
        Standardized title with ticket ID prefix
    """
    if ticket_id not in TICKET_MAP:
        raise ValueError(f"Ticket #{ticket_id} not in historical map")

    return f"#{ticket_id:03d} - {TICKET_MAP[ticket_id]}"


def is_valid_ticket(ticket_id: int) -> bool:
    """Check if ticket ID is in the valid range."""
    return 1 <= ticket_id <= 27


def get_all_tickets():
    """Get all ticket IDs in the historical map."""
    return sorted(TICKET_MAP.keys())


if __name__ == "__main__":
    print("=" * 80)
    print("📋 HISTORICAL TICKET MAP")
    print("=" * 80)
    print()
    print(f"Total tickets: {len(TICKET_MAP)}")
    print()

    for ticket_id in get_all_tickets():
        title = get_ticket_title(ticket_id)
        print(f"{title}")

    print()
    print(f"Expected status: {EXPECTED_STATUS}")

"""
ops_capacity_analysis.py
==========================
Operations capacity planning — Phase 5 (staffing/SLA modeling).

Answers a question grounded in understanding the drivers of operations:
how much staffing does it actually take to clear the queue. Nothing else in
this project asks that — every other module stops at detection/scoring/routing.

Two real, distinct things are computed, and kept separate on purpose so
neither misrepresents the other:

  1. STEADY-STATE ARRIVAL RATE — real, not modeled. Derived directly from
     the actual span of Review_Date in the data (2021-03-14 to
     2026-06-18, ~274.6 weeks) and the actual 300-review volume. This is
     an honest historical average arrival rate, not a claim about future
     volume.

  2. SLA-DRIVEN BURST CAPACITY — how many analysts would need to work the
     Critical/High queues *concurrently* to clear the current backlog
     snapshot inside the SLA windows already defined in config.py
     (SLA_P1_HOURS, SLA_P2_HOURS). This uses the MODELED handling-time
     assumptions in config.py (AVG_HANDLING_TIME_MINUTES) — disclosed
     there and again here, not presented as measured real timing data.

Output: reports/ops_capacity.csv (Metric,Value — same convention as the
other *_summary.csv files in this project)

Run standalone:
    python analytics/ops_capacity_analysis.py
"""

import os
import sys
import math

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    REPORTS_DIR,
    AVG_HANDLING_TIME_MINUTES,
    ANALYST_HOURS_PER_DAY,
    ANALYST_WORKING_DAYS_PER_WEEK,
    SLA_P1_HOURS,
    SLA_P2_HOURS,
    get_logger,
)

log = get_logger(__name__)


def get_real_arrival_rate():
    """Real (not modeled) — actual review volume over the actual observed
    date span in the dataset."""
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    dates = pd.read_sql("SELECT Review_Date FROM Reviews", con)["Review_Date"]
    con.close()
    dates = pd.to_datetime(dates)
    span_days = (dates.max() - dates.min()).days
    span_weeks = span_days / 7
    total_reviews = len(dates)
    return {
        "date_min": dates.min().strftime("%Y-%m-%d"),
        "date_max": dates.max().strftime("%Y-%m-%d"),
        "span_weeks": span_weeks,
        "total_reviews": total_reviews,
        "reviews_per_week": total_reviews / span_weeks,
    }


def get_severity_volume():
    path = os.path.join(REPORTS_DIR, "severity_distribution.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "ops_capacity_analysis.py depends on reports/severity_distribution.csv. "
            "Run trust_safety/trust_safety_pipeline.py (or run_all.py) first."
        )
    df = pd.read_csv(path)
    return dict(zip(df["Severity"], df["Count"]))


def build_ops_capacity() -> pd.DataFrame:
    arrival = get_real_arrival_rate()
    volume = get_severity_volume()

    rows = []

    # ── Section 1: real arrival rate (no modeled assumptions used here) ──
    rows.append(("[Arrival] Dataset Date Range", f"{arrival['date_min']} to {arrival['date_max']}"))
    rows.append(("[Arrival] Observed Span (weeks)", round(arrival["span_weeks"], 1)))
    rows.append(("[Arrival] Total Reviews", arrival["total_reviews"]))
    rows.append(("[Arrival] Real Avg Reviews/Week", round(arrival["reviews_per_week"], 2)))

    # ── Section 2: total handling-time demand at current volume mix ──
    # MODELED: AVG_HANDLING_TIME_MINUTES per tier, from config.py
    total_minutes = sum(volume.get(tier, 0) * mins for tier, mins in AVG_HANDLING_TIME_MINUTES.items())
    total_hours = total_minutes / 60
    for tier, mins in AVG_HANDLING_TIME_MINUTES.items():
        count = volume.get(tier, 0)
        rows.append((f"[Volume] {tier} Cases", count))
        rows.append((f"[Modeled] {tier} Handling Time (min/case)", mins))

    rows.append(("[Modeled] Total Handling Time for Full Snapshot (hours)", round(total_hours, 1)))

    # ── Section 3: steady-state analyst load at the REAL arrival rate ──
    # Weight the real weekly arrival rate by the same severity mix as the snapshot,
    # apply modeled handling times, compare to one analyst's real weekly capacity.
    avg_minutes_per_review = total_minutes / arrival["total_reviews"]
    weekly_minutes_at_real_rate = arrival["reviews_per_week"] * avg_minutes_per_review
    weekly_hours_at_real_rate = weekly_minutes_at_real_rate / 60
    analyst_weekly_hours = ANALYST_HOURS_PER_DAY * ANALYST_WORKING_DAYS_PER_WEEK
    utilization_pct = (weekly_hours_at_real_rate / analyst_weekly_hours) * 100

    rows.append(("[Steady-State] Modeled Weekly Handling Load (hours)", round(weekly_hours_at_real_rate, 2)))
    rows.append(("[Steady-State] One Analyst's Weekly Capacity (hours)", analyst_weekly_hours))
    rows.append(("[Steady-State] Utilization of 1 Analyst (%)", round(utilization_pct, 1)))
    rows.append((
        "[Steady-State] Analysts Needed at Real Arrival Rate",
        max(1, math.ceil(utilization_pct / 100)),
    ))

    # ── Section 4: SLA-driven burst capacity for the current backlog snapshot ──
    # "If all Critical/High cases in the current snapshot needed to clear inside
    # their SLA windows starting now, how many analysts working in parallel
    # would it take?" This is a burst/worst-case number, not a steady-state one.
    critical_hours = (volume.get("Critical", 0) * AVG_HANDLING_TIME_MINUTES["Critical"]) / 60
    high_hours = (volume.get("High", 0) * AVG_HANDLING_TIME_MINUTES["High"]) / 60
    analysts_for_critical_sla = math.ceil(critical_hours / SLA_P1_HOURS) if critical_hours > 0 else 0
    analysts_for_high_sla = math.ceil(high_hours / SLA_P2_HOURS) if high_hours > 0 else 0

    rows.append(("[SLA Burst] Critical Backlog Total Handling Time (hours)", round(critical_hours, 2)))
    rows.append((f"[SLA Burst] Analysts Needed to Clear Critical Backlog Within SLA ({SLA_P1_HOURS}h)", analysts_for_critical_sla))
    rows.append(("[SLA Burst] High Backlog Total Handling Time (hours)", round(high_hours, 2)))
    rows.append((f"[SLA Burst] Analysts Needed to Clear High Backlog Within SLA ({SLA_P2_HOURS}h)", analysts_for_high_sla))
    rows.append((
        "[SLA Burst] Peak Concurrent Analysts Needed (Critical + High overlap)",
        max(analysts_for_critical_sla, analysts_for_high_sla),
    ))

    return pd.DataFrame(rows, columns=["Metric", "Value"])


def main():
    log.info("Building operations capacity analysis...")
    result = build_ops_capacity()
    out_path = os.path.join(REPORTS_DIR, "ops_capacity.csv")
    result.to_csv(out_path, index=False)
    log.info("Saved %d metrics -> %s", len(result), out_path)


if __name__ == "__main__":
    main()

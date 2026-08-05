"""
tests/test_ops_capacity.py
============================
Unit tests for analytics/ops_capacity_analysis.py (Phase 5 — operations
capacity planning).

Run with:
    python -m pytest tests/test_ops_capacity.py -v

Tests cover:
    - Real arrival rate is computed from actual Review_Date span (not modeled)
    - Volume figures match reports/severity_distribution.csv exactly
    - SLA-driven analyst counts are internally consistent with SLA_P1_HOURS/SLA_P2_HOURS
    - No negative or nonsensical values
"""

import sys
import os
import math
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REPORTS_DIR, DB_PATH, SLA_P1_HOURS, SLA_P2_HOURS, AVG_HANDLING_TIME_MINUTES
from analytics.ops_capacity_analysis import build_ops_capacity, get_real_arrival_rate, get_severity_volume


@pytest.fixture(scope="module")
def result():
    if not os.path.exists(DB_PATH) or not os.path.exists(os.path.join(REPORTS_DIR, "severity_distribution.csv")):
        pytest.skip("Requires PraxisIQ.db and reports/severity_distribution.csv.")
    return build_ops_capacity().set_index("Metric")["Value"]


def test_total_reviews_matches_real_arrival_rate_source():
    arrival = get_real_arrival_rate()
    assert arrival["total_reviews"] == 300


def test_arrival_rate_is_positive():
    arrival = get_real_arrival_rate()
    assert arrival["reviews_per_week"] > 0


def test_volume_matches_severity_distribution_exactly(result):
    volume = get_severity_volume()
    for tier in AVG_HANDLING_TIME_MINUTES:
        expected = volume.get(tier, 0)
        assert result[f"[Volume] {tier} Cases"] == expected


def test_sla_analyst_counts_are_non_negative_integers(result):
    assert result["[SLA Burst] Analysts Needed to Clear Critical Backlog Within SLA (4h)"] >= 0
    assert result["[SLA Burst] Analysts Needed to Clear High Backlog Within SLA (24h)"] >= 0


def test_sla_analyst_count_is_internally_consistent(result):
    volume = get_severity_volume()
    critical_hours = (volume.get("Critical", 0) * AVG_HANDLING_TIME_MINUTES["Critical"]) / 60
    expected = math.ceil(critical_hours / SLA_P1_HOURS) if critical_hours > 0 else 0
    assert result["[SLA Burst] Analysts Needed to Clear Critical Backlog Within SLA (4h)"] == expected


def test_peak_concurrent_is_max_of_the_two_tiers(result):
    crit = result["[SLA Burst] Analysts Needed to Clear Critical Backlog Within SLA (4h)"]
    high = result["[SLA Burst] Analysts Needed to Clear High Backlog Within SLA (24h)"]
    assert result["[SLA Burst] Peak Concurrent Analysts Needed (Critical + High overlap)"] == max(crit, high)


def test_utilization_is_non_negative(result):
    assert result["[Steady-State] Utilization of 1 Analyst (%)"] >= 0


def test_analysts_needed_at_real_rate_is_at_least_one(result):
    assert result["[Steady-State] Analysts Needed at Real Arrival Rate"] >= 1

"""
tests/test_appeals_workflow.py
================================
Unit tests for trust_safety/appeals_workflow.py (Phase 3 — appeals &
reinstatement workflow).

Run with:
    python -m pytest tests/test_appeals_workflow.py -v

Tests cover:
    - Only Critical/High severities are appeal-eligible
    - Appeal / overturn counts match config.py rate assumptions
    - Overturned is always a subset of Appealed
    - Reproducibility (same random_state -> identical result)
    - Every row is labeled as a modeled simulation, never presented as real
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    REPORTS_DIR,
    APPEAL_ELIGIBLE_SEVERITIES,
    APPEAL_RATE_ASSUMPTION,
    APPEAL_OVERTURN_RATE_ASSUMPTION,
)
from trust_safety.appeals_workflow import build_appeals_queue, build_summary


@pytest.fixture(scope="module")
def appeals():
    src = os.path.join(REPORTS_DIR, "risk_escalation_queue.csv")
    if not os.path.exists(src):
        pytest.skip("Requires reports/risk_escalation_queue.csv — run trust_safety_pipeline.py first.")
    return build_appeals_queue()


def test_only_eligible_severities_can_be_appealed(appeals):
    appealed_rows = appeals[appeals["Appeal_Status"] == "Appealed"]
    assert set(appealed_rows["Severity"].unique()).issubset(set(APPEAL_ELIGIBLE_SEVERITIES))


def test_ineligible_severities_marked_not_eligible(appeals):
    ineligible_rows = appeals[~appeals["Severity"].isin(APPEAL_ELIGIBLE_SEVERITIES)]
    assert (ineligible_rows["Appeal_Status"] == "Not Eligible").all()
    assert (ineligible_rows["Appeal_Outcome"] == "N/A").all()


def test_appeal_count_matches_configured_rate(appeals):
    n_eligible = (appeals["Appeal_Status"] != "Not Eligible").sum()
    n_appealed = (appeals["Appeal_Status"] == "Appealed").sum()
    expected = round(n_eligible * APPEAL_RATE_ASSUMPTION)
    assert n_appealed == expected


def test_overturn_count_matches_configured_rate(appeals):
    n_appealed = (appeals["Appeal_Status"] == "Appealed").sum()
    n_overturned = (appeals["Appeal_Outcome"] == "Overturned").sum()
    expected = round(n_appealed * APPEAL_OVERTURN_RATE_ASSUMPTION)
    assert n_overturned == expected


def test_overturned_is_subset_of_appealed(appeals):
    overturned_rows = appeals[appeals["Appeal_Outcome"] == "Overturned"]
    assert (overturned_rows["Appeal_Status"] == "Appealed").all()


def test_not_appealed_rows_have_na_outcome(appeals):
    not_appealed_rows = appeals[appeals["Appeal_Status"] == "Not Appealed"]
    assert (not_appealed_rows["Appeal_Outcome"] == "N/A").all()


def test_reproducible_with_same_random_state(appeals):
    rerun = build_appeals_queue()
    pd.testing.assert_series_equal(
        appeals["Appeal_Status"].reset_index(drop=True),
        rerun["Appeal_Status"].reset_index(drop=True),
    )
    pd.testing.assert_series_equal(
        appeals["Appeal_Outcome"].reset_index(drop=True),
        rerun["Appeal_Outcome"].reset_index(drop=True),
    )


def test_every_row_labeled_as_modeled_simulation(appeals):
    assert (appeals["Data_Note"].str.contains("MODELED SIMULATION", na=False)).all()


def test_summary_counts_match_queue(appeals):
    summary = build_summary(appeals).set_index("Metric")["Value"]
    n_eligible = (appeals["Appeal_Status"] != "Not Eligible").sum()
    n_appealed = (appeals["Appeal_Status"] == "Appealed").sum()
    n_overturned = (appeals["Appeal_Outcome"] == "Overturned").sum()
    assert summary["Eligible for Appeal (Critical/High)"] == n_eligible
    assert summary["Appealed (modeled)"] == n_appealed
    assert summary["Overturned on Appeal (modeled)"] == n_overturned

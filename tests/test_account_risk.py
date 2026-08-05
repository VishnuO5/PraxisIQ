"""
tests/test_account_risk.py
===========================
Unit tests for analytics/account_risk_scoring.py (Phase 2 — account-level
enforcement scoring).

Run with:
    python -m pytest tests/test_account_risk.py -v

Tests cover:
    - _action_for_score threshold boundaries (None / Warning / Restricted / Suspended)
    - build_account_risk_scores runs end-to-end against real report data
    - Output schema and value sanity
    - No single weak signal alone crosses the Warning threshold (regression
      guard for the burst-day-overlap-only bug found and fixed during Phase 2)
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ACCOUNT_STRIKE_THRESHOLDS, ACCOUNT_RISK_WEIGHTS, REPORTS_DIR
from analytics.account_risk_scoring import _action_for_score, build_account_risk_scores


# ── Threshold boundary tests ───────────────────────────────────────────────

def test_action_below_warning_is_none():
    assert _action_for_score(ACCOUNT_STRIKE_THRESHOLDS["Warning"] - 0.01) == "None"


def test_action_at_warning_boundary():
    assert _action_for_score(ACCOUNT_STRIKE_THRESHOLDS["Warning"]) == "Warning"


def test_action_at_restricted_boundary():
    assert _action_for_score(ACCOUNT_STRIKE_THRESHOLDS["Restricted"]) == "Restricted"


def test_action_at_suspended_boundary():
    assert _action_for_score(ACCOUNT_STRIKE_THRESHOLDS["Suspended"]) == "Suspended"


def test_action_zero_score_is_none():
    assert _action_for_score(0.0) == "None"


# ── Regression guard: no single weak signal should trigger an action alone ──

def test_no_single_weight_alone_crosses_warning():
    """
    Phase 2 build originally weighted burst_day_overlap at 2.5, which alone
    crossed the Warning threshold (2.0) for any account that merely posted
    on a high-volume day — flagging 63% of all accounts as noise. Weights
    were rebalanced so each individual flag, alone, stays below Warning.
    This test locks that guarantee in.
    """
    warning_threshold = ACCOUNT_STRIKE_THRESHOLDS["Warning"]
    for signal, weight in ACCOUNT_RISK_WEIGHTS.items():
        assert weight < warning_threshold, (
            f"'{signal}' weight ({weight}) alone reaches or exceeds the Warning "
            f"threshold ({warning_threshold}) — a single weak signal should never "
            f"be sufficient on its own to trigger enforcement."
        )


# ── End-to-end test against real report data ────────────────────────────────

@pytest.fixture(scope="module")
def account_scores():
    suspicious_exists = os.path.exists(os.path.join(REPORTS_DIR, "suspicious_reviewer_detection.csv"))
    burst_exists = os.path.exists(os.path.join(REPORTS_DIR, "review_burst_detection.csv"))
    if not (suspicious_exists and burst_exists):
        pytest.skip("Requires reports/suspicious_reviewer_detection.csv and "
                    "reports/review_burst_detection.csv — run run_all.py first.")
    return build_account_risk_scores()


def test_output_has_expected_columns(account_scores):
    expected = {
        "Reviewer_Name", "Review_Count", "Avg_Rating", "Flag_Low_Avg_Rating",
        "Flag_No_Variance", "Burst_Day_Overlap", "Account_Risk_Score",
        "Enforcement_Action", "Action_Description",
    }
    assert expected.issubset(set(account_scores.columns))


def test_one_row_per_reviewer(account_scores):
    assert account_scores["Reviewer_Name"].is_unique


def test_all_actions_are_valid_tiers(account_scores):
    valid = {"None", "Warning", "Restricted", "Suspended"}
    assert set(account_scores["Enforcement_Action"].unique()).issubset(valid)


def test_scores_are_non_negative(account_scores):
    assert (account_scores["Account_Risk_Score"] >= 0).all()


def test_sorted_descending_by_risk_score(account_scores):
    scores = account_scores["Account_Risk_Score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_higher_action_tiers_have_higher_or_equal_scores(account_scores):
    """Suspended accounts should never score lower than Restricted, which
    should never score lower than Warning, which should never score lower
    than None — the ladder must be internally consistent."""
    tier_order = ["None", "Warning", "Restricted", "Suspended"]
    present = [t for t in tier_order if t in account_scores["Enforcement_Action"].unique()]
    avg_by_tier = account_scores.groupby("Enforcement_Action")["Account_Risk_Score"].mean()
    for lower, higher in zip(present, present[1:]):
        assert avg_by_tier[lower] <= avg_by_tier[higher]

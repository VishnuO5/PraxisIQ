"""
tests/test_risk_service.py
============================
Unit tests for api/risk_service.py (Phase 7 — real-time risk scoring
service).

Run with:
    python -m pytest tests/test_risk_service.py -v

Tests cover:
    - assign_severity produces the same output as the batch pipeline's
      rules for every real Label/Rating combination in the actual dataset
      (drift guard — the whole point of "same logic, different interface"
      breaks silently if these two implementations ever diverge)
    - FastAPI endpoint behavior via TestClient (real HTTP, not just
      function calls)
    - Invalid input handling (bad label, bad date, out-of-range rating)
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH, PRIORITY_MAP, TIER_MAP
from api.risk_service import app, assign_severity, ReviewInput, score_review

try:
    from fastapi.testclient import TestClient
    client = TestClient(app)
except ImportError:
    client = None


# ── Drift guard: risk_service's assign_severity must match the batch
#    pipeline's assign_severity for every real review in the dataset ──

def _batch_assign_severity(label, rating):
    """Copied verbatim from trust_safety/trust_safety_pipeline.py so this
    test has no import-time side effects (that module runs a full pipeline
    on import). If the batch pipeline's rules ever change, this copy must
    be updated too — that's the point: a diff here is a deliberate,
    visible signal, not silent drift."""
    if label == "Treatment" and rating <= 2:
        return "Critical"
    elif label in ["Communication", "Pricing", "Waiting Time", "Staff"] and rating <= 2:
        return "High"
    elif label == "Treatment" and rating == 3:
        return "High"
    elif label in ["Communication", "Staff"] and rating == 3:
        return "Medium"
    elif label == "Neutral":
        return "Low"
    elif label == "Positive":
        return "Safe"
    else:
        return "Medium"


@pytest.fixture(scope="module")
def real_reviews():
    if not os.path.exists(DB_PATH):
        pytest.skip("Requires PraxisIQ.db — run create_database.py first.")
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT Label, Rating FROM Reviews", con)
    con.close()
    return df


def test_severity_matches_batch_pipeline_for_all_real_reviews(real_reviews):
    mismatches = []
    for _, row in real_reviews.iterrows():
        service_result = assign_severity(row["Label"], row["Rating"])
        batch_result = _batch_assign_severity(row["Label"], row["Rating"])
        if service_result != batch_result:
            mismatches.append((row["Label"], row["Rating"], service_result, batch_result))
    assert not mismatches, f"risk_service and batch pipeline disagree on: {mismatches}"


# ── Direct function tests ────────────────────────────────────────────────

def test_critical_severity_treatment_low_rating():
    assert assign_severity("Treatment", 1) == "Critical"
    assert assign_severity("Treatment", 2) == "Critical"


def test_safe_severity_positive():
    assert assign_severity("Positive", 5) == "Safe"


def test_priority_and_tier_maps_are_consistent():
    for severity in ["Critical", "High", "Medium", "Low", "Safe"]:
        assert severity in PRIORITY_MAP
        assert severity in TIER_MAP


def test_score_review_function_end_to_end():
    review = ReviewInput(
        review_text="Filling was painful",
        rating=1,
        reviewer_name="Nonexistent Test Reviewer ZZZ",
        review_date="2026-08-01",
        label="Treatment",
    )
    result = score_review(review)
    assert result.severity == "Critical"
    assert result.risk_score > 0
    assert result.repeat_low_rater is False  # reviewer doesn't exist in DB


# ── HTTP-level tests via FastAPI TestClient ─────────────────────────────

@pytest.mark.skipif(client is None, reason="fastapi.testclient not available")
def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.skipif(client is None, reason="fastapi.testclient not available")
def test_score_review_endpoint_valid_request():
    resp = client.post("/score_review", json={
        "review_text": "Great service",
        "rating": 5,
        "reviewer_name": "Test Happy Patient",
        "review_date": "2020-01-01",
        "label": "Positive",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"] == "Safe"
    assert body["sla_hours"] is None


@pytest.mark.skipif(client is None, reason="fastapi.testclient not available")
def test_score_review_endpoint_invalid_label():
    resp = client.post("/score_review", json={
        "review_text": "x",
        "rating": 3,
        "reviewer_name": "Test",
        "review_date": "2026-01-01",
        "label": "NotARealLabel",
    })
    assert resp.status_code == 422


@pytest.mark.skipif(client is None, reason="fastapi.testclient not available")
def test_score_review_endpoint_invalid_rating():
    resp = client.post("/score_review", json={
        "review_text": "x",
        "rating": 9,
        "reviewer_name": "Test",
        "review_date": "2026-01-01",
        "label": "Positive",
    })
    assert resp.status_code == 422


@pytest.mark.skipif(client is None, reason="fastapi.testclient not available")
def test_score_review_endpoint_invalid_date():
    resp = client.post("/score_review", json={
        "review_text": "x",
        "rating": 3,
        "reviewer_name": "Test",
        "review_date": "not-a-date",
        "label": "Neutral",
    })
    assert resp.status_code == 422

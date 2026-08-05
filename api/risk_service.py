"""
risk_service.py
================
Real-time risk scoring service — Phase 7 (batch-to-streaming alignment).

Every scoring pipeline in this project (trust_safety_pipeline.py,
account_risk_scoring.py, ops_capacity_analysis.py) runs as a batch job
against the whole Reviews table at once. This service wraps the same
severity/scoring logic as a callable HTTP endpoint — one review in,
one scored result out — which is the concrete first step toward the
batch-to-streaming shift this project's README already names as a
platform-scale requirement.

IMPORTANT — what this does and doesn't do:
  - assign_severity() and the Risk_Score formula below are an intentional
    mirror of trust_safety/trust_safety_pipeline.py's logic, using the
    exact same config.py constants (RISK_MAP, CATEGORY_WEIGHT,
    RECENCY_WINDOW_DAYS, RECENCY_MULTIPLIER, REPEAT_LOW_RATER_BONUS,
    PRIORITY_MAP, TIER_MAP). tests/test_risk_service.py locks the two
    implementations together — it fails if they ever drift apart.
  - This endpoint does NOT classify raw review text into a Label
    (Treatment/Communication/Pricing/etc.) — that's the ML/LLM
    classification stage (ml/review_classifier_v2.py,
    llm/llm_evaluation_final.py), a separate concern from severity
    scoring. This service picks up downstream of classification: it
    expects `label` as an input field, the same way the batch pipeline
    expects a `Label` column already present in the Reviews table.
  - Repeat_Low_Rater lookup queries the real PraxisIQ.db for the
    reviewer's actual prior review history — not simulated.

Run standalone:
    uvicorn api.risk_service:app --reload --host 127.0.0.1 --port 8000

Example request:
    curl -X POST http://127.0.0.1:8000/score_review \
      -H "Content-Type: application/json" \
      -d '{"review_text": "Filling was painful", "rating": 1, "reviewer_name": "Jane D", "review_date": "2026-08-01", "label": "Treatment"}'
"""

import os
import sys
import sqlite3
from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    RISK_MAP,
    CATEGORY_WEIGHT,
    RECENCY_WINDOW_DAYS,
    RECENCY_MULTIPLIER,
    REPEAT_LOW_RATER_BONUS,
    PRIORITY_MAP,
    TIER_MAP,
    SLA_P1_HOURS,
    SLA_P2_HOURS,
    RISK_SERVICE_HOST,
    RISK_SERVICE_PORT,
    RISK_SERVICE_VERSION,
    get_logger,
)

log = get_logger(__name__)

VALID_LABELS = list(CATEGORY_WEIGHT.keys())

app = FastAPI(
    title="PraxisIQ Risk Scoring Service",
    version=RISK_SERVICE_VERSION,
    description=(
        "Real-time per-review severity/priority scoring — mirrors "
        "trust_safety_pipeline.py's batch logic as a callable endpoint."
    ),
)


class ReviewInput(BaseModel):
    review_text: str = Field(..., min_length=1, description="Raw review text (not re-classified here)")
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    reviewer_name: str = Field(..., min_length=1)
    review_date: str = Field(..., description="YYYY-MM-DD")
    label: str = Field(..., description=f"One of: {', '.join(VALID_LABELS)}")


class ScoreOutput(BaseModel):
    severity: str
    priority: str
    moderation_tier: str
    risk_level: str
    risk_score: float
    repeat_low_rater: bool
    recency_multiplier_applied: bool
    sla_hours: float | None


def assign_severity(label: str, rating: int) -> str:
    """Exact mirror of trust_safety_pipeline.py's assign_severity(). Any
    change here must be made there too — tests/test_risk_service.py
    checks both against real historical reviews to catch drift."""
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


def get_repeat_low_rater(reviewer_name: str) -> bool:
    """Real lookup against PraxisIQ.db — same rule as the batch pipeline:
    more than 1 prior review AND historical avg rating < 3.0."""
    if not os.path.exists(DB_PATH):
        return False
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT Rating FROM Reviews WHERE Reviewer_Name = ?", con, params=(reviewer_name,)
    )
    con.close()
    if len(df) <= 1:
        return False
    return bool(df["Rating"].mean() < 3.0)


def score_review(review: ReviewInput) -> ScoreOutput:
    if review.label not in VALID_LABELS:
        raise HTTPException(status_code=422, detail=f"label must be one of {VALID_LABELS}")

    severity = assign_severity(review.label, review.rating)
    priority = PRIORITY_MAP.get(severity, "Unassigned")
    tier = TIER_MAP.get(severity, "Unassigned")
    risk_level = RISK_MAP.get(review.label, "Needs Review")

    try:
        review_date = datetime.strptime(review.review_date, "%Y-%m-%d")
        recency_applied = (datetime.now() - review_date).days <= RECENCY_WINDOW_DAYS
    except ValueError:
        raise HTTPException(status_code=422, detail="review_date must be YYYY-MM-DD")

    recency_multiplier = RECENCY_MULTIPLIER if recency_applied else 1.0
    repeat_low_rater = get_repeat_low_rater(review.reviewer_name)
    category_weight = CATEGORY_WEIGHT.get(review.label, 0)

    risk_score = round(
        category_weight
        * (6 - review.rating)
        * recency_multiplier
        * (1 + REPEAT_LOW_RATER_BONUS * int(repeat_low_rater)),
        2,
    )

    sla_hours = None
    if severity == "Critical":
        sla_hours = SLA_P1_HOURS
    elif severity == "High":
        sla_hours = SLA_P2_HOURS

    return ScoreOutput(
        severity=severity,
        priority=priority,
        moderation_tier=tier,
        risk_level=risk_level,
        risk_score=risk_score,
        repeat_low_rater=repeat_low_rater,
        recency_multiplier_applied=recency_applied,
        sla_hours=sla_hours,
    )


@app.get("/health")
def health():
    return {"status": "ok", "version": RISK_SERVICE_VERSION, "db_connected": os.path.exists(DB_PATH)}


@app.post("/score_review", response_model=ScoreOutput)
def score_review_endpoint(review: ReviewInput):
    log.info("Scoring review from %s (label=%s, rating=%d)", review.reviewer_name, review.label, review.rating)
    return score_review(review)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=RISK_SERVICE_HOST, port=RISK_SERVICE_PORT)

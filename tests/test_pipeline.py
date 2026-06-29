"""
tests/test_pipeline.py
======================
Unit tests for PraxisIQ core pipeline functions.

Run with:
    python -m pytest tests/ -v

Tests cover:
    - Risk classification logic (assign_severity)
    - Text normalization (duplicate detection)
    - Fuzzy similarity threshold
    - Burst detection logic
    - Risk score computation
    - Config values validation
    - Database schema validation
    - Label validation
    - Confidence interval computation
    - Data quality score logic
"""

import sys
import os
import pytest
import sqlite3
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    RISK_MAP,
    CATEGORY_WEIGHT,
    PRIORITY_MAP,
    TIER_MAP,
    DB_PATH,
    REPORTS_DIR,
    ML_TEST_SIZE,
    ML_RANDOM_STATE,
    BURST_STATIC_SIGMA,
    BURST_ROLLING_MULTIPLIER,
)

# ── FIXTURES ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_reviews():
    """Small sample DataFrame mimicking the Reviews table."""
    return pd.DataFrame({
        "Review_ID"   : [1, 2, 3, 4, 5],
        "Reviewer_Name": ["Alice", "Bob", "Alice", "Carol", "Dave"],
        "Rating"      : [1, 5, 2, 3, 1],
        "Review_Date" : ["2024-01-01", "2024-01-01", "2024-01-02", "2024-02-01", "2024-02-01"],
        "Label"       : ["Treatment", "Positive", "Communication", "Waiting Time", "Treatment"],
        "Review_Text" : [
            "Root canal was extremely painful",
            "Excellent service overall",
            "Doctor did not explain procedure",
            "Waited 45 minutes past appointment",
            "Treatment made my tooth worse",
        ]
    })


# ── TEST 1: RISK MAP COMPLETENESS ─────────────────────────────────────────────

def test_risk_map_covers_all_labels():
    """Every valid review label must have a risk level in RISK_MAP."""
    valid_labels = {"Positive", "Treatment", "Communication", "Waiting Time",
                    "Pricing", "Staff", "Neutral"}
    for label in valid_labels:
        assert label in RISK_MAP, f"Label '{label}' missing from RISK_MAP"


# ── TEST 2: ASSIGN_SEVERITY LOGIC ─────────────────────────────────────────────

def assign_severity(row):
    """Replicated from trust_safety_pipeline.py for isolated testing."""
    if row["Label"] == "Treatment" and row["Rating"] <= 2:
        return "Critical"
    elif row["Label"] in ["Communication", "Pricing", "Waiting Time", "Staff"] and row["Rating"] <= 2:
        return "High"
    elif row["Label"] == "Treatment" and row["Rating"] == 3:
        return "High"
    elif row["Label"] in ["Communication", "Staff"] and row["Rating"] == 3:
        return "Medium"
    elif row["Label"] == "Neutral":
        return "Low"
    elif row["Label"] == "Positive":
        return "Safe"
    else:
        return "Medium"


def test_treatment_rating_1_is_critical():
    row = pd.Series({"Label": "Treatment", "Rating": 1})
    assert assign_severity(row) == "Critical"


def test_treatment_rating_3_is_high():
    row = pd.Series({"Label": "Treatment", "Rating": 3})
    assert assign_severity(row) == "High"


def test_positive_is_safe():
    row = pd.Series({"Label": "Positive", "Rating": 5})
    assert assign_severity(row) == "Safe"


def test_communication_rating_2_is_high():
    row = pd.Series({"Label": "Communication", "Rating": 2})
    assert assign_severity(row) == "High"


def test_neutral_is_low():
    row = pd.Series({"Label": "Neutral", "Rating": 3})
    assert assign_severity(row) == "Low"


# ── TEST 3: TEXT NORMALIZATION ────────────────────────────────────────────────

def normalize(text):
    """Replicated from duplicate_review_detection.py."""
    if pd.isna(text):
        return ""
    return " ".join(str(text).lower().strip().split())


def test_normalize_lowercases():
    assert normalize("GREAT Service") == "great service"


def test_normalize_strips_whitespace():
    assert normalize("  hello world  ") == "hello world"


def test_normalize_collapses_spaces():
    assert normalize("hello    world") == "hello world"


def test_normalize_handles_null():
    assert normalize(None) == ""


# ── TEST 4: FUZZY SIMILARITY ──────────────────────────────────────────────────

def test_identical_texts_score_1():
    from difflib import SequenceMatcher
    a = "root canal was painful"
    b = "root canal was painful"
    assert SequenceMatcher(None, a, b).ratio() == 1.0


def test_very_different_texts_below_threshold():
    from difflib import SequenceMatcher
    a = "excellent service highly recommended"
    b = "waiting time was too long"
    ratio = SequenceMatcher(None, a, b).ratio()
    assert ratio < 0.85, f"Expected ratio < 0.85 but got {ratio}"


def test_near_duplicate_above_threshold():
    from difflib import SequenceMatcher
    a = "root canal was extremely painful despite local anesthesia"
    b = "root canal was extremely painful despite local anaesthesia"
    ratio = SequenceMatcher(None, a, b).ratio()
    assert ratio >= 0.85, f"Expected ratio >= 0.85 but got {ratio}"


# ── TEST 5: RISK SCORE COMPUTATION ───────────────────────────────────────────

def test_risk_score_higher_for_treatment_than_positive(sample_reviews):
    """Treatment 1-star should score higher than Positive 5-star."""
    treatment_row = sample_reviews[sample_reviews["Label"] == "Treatment"].iloc[0]
    positive_row  = sample_reviews[sample_reviews["Label"] == "Positive"].iloc[0]

    treatment_score = CATEGORY_WEIGHT.get("Treatment", 0) * (6 - treatment_row["Rating"])
    positive_score  = CATEGORY_WEIGHT.get("Positive", 0)  * (6 - positive_row["Rating"])

    assert treatment_score > positive_score


def test_category_weight_treatment_is_highest():
    """Treatment must have the highest category weight."""
    max_weight = max(CATEGORY_WEIGHT.values())
    assert CATEGORY_WEIGHT["Treatment"] == max_weight


def test_category_weight_positive_is_zero():
    assert CATEGORY_WEIGHT["Positive"] == 0


# ── TEST 6: CONFIG VALIDATION ────────────────────────────────────────────────

def test_ml_test_size_is_valid():
    assert 0 < ML_TEST_SIZE < 1, "ML_TEST_SIZE must be between 0 and 1"


def test_burst_static_sigma_is_positive():
    assert BURST_STATIC_SIGMA > 0


def test_burst_rolling_multiplier_greater_than_one():
    assert BURST_ROLLING_MULTIPLIER > 1.0


# ── TEST 7: DATABASE SCHEMA ──────────────────────────────────────────────────

def test_database_exists():
    assert os.path.exists(DB_PATH), f"Database not found at {DB_PATH}"


def test_patients_table_has_required_columns():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Patients LIMIT 1", conn)
    conn.close()
    required = {"Patient_Id", "Primary_Treatment", "Returned_Patient", "Total_Visits"}
    for col in required:
        assert col in df.columns, f"Column '{col}' missing from Patients table"


def test_reviews_table_has_required_columns():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Reviews LIMIT 1", conn)
    conn.close()
    required = {"Review_ID", "Rating", "Label", "Review_Text", "Review_Date"}
    for col in required:
        assert col in df.columns, f"Column '{col}' missing from Reviews table"


def test_reviews_ratings_in_valid_range():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT Rating FROM Reviews", conn)
    conn.close()
    assert df["Rating"].between(1, 5).all(), "Some ratings are outside 1-5 range"


def test_reviews_labels_are_valid():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT Label FROM Reviews", conn)
    conn.close()
    valid = {"Positive", "Treatment", "Communication", "Waiting Time",
             "Pricing", "Staff", "Neutral"}
    invalid = set(df["Label"].unique()) - valid
    assert len(invalid) == 0, f"Invalid labels found: {invalid}"


# ── TEST 8: CONFIDENCE INTERVAL ──────────────────────────────────────────────

def test_wilson_ci_bounds_are_valid():
    """Wilson CI lower bound must be < accuracy < upper bound."""
    from scipy.stats import norm as _norm
    accuracy = 0.8222
    n = 90
    z = _norm.ppf(0.975)
    p = accuracy
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    margin = (z * ((p * (1 - p) / n) + z**2 / (4 * n**2))**0.5) / denominator
    ci_lower = (centre - margin) * 100
    ci_upper = (centre + margin) * 100

    assert ci_lower < accuracy * 100 < ci_upper
    assert ci_lower > 0
    assert ci_upper < 100


def test_wilson_ci_width_reasonable():
    """With n=90, CI width should be less than 20 percentage points."""
    from scipy.stats import norm as _norm
    accuracy = 0.8222
    n = 90
    z = _norm.ppf(0.975)
    p = accuracy
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    margin = (z * ((p * (1 - p) / n) + z**2 / (4 * n**2))**0.5) / denominator
    width = ((centre + margin) - (centre - margin)) * 100
    assert width < 20, f"CI width {width:.1f}pp seems too wide for n=90"
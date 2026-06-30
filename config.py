"""
config.py
=========
Central configuration for PraxisIQ.

All thresholds, weights, model parameters, paths, and logging setup
are defined here. Import this module in any script instead of
hardcoding values inline.

Usage:
    from config import BURST_STATIC_SIGMA, CATEGORY_WEIGHT, ML_TEST_SIZE
    from config import get_logger
    log = get_logger(__name__)
    log.info("Pipeline started")
"""

import os
import logging
import logging.handlers

# ── PATHS ─────────────────────────────────────────────────────────────────────

ROOT        = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(ROOT, "PraxisIQ.db")
REPORTS_DIR = os.path.join(ROOT, "reports")
EXCEL_PATH  = os.path.join(ROOT, "sample_data_synthetic.xlsx")


# ── LOGGING ───────────────────────────────────────────────────────────────────

LOG_DIR        = os.path.join(ROOT, "logs")
LOG_FILE       = os.path.join(LOG_DIR, "praxisiq.log")
LOG_LEVEL      = logging.INFO
LOG_FORMAT     = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger writing to console + logs/praxisiq.log.

    Usage in any script:
        from config import get_logger
        log = get_logger(__name__)
        log.info("Started")
        log.warning("Something unexpected")
        log.error("Something failed")
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers on re-import
    logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console = logging.StreamHandler()
    console.setLevel(LOG_LEVEL)
    console.setFormatter(formatter)
    logger.addHandler(console)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

# ── BURST DETECTION ───────────────────────────────────────────────────────────

# Method 1 — Static threshold: flag days where count > mean + N * std
BURST_STATIC_SIGMA      = 2        # number of standard deviations above mean

# Method 2 — Rolling window: flag days where count > multiplier * rolling avg
BURST_ROLLING_WINDOW    = 7        # days in rolling average window
BURST_ROLLING_MULTIPLIER = 2.0     # how many times the rolling avg to flag

# ── RISK CLASSIFICATION ───────────────────────────────────────────────────────

# Maps review label → risk tier used throughout the pipeline and dashboard
RISK_MAP = {
    "Treatment":     "High Risk",
    "Communication": "Needs Review",
    "Waiting Time":  "Needs Review",
    "Pricing":       "Needs Review",
    "Staff":         "Needs Review",
    "Neutral":       "Safe",
    "Positive":      "Safe",
}

# ── COMPOSITE RISK SCORING ────────────────────────────────────────────────────

# Weight assigned to each category in the composite risk score formula:
#   Risk_Score = Category_Weight * (6 - Rating) * Recency_Multiplier * Repeat_Factor
CATEGORY_WEIGHT = {
    "Treatment":     5,
    "Communication": 4,
    "Staff":         3,
    "Waiting Time":  2,
    "Pricing":       2,
    "Neutral":       1,
    "Positive":      0,
}

# Recency: reviews within this many days get an elevated weight multiplier
RECENCY_WINDOW_DAYS   = 90
RECENCY_MULTIPLIER    = 1.5    # applied to reviews within RECENCY_WINDOW_DAYS

# Repeat low-rater bonus weight (added on top of base score)
REPEAT_LOW_RATER_BONUS = 0.2   # 20% uplift if reviewer has multiple low-rated reviews

# ── SEVERITY & PRIORITY ───────────────────────────────────────────────────────

# Severity assignment logic (used in trust_safety_pipeline.py)
# These map to the SLA times below
SEVERITY_RULES = {
    # (label, max_rating) -> severity
    ("Treatment",     2): "Critical",
    ("Treatment",     3): "High",
    ("Communication", 2): "High",
    ("Communication", 3): "Medium",
    ("Waiting Time",  2): "High",
    ("Pricing",       2): "High",
    ("Staff",         5): "Medium",   # all staff → medium regardless of rating
    ("Neutral",       5): "Low",
    ("Positive",      5): "Safe",
}

PRIORITY_MAP = {
    "Critical": "P1 — Immediate (< 4 hours)",
    "High":     "P2 — Same Day (< 24 hours)",
    "Medium":   "P3 — Weekly Batch",
    "Low":      "P4 — Monthly Review",
    "Safe":     "P5 — No Action Required",
}

TIER_MAP = {
    "Critical": "TIER 1 — Immediate Review",
    "High":     "TIER 2 — Review within 24h",
    "Medium":   "TIER 3 — Weekly Batch",
    "Low":      "TIER 3 — Weekly Batch",
    "Safe":     "APPROVED — No Action",
}

SEVERITY_ORDER = {
    "Critical": 1,
    "High":     2,
    "Medium":   3,
    "Low":      4,
    "Safe":     5,
}

# ── SLA TIMES (hours) ─────────────────────────────────────────────────────────

SLA_P1_HOURS = 4     # Critical — must clear within 4 hours
SLA_P2_HOURS = 24    # High — must clear within 24 hours

# ── QUEUE COUNTS (from trust_safety_pipeline.py output) ──────────────────────

# NOTE: The Queue Clearance Simulator in dashboards/app.py no longer reads
# these — it loads live counts from reports/severity_distribution.csv on
# every run, so the simulator can't go stale. These constants are kept only
# as a documented historical reference / fallback value if that report is
# ever missing.
QUEUE_P1_CRITICAL = 34
QUEUE_P2_HIGH     = 111
QUEUE_P3_MEDIUM   = 29

# ── VISIT OUTLIER DETECTION ───────────────────────────────────────────────────

# Flag patients whose visit count exceeds mean + N * std
VISIT_OUTLIER_SIGMA = 2

# ── ML MODEL PARAMETERS ───────────────────────────────────────────────────────

ML_TEST_SIZE        = 0.30    # hold-out test fraction (matches LLM eval split)
ML_RANDOM_STATE     = 42      # random seed for reproducibility
ML_STRATIFY         = True    # stratify split by label
ML_MAX_FEATURES     = 5000    # TF-IDF vocabulary size
ML_NGRAM_RANGE      = (1, 2)  # unigrams + bigrams
ML_MAX_ITER         = 2000    # LogisticRegression max iterations
ML_CLASS_WEIGHT     = "balanced"  # correct for class imbalance

# ── LLM EVALUATION ───────────────────────────────────────────────────────────

LLM_DEV_FRACTION    = 0.70    # fraction used for prompt development
LLM_TEST_FRACTION   = 0.30    # fraction used as held-out test set (never seen during dev)
LLM_RANDOM_STATE    = 42
LLM_MODEL           = "qwen2.5:7b"

# ── DATA LABELING CATEGORIES ──────────────────────────────────────────────────

REVIEW_CATEGORIES = [
    "Positive",
    "Treatment",
    "Communication",
    "Waiting Time",
    "Pricing",
    "Staff",
    "Neutral",
]

COMPLAINT_CATEGORIES = [
    "Treatment",
    "Communication",
    "Waiting Time",
    "Pricing",
    "Staff",
]
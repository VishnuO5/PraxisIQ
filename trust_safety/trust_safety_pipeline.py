"""
trust_safety_pipeline.py
========================
Unified Trust & Safety pipeline — replaces:
  - case_management_system.py
  - risk_escalation_engine.py
  - moderation_queue.py
  - review_risk_mapping.py
  - trust_safety_metrics.py

All five files were doing the same risk_map logic with different output filenames.
This single pipeline does everything in one structured pass with proper scoring.

Outputs (all saved to reports/):
  - trust_safety_metrics.csv
  - trust_safety_risk_summary.csv
  - moderation_queue.csv
  - case_management_queue.csv
  - risk_escalation_queue.csv
  - severity_distribution.csv
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "PraxisIQ.db"

# ── PRE-FLIGHT ───────────────────────────────────────────────────────────────

if not os.path.exists(DB_PATH):
    print(f"[ERROR] Database not found: {DB_PATH}")
    print("Run create_database.py first.")
    sys.exit(1)

os.makedirs("reports", exist_ok=True)

print("\nTrust & Safety Pipeline")
print("=" * 70)

# ── LOAD DATA ────────────────────────────────────────────────────────────────

conn = sqlite3.connect(DB_PATH)

reviews = pd.read_sql_query("""
    SELECT
        Review_ID,
        Reviewer_Name,
        Rating,
        Review_Date,
        Label,
        Review_Text
    FROM Reviews
""", conn)

conn.close()

print(f"Loaded {len(reviews)} reviews")

# ── STEP 1: RISK CLASSIFICATION ───────────────────────────────────────────────

# Category-level risk mapping
RISK_MAP = {
    "Treatment"    : "High Risk",
    "Communication": "Needs Review",
    "Waiting Time" : "Needs Review",
    "Pricing"      : "Needs Review",
    "Staff"        : "Needs Review",
    "Neutral"      : "Safe",
    "Positive"     : "Safe",
}

# Severity assignment — combines category AND rating
def assign_severity(row):
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

PRIORITY_MAP = {
    "Critical": "P1 — Immediate (< 4 hours)",
    "High"    : "P2 — Same Day (< 24 hours)",
    "Medium"  : "P3 — Weekly Batch",
    "Low"     : "P4 — Monthly Review",
    "Safe"    : "P5 — No Action Required",
}

TIER_MAP = {
    "Critical": "TIER 1 — Immediate Review",
    "High"    : "TIER 2 — Review within 24h",
    "Medium"  : "TIER 3 — Weekly Batch",
    "Low"     : "TIER 3 — Weekly Batch",
    "Safe"    : "APPROVED — No Action",
}

reviews["Risk_Level"]     = reviews["Label"].map(RISK_MAP)
reviews["Severity"]       = reviews.apply(assign_severity, axis=1)
reviews["Priority"]       = reviews["Severity"].map(PRIORITY_MAP)
reviews["Moderation_Tier"]= reviews["Severity"].map(TIER_MAP)

# ── STEP 2: COMPOSITE RISK SCORE ─────────────────────────────────────────────

CATEGORY_WEIGHT = {
    "Treatment"    : 5,
    "Communication": 4,
    "Staff"        : 3,
    "Waiting Time" : 2,
    "Pricing"      : 2,
    "Neutral"      : 1,
    "Positive"     : 0,
}

# Recency: reviews in last 90 days get 1.5x weight
reviews["Review_Date_parsed"] = pd.to_datetime(reviews["Review_Date"], errors="coerce")
cutoff_90d = pd.Timestamp.now() - pd.Timedelta(days=90)
reviews["Recency_Multiplier"] = reviews["Review_Date_parsed"].apply(
    lambda d: 1.5 if pd.notna(d) and d >= cutoff_90d else 1.0
)

# Reviewer history: repeat low-rater flag
reviewer_history = (
    reviews.groupby("Reviewer_Name")
    .agg(
        Prior_Reviews        = ("Review_ID", "count"),
        Historical_Avg_Rating= ("Rating", "mean")
    )
    .reset_index()
)
reviewer_history["Repeat_Low_Rater"] = (
    (reviewer_history["Prior_Reviews"] > 1) &
    (reviewer_history["Historical_Avg_Rating"] < 3.0)
).astype(int)

reviews = reviews.merge(reviewer_history, on="Reviewer_Name", how="left")

reviews["Category_Weight"] = reviews["Label"].map(CATEGORY_WEIGHT).fillna(0)

reviews["Risk_Score"] = (
    reviews["Category_Weight"]
    * (6 - reviews["Rating"])
    * reviews["Recency_Multiplier"]
    * (1 + 0.2 * reviews["Repeat_Low_Rater"])
).round(2)

# ── STEP 3: CASE ID + QUEUE POSITION ─────────────────────────────────────────

SEVERITY_ORDER = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4, "Safe": 5}
reviews["Severity_Order"] = reviews["Severity"].map(SEVERITY_ORDER)

reviews_sorted = reviews.sort_values(
    by=["Severity_Order", "Rating", "Risk_Score"],
    ascending=[True, True, False]
).reset_index(drop=True)

reviews_sorted["Case_ID"]       = [f"CASE_{i+1:04d}" for i in range(len(reviews_sorted))]
reviews_sorted["Queue_Position"] = range(1, len(reviews_sorted) + 1)
reviews_sorted["Status"]         = "Open"

# ── STEP 4: PRINT SUMMARY ─────────────────────────────────────────────────────

print("\n── Risk Level Distribution ──")
risk_counts = reviews["Risk_Level"].value_counts()
for level, count in risk_counts.items():
    pct = count / len(reviews) * 100
    print(f"  {level:<15}: {count:>4} reviews ({pct:.1f}%)")

print("\n── Severity Distribution ──")
sev_counts = reviews["Severity"].value_counts()
for sev, count in sev_counts.items():
    pct = count / len(reviews) * 100
    print(f"  {sev:<10}: {count:>4} reviews ({pct:.1f}%)")

print("\n── Top 15 Priority Cases ──")
top_cases = reviews_sorted[
    ["Case_ID", "Queue_Position", "Severity", "Priority",
     "Label", "Rating", "Risk_Score", "Reviewer_Name"]
].head(15)
print(top_cases.to_string(index=False))

critical_count = len(reviews[reviews["Severity"] == "Critical"])
high_count     = len(reviews[reviews["Severity"] == "High"])
print(f"\nCritical cases requiring immediate review : {critical_count}")
print(f"High priority cases (same day)            : {high_count}")
print(f"Total cases in moderation queue           : {len(reviews)}")

# ── STEP 5: SAVE ALL OUTPUTS ──────────────────────────────────────────────────

# 1. Trust & Safety Metrics summary
total = len(reviews)
metrics = pd.DataFrame({
    "Metric": [
        "Total Reviews",
        "Safe Reviews",
        "Needs Review",
        "High Risk Reviews",
        "Safe %",
        "Needs Review %",
        "High Risk %",
        "Critical Cases",
        "Avg Risk Score (non-safe)",
    ],
    "Value": [
        total,
        len(reviews[reviews["Risk_Level"] == "Safe"]),
        len(reviews[reviews["Risk_Level"] == "Needs Review"]),
        len(reviews[reviews["Risk_Level"] == "High Risk"]),
        round(len(reviews[reviews["Risk_Level"] == "Safe"]) / total * 100, 2),
        round(len(reviews[reviews["Risk_Level"] == "Needs Review"]) / total * 100, 2),
        round(len(reviews[reviews["Risk_Level"] == "High Risk"]) / total * 100, 2),
        critical_count,
        round(reviews[reviews["Risk_Level"] != "Safe"]["Risk_Score"].mean(), 2),
    ]
})
metrics.to_csv("reports/trust_safety_metrics.csv", index=False)

# 2. Risk summary by category
risk_summary = (
    reviews.groupby(["Label", "Risk_Level"])
    .agg(Count=("Review_ID", "count"), Avg_Rating=("Rating", "mean"))
    .reset_index()
    .sort_values("Count", ascending=False)
)
risk_summary["Avg_Rating"] = risk_summary["Avg_Rating"].round(2)
risk_summary.to_csv("reports/trust_safety_risk_summary.csv", index=False)

# 3. Full moderation queue
moderation_cols = [
    "Case_ID", "Queue_Position", "Moderation_Tier", "Severity", "Priority",
    "Review_ID", "Reviewer_Name", "Review_Date", "Rating", "Label",
    "Risk_Level", "Risk_Score", "Repeat_Low_Rater", "Review_Text"
]
reviews_sorted[moderation_cols].to_csv("reports/moderation_queue.csv", index=False)

# 4. Case management queue (P1 and P2 only)
case_mgmt = reviews_sorted[
    reviews_sorted["Severity"].isin(["Critical", "High"])
][moderation_cols].copy()
case_mgmt.to_csv("reports/case_management_queue.csv", index=False)

# 5. Risk escalation queue
reviews_sorted[moderation_cols].to_csv("reports/risk_escalation_queue.csv", index=False)

# 6. Severity distribution
sev_dist = (
    reviews["Severity"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "Severity", "Severity": "Count"})
)
sev_dist.to_csv("reports/severity_distribution.csv", index=False)

print("\nSaved:")
print("  reports/trust_safety_metrics.csv")
print("  reports/trust_safety_risk_summary.csv")
print("  reports/moderation_queue.csv")
print("  reports/case_management_queue.csv")
print("  reports/risk_escalation_queue.csv")
print("  reports/severity_distribution.csv")
print("\nPipeline complete.")
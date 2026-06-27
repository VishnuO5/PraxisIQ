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

# ── CONFIG ────────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    REPORTS_DIR,
    RISK_MAP,
    CATEGORY_WEIGHT,
    RECENCY_WINDOW_DAYS,
    RECENCY_MULTIPLIER,
    REPEAT_LOW_RATER_BONUS,
    PRIORITY_MAP,
    TIER_MAP,
    SEVERITY_ORDER,
)

# ── PRE-FLIGHT ───────────────────────────────────────────────────────────────

if not os.path.exists(DB_PATH):
    print(f"[ERROR] Database not found: {DB_PATH}")
    print("Run create_database.py first.")
    sys.exit(1)

os.makedirs(REPORTS_DIR, exist_ok=True)

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

reviews["Risk_Level"]      = reviews["Label"].map(RISK_MAP)
reviews["Severity"]        = reviews.apply(assign_severity, axis=1)
reviews["Priority"]        = reviews["Severity"].map(PRIORITY_MAP)
reviews["Moderation_Tier"] = reviews["Severity"].map(TIER_MAP)

# ── STEP 2: COMPOSITE RISK SCORE ─────────────────────────────────────────────

# Recency multiplier — from config
reviews["Review_Date_parsed"] = pd.to_datetime(reviews["Review_Date"], errors="coerce")
cutoff = pd.Timestamp.now() - pd.Timedelta(days=RECENCY_WINDOW_DAYS)
reviews["Recency_Multiplier"] = reviews["Review_Date_parsed"].apply(
    lambda d: RECENCY_MULTIPLIER if pd.notna(d) and d >= cutoff else 1.0
)

# Reviewer history: repeat low-rater flag
reviewer_history = (
    reviews.groupby("Reviewer_Name")
    .agg(
        Prior_Reviews         = ("Review_ID", "count"),
        Historical_Avg_Rating = ("Rating", "mean")
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
    * (1 + REPEAT_LOW_RATER_BONUS * reviews["Repeat_Low_Rater"])
).round(2)

# ── STEP 3: CASE ID + QUEUE POSITION ─────────────────────────────────────────

reviews["Severity_Order"] = reviews["Severity"].map(SEVERITY_ORDER)

reviews_sorted = reviews.sort_values(
    by=["Severity_Order", "Rating", "Risk_Score"],
    ascending=[True, True, False]
).reset_index(drop=True)

reviews_sorted["Case_ID"]        = [f"CASE_{i+1:04d}" for i in range(len(reviews_sorted))]
reviews_sorted["Queue_Position"]  = range(1, len(reviews_sorted) + 1)
reviews_sorted["Status"]          = "Open"

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

total = len(reviews)

metrics = pd.DataFrame({
    "Metric": [
        "Total Reviews", "Safe Reviews", "Needs Review", "High Risk Reviews",
        "Safe %", "Needs Review %", "High Risk %", "Critical Cases",
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
metrics.to_csv(os.path.join(REPORTS_DIR, "trust_safety_metrics.csv"), index=False)

risk_summary = (
    reviews.groupby(["Label", "Risk_Level"])
    .agg(Count=("Review_ID", "count"), Avg_Rating=("Rating", "mean"))
    .reset_index()
    .sort_values("Count", ascending=False)
)
risk_summary["Avg_Rating"] = risk_summary["Avg_Rating"].round(2)
risk_summary.to_csv(os.path.join(REPORTS_DIR, "trust_safety_risk_summary.csv"), index=False)

moderation_cols = [
    "Case_ID", "Queue_Position", "Moderation_Tier", "Severity", "Priority",
    "Review_ID", "Reviewer_Name", "Review_Date", "Rating", "Label",
    "Risk_Level", "Risk_Score", "Repeat_Low_Rater", "Review_Text"
]
reviews_sorted[moderation_cols].to_csv(os.path.join(REPORTS_DIR, "moderation_queue.csv"), index=False)

case_mgmt = reviews_sorted[
    reviews_sorted["Severity"].isin(["Critical", "High"])
][moderation_cols].copy()
case_mgmt.to_csv(os.path.join(REPORTS_DIR, "case_management_queue.csv"), index=False)

reviews_sorted[moderation_cols].to_csv(os.path.join(REPORTS_DIR, "risk_escalation_queue.csv"), index=False)

sev_dist = (
    reviews["Severity"]
    .value_counts()
    .reset_index()
    .rename(columns={"index": "Severity", "Severity": "Count"})
)
sev_dist.to_csv(os.path.join(REPORTS_DIR, "severity_distribution.csv"), index=False)

print("\nSaved:")
print(f"  {REPORTS_DIR}/trust_safety_metrics.csv")
print(f"  {REPORTS_DIR}/trust_safety_risk_summary.csv")
print(f"  {REPORTS_DIR}/moderation_queue.csv")
print(f"  {REPORTS_DIR}/case_management_queue.csv")
print(f"  {REPORTS_DIR}/risk_escalation_queue.csv")
print(f"  {REPORTS_DIR}/severity_distribution.csv")
print("\nPipeline complete.")
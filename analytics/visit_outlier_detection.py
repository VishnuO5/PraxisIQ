"""
visit_outlier_detection.py
==========================
Detects patients with statistically anomalous visit frequencies.

Method: Z-score with a 2-sigma threshold.
  - Z > 2.0  → high-frequency outlier (unusually frequent visitor)
  - Also flags low-engagement patients: long care span but very few visits

Outputs:
  - reports/visit_outliers.csv
  - reports/visit_outlier_summary.csv
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger
log = get_logger(__name__)
import sqlite3
import pandas as pd




if not os.path.exists(DB_PATH):
    log.error(f"[ERROR] Database not found: {DB_PATH}")
    log.info("Run create_database.py first.")
    sys.exit(1)

os.makedirs(REPORTS_DIR, exist_ok=True)

log.info("\nVisit Outlier Detection")
log.info("=" * 60)

conn = sqlite3.connect(DB_PATH)

patients = pd.read_sql_query(
    """
    SELECT
        Patient_Id,
        Age,
        Gender,
        Primary_Treatment,
        Total_Visits,
        Returned_Patient,
        First_Visit_Date,
        Last_Visit_Date
    FROM Patients
    """,
    conn,
)

conn.close()

# ── STATISTICS ────────────────────────────────────────────────────────────────

mean_visits = patients["Total_Visits"].mean()
std_visits  = patients["Total_Visits"].std()
SIGMA       = 2.0
threshold   = mean_visits + SIGMA * std_visits

log.info(f"\nVisit Distribution")
log.info(f"  Mean visits       : {mean_visits:.2f}")
log.info(f"  Std deviation     : {std_visits:.2f}")
log.info(f"  Outlier threshold : {threshold:.2f} visits  (mean + {SIGMA}σ)")
log.info(f"  Min / Max         : {patients['Total_Visits'].min()} / {patients['Total_Visits'].max()}")

# ── PERCENTILE BREAKDOWN ──────────────────────────────────────────────────────

percentiles = patients["Total_Visits"].quantile([0.50, 0.75, 0.90, 0.95, 0.99])
log.info("\nVisit Count Percentiles:")
for p, v in percentiles.items():
    log.info(f"  {int(p * 100)}th percentile : {v:.0f} visits")

# ── Z-SCORE OUTLIERS ──────────────────────────────────────────────────────────

patients["Z_Score"] = (
    (patients["Total_Visits"] - mean_visits) / std_visits
).round(2)

outliers = patients[patients["Total_Visits"] > threshold].copy()
outliers = outliers.sort_values("Total_Visits", ascending=False).reset_index(drop=True)

log.info(f"\nOutlier Patients (Z > {SIGMA}σ) : {len(outliers)}")

# ── CARE SPAN ─────────────────────────────────────────────────────────────────

patients["First_Visit_Date"] = pd.to_datetime(patients["First_Visit_Date"], format="mixed")
patients["Last_Visit_Date"]  = pd.to_datetime(patients["Last_Visit_Date"],  format="mixed")
patients["Care_Span_Days"]   = (
    patients["Last_Visit_Date"] - patients["First_Visit_Date"]
).dt.days

# Low engagement: top 25% care span but only 1–2 visits
span_q75 = patients["Care_Span_Days"].quantile(0.75)
low_engagement = patients[
    (patients["Care_Span_Days"] > span_q75) &
    (patients["Total_Visits"] <= 2)
].copy()

log.info(f"Low-Engagement Patients        : {len(low_engagement)}")
log.info(f"  (care span > {span_q75:.0f} days but ≤ 2 visits)")

# ── TREATMENT BREAKDOWN ───────────────────────────────────────────────────────

outliers_with_span = outliers.merge(
    patients[["Patient_Id", "Care_Span_Days"]],
    on="Patient_Id",
    how="left"
)

treatment_summary = (
    outliers_with_span.groupby("Primary_Treatment")
    .agg(
        Outlier_Count=("Patient_Id", "count"),
        Avg_Visits=("Total_Visits", "mean"),
        Max_Visits=("Total_Visits", "max"),
    )
    .round(1)
    .sort_values("Outlier_Count", ascending=False)
    .reset_index()
)

log.info("\nOutliers by Treatment Type:")
log.info(treatment_summary.to_string(index=False))

# ── TOP OUTLIERS ──────────────────────────────────────────────────────────────

display_cols = [
    "Patient_Id", "Age", "Gender",
    "Primary_Treatment", "Total_Visits", "Z_Score", "Care_Span_Days"
]
log.info("\nTop 20 High-Visit Outlier Patients:")
log.info(outliers_with_span[display_cols].head(20).to_string(index=False))

# ── SAVE ──────────────────────────────────────────────────────────────────────

save_cols = [
    "Patient_Id", "Age", "Gender", "Primary_Treatment",
    "Total_Visits", "Z_Score", "Care_Span_Days", "Returned_Patient"
]
outliers_with_span[[c for c in save_cols if c in outliers_with_span.columns]].to_csv(
    os.path.join(REPORTS_DIR, "visit_outliers.csv"), index=False
)

summary = pd.DataFrame({
    "Metric": [
        "Total Patients",
        "Mean Visits",
        "Std Deviation",
        "Outlier Threshold (mean+2σ)",
        "Outlier Count",
        "Outlier Rate (%)",
        "Low Engagement Count",
    ],
    "Value": [
        len(patients),
        round(mean_visits, 2),
        round(std_visits, 2),
        round(threshold, 2),
        len(outliers),
        round(len(outliers) / len(patients) * 100, 1),
        len(low_engagement),
    ],
})
summary.to_csv(os.path.join(REPORTS_DIR, "visit_outlier_summary.csv"), index=False)

log.info("\nSaved:")
log.info("  reports/visit_outliers.csv")
log.info("  reports/visit_outlier_summary.csv")
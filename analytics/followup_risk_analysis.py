"""
followup_risk_analysis.py
=========================
Identifies patients at risk of dropping off care based on visit behaviour
and treatment patterns.

Real schema has no Follow_Up_Required / Follow_Up_Completed columns.
Risk is derived from three signals that DO exist in the real data:
  1. Returned_Patient == 'No'  (never came back after first visit)
  2. Single-visit high-complexity treatments (Root Canal, Implant, etc.)
  3. Total_Visits == 1 (one-and-done, regardless of treatment)
"""

import os
import sys
import sqlite3
import pandas as pd

DB_PATH = "PraxisIQ.db"

if not os.path.exists(DB_PATH):
    print(f"[ERROR] Database not found: {DB_PATH}")
    print("Run create_database.py first.")
    sys.exit(1)

os.makedirs("reports", exist_ok=True)

print("\nFollow-Up Risk Analysis")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)

patients = pd.read_sql_query(
    """
    SELECT
        Patient_Id,
        Gender,
        Age,
        First_Visit_Date,
        Last_Visit_Date,
        Total_Visits,
        Returned_Patient,
        Primary_Treatment
    FROM Patients
    """,
    conn,
)

conn.close()

# ── HIGH-COMPLEXITY TREATMENTS (should require follow-up by nature) ──────────
HIGH_COMPLEXITY = {
    "Root Canal",
    "Implant",
    "Metal Braces Treatment",
    "Aligner",
    "Gum Treatment",
    "Fixed Bridge",
    "Partial Denture",
    "Complete Denture",
    "Deep Scaling and Root Planing",
    "Crown/Cap",
}

# ── DERIVE RISK SIGNALS ───────────────────────────────────────────────────────

patients["First_Visit_Date"] = pd.to_datetime(patients["First_Visit_Date"], format="mixed")
patients["Last_Visit_Date"]  = pd.to_datetime(patients["Last_Visit_Date"], format="mixed")
patients["Care_Span_Days"]   = (
    patients["Last_Visit_Date"] - patients["First_Visit_Date"]
).dt.days

patients["High_Complexity_Treatment"] = patients["Primary_Treatment"].isin(HIGH_COMPLEXITY)
patients["Single_Visit_Only"]         = patients["Total_Visits"] == 1
patients["Never_Returned"]            = patients["Returned_Patient"] == "No"

# Risk score 0–3: each flag adds 1 point
patients["Risk_Score"] = (
    patients["High_Complexity_Treatment"].astype(int) +
    patients["Single_Visit_Only"].astype(int) +
    patients["Never_Returned"].astype(int)
)

def risk_tier(score):
    if score == 3:
        return "Critical"
    elif score == 2:
        return "High"
    elif score == 1:
        return "Medium"
    else:
        return "Low"

patients["Risk_Tier"] = patients["Risk_Score"].apply(risk_tier)

# ── PRINT SUMMARY ─────────────────────────────────────────────────────────────

print(f"\nTotal Patients Analysed : {len(patients)}")
print(f"Critical Risk (score=3) : {len(patients[patients['Risk_Score'] == 3])}")
print(f"High Risk     (score=2) : {len(patients[patients['Risk_Score'] == 2])}")
print(f"Medium Risk   (score=1) : {len(patients[patients['Risk_Score'] == 1])}")
print(f"Low Risk      (score=0) : {len(patients[patients['Risk_Score'] == 0])}")

# ── DROPOUT RATE BY TREATMENT ─────────────────────────────────────────────────

treatment_risk = (
    patients.groupby("Primary_Treatment")
    .agg(
        Total_Patients=("Patient_Id", "count"),
        Never_Returned=("Never_Returned", "sum"),
    )
    .assign(
        Dropout_Rate_Pct=lambda d: (
            d["Never_Returned"] / d["Total_Patients"] * 100
        ).round(1)
    )
    .sort_values("Dropout_Rate_Pct", ascending=False)
    .reset_index()
)

print("\nDropout Rate by Treatment:\n")
print(treatment_risk.to_string(index=False))

# ── SAVE ──────────────────────────────────────────────────────────────────────

at_risk = patients[patients["Risk_Score"] >= 2].sort_values(
    ["Risk_Score", "Age"], ascending=[False, False]
)

save_cols = [
    "Patient_Id", "Age", "Gender", "Primary_Treatment",
    "Total_Visits", "Care_Span_Days", "Risk_Score", "Risk_Tier"
]
at_risk[save_cols].to_csv("reports/followup_risk_queue.csv", index=False)
treatment_risk.to_csv("reports/treatment_dropout_rates.csv", index=False)

print("\nSaved:")
print("  reports/followup_risk_queue.csv")
print("  reports/treatment_dropout_rates.csv")
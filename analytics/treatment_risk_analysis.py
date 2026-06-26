"""
treatment_risk_analysis.py
==========================
Analyses patient risk by treatment type, using the columns that actually
exist in PraxisIQ.db: Total_Visits and Returned_Patient.

Goes beyond simple counts to identify:
- Which treatments have the highest non-return rate (patient didn't come back)
- Which treatments produce unusually high visit counts (possible complications
  or repeated re-treatment)
- Statistical significance of treatment-level risk differences
- Risk tier distribution per treatment
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats

DB_PATH  = "PraxisIQ.db"
OUT_PATH = "reports/treatment_risk_analysis.csv"

# ── PRE-FLIGHT ───────────────────────────────────────────────────────────────

if not os.path.exists(DB_PATH):
    print(f"[ERROR] Database not found: {DB_PATH}")
    print("Run create_database.py first.")
    sys.exit(1)

print("\nTreatment Risk Analysis")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)

# ── LOAD DATA ────────────────────────────────────────────────────────────────
# NOTE: Only columns that actually exist in the Patients table are used here:
# Patient_Id, Gender, Age, Total_Visits, Returned_Patient, Primary_Treatment.
# There is no Risk_Category or Follow_Up column in this dataset.

patients = pd.read_sql_query("""
    SELECT
        Patient_Id,
        Primary_Treatment,
        Total_Visits,
        Returned_Patient,
        Age,
        Gender
    FROM Patients
""", conn)

conn.close()

print(f"\nLoaded {len(patients)} patients")

# ── FEATURE ENGINEERING ──────────────────────────────────────────────────────

patients["did_not_return"] = (patients["Returned_Patient"] == "No").astype(int)

# A patient is flagged "high visit" if their visit count is in the top quartile
# of the whole dataset (a proxy for repeated/complicated treatment, since this
# dataset has no explicit complication or follow-up field).
visit_threshold = patients["Total_Visits"].quantile(0.75)
patients["high_visit_count"] = (patients["Total_Visits"] > visit_threshold).astype(int)

print(f"High-visit threshold (75th percentile): > {visit_threshold:.0f} visits")

# ── TREATMENT-LEVEL RISK PROFILE ─────────────────────────────────────────────

treatment_stats = (
    patients.groupby("Primary_Treatment")
    .agg(
        Total_Patients      = ("Patient_Id",        "count"),
        Did_Not_Return       = ("did_not_return",     "sum"),
        High_Visit_Count     = ("high_visit_count",   "sum"),
        Avg_Total_Visits     = ("Total_Visits",        "mean"),
        Avg_Age              = ("Age",                 "mean"),
    )
    .reset_index()
)

treatment_stats["Non_Return_Rate_Pct"] = (
    treatment_stats["Did_Not_Return"] / treatment_stats["Total_Patients"] * 100
).round(1)

treatment_stats["High_Visit_Rate_Pct"] = (
    treatment_stats["High_Visit_Count"] / treatment_stats["Total_Patients"] * 100
).round(1)

treatment_stats["Avg_Total_Visits"] = treatment_stats["Avg_Total_Visits"].round(1)
treatment_stats["Avg_Age"] = treatment_stats["Avg_Age"].round(1)

# ── RISK TIER ASSIGNMENT ─────────────────────────────────────────────────────

def assign_risk_tier(row):
    score = 0
    if row["Non_Return_Rate_Pct"] >= 40:
        score += 2
    elif row["Non_Return_Rate_Pct"] >= 25:
        score += 1
    if row["High_Visit_Rate_Pct"] >= 35:
        score += 2
    elif row["High_Visit_Rate_Pct"] >= 20:
        score += 1
    if score >= 3:
        return "CRITICAL"
    elif score >= 2:
        return "HIGH"
    elif score >= 1:
        return "MEDIUM"
    else:
        return "LOW"

treatment_stats["Risk_Tier"] = treatment_stats.apply(assign_risk_tier, axis=1)

# ── STATISTICAL TEST ─────────────────────────────────────────────────────────
# Chi-square test: is non-return rate significantly different across treatments?

contingency_data = treatment_stats[
    treatment_stats["Total_Patients"] >= 5  # only treatments with enough data
][["Did_Not_Return", "Total_Patients"]].copy()

contingency_data["Returned"] = (
    contingency_data["Total_Patients"] - contingency_data["Did_Not_Return"]
)

if len(contingency_data) >= 2:
    chi2, p_value, dof, _ = stats.chi2_contingency(
        contingency_data[["Did_Not_Return", "Returned"]].values
    )
    print(f"\nChi-Square Test — Non-Return Rate across Treatments:")
    print(f"  Chi2 = {chi2:.4f}, p = {p_value:.4f}, dof = {dof}")
    if p_value < 0.05:
        print("  Result: SIGNIFICANT — non-return rate differs meaningfully by treatment (p < 0.05)")
    else:
        print("  Result: NOT SIGNIFICANT — no strong treatment-level difference detected")

# ── PRINT RESULTS ────────────────────────────────────────────────────────────

results = treatment_stats.sort_values("Non_Return_Rate_Pct", ascending=False)

print(f"\n{'Treatment':<35} {'Patients':>8} {'NonReturn%':>11} {'HighVisit%':>11} {'Tier':>10}")
print("-" * 80)

for _, row in results.iterrows():
    print(
        f"{row['Primary_Treatment']:<35} "
        f"{int(row['Total_Patients']):>8} "
        f"{row['Non_Return_Rate_Pct']:>10.1f}% "
        f"{row['High_Visit_Rate_Pct']:>10.1f}% "
        f"{row['Risk_Tier']:>10}"
    )

# ── CRITICAL TREATMENTS SUMMARY ───────────────────────────────────────────────

critical = results[results["Risk_Tier"].isin(["CRITICAL", "HIGH"])]
print(f"\nCRITICAL/HIGH risk treatments: {len(critical)}")
for _, row in critical.iterrows():
    print(
        f"  {row['Primary_Treatment']}: "
        f"{row['Did_Not_Return']} non-returning patients "
        f"({row['Non_Return_Rate_Pct']}% of {int(row['Total_Patients'])}), "
        f"high-visit rate {row['High_Visit_Rate_Pct']}%"
    )

# ── SAVE ─────────────────────────────────────────────────────────────────────

os.makedirs("reports", exist_ok=True)
results.to_csv(OUT_PATH, index=False)
print(f"\nSaved: {OUT_PATH}")
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger
log = get_logger(__name__)
import sqlite3
import pandas as pd

from scipy.stats import f_oneway

log.info("\nModule 2 - Statistical Analysis")
log.info("=" * 60)

# ==========================
# LOAD DATA
# ==========================

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query(
    """
    SELECT
        Primary_Treatment,
        Total_Visits
    FROM Patients
    """,
    conn
)

conn.close()

log.info("\nTreatment Distribution:")
log.info(df["Primary_Treatment"].value_counts())

# ==========================
# PREPARE GROUPS
# ==========================

groups = []

for treatment in df["Primary_Treatment"].unique():

    visits = df[
        df["Primary_Treatment"] == treatment
    ]["Total_Visits"]

    groups.append(visits)

# ==========================
# ANOVA TEST
# ==========================

f_statistic, p_value = f_oneway(*groups)

log.info("\nANOVA Results")
log.info("=" * 60)

log.info(f"F Statistic: {f_statistic:.4f}")
log.info(f"P Value    : {p_value:.6f}")

# ==========================
# INTERPRETATION
# ==========================

if p_value < 0.05:

    conclusion = (
        "Significant difference detected "
        "between treatment groups."
    )

else:

    conclusion = (
        "No statistically significant difference "
        "between treatment groups."
    )

log.info("\nConclusion:")
log.info(conclusion)

# ==========================
# SAVE RESULTS
# ==========================

results = pd.DataFrame({
    "Metric": [
        "F Statistic",
        "P Value"
    ],
    "Value": [
        round(f_statistic, 4),
        round(p_value, 6)
    ]
})

results.to_csv(
    os.path.join(REPORTS_DIR, "statistical_analysis.csv"),
    index=False
)

log.info("\nSaved:")
log.info(os.path.join(REPORTS_DIR, "statistical_analysis.csv"))
# ── Chi-Square: Review Category vs Rating Tier ──────────────────
from scipy.stats import chi2_contingency

conn2 = sqlite3.connect(DB_PATH)
reviews = pd.read_sql_query("SELECT Label, Rating FROM Reviews", conn2)
conn2.close()

reviews['Rating_Tier'] = reviews['Rating'].apply(
    lambda r: 'Low (1-2)' if r <= 2 else ('Mid (3)' if r == 3 else 'High (4-5)')
)

contingency = pd.crosstab(reviews['Label'], reviews['Rating_Tier'])
chi2, p, dof, expected = chi2_contingency(contingency)

log.info("\nChi-Square Test — Review Category vs Rating Tier")
log.info("=" * 50)
log.info(f"Chi2 Statistic    : {chi2:.4f}")
log.info(f"P-Value           : {p:.6f}")
log.info(f"Degrees of Freedom: {dof}")

if p < 0.05:
    log.info("Result: Significant association between review category and rating.")
else:
    log.info("Result: No significant association found.")

chi2_results = pd.DataFrame({
    "Metric": ["Chi2 Statistic", "P-Value", "Degrees of Freedom"],
    "Value": [round(chi2, 4), round(p, 6), dof]
})

chi2_results.to_csv(os.path.join(REPORTS_DIR, "chi2_analysis.csv"), index=False)
log.info("\nSaved: reports/chi2_analysis.csv")
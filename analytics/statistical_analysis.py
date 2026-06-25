import sqlite3
import pandas as pd
from scipy.stats import f_oneway

print("\nModule 2 - Statistical Analysis")
print("=" * 60)

# ==========================
# LOAD DATA
# ==========================

conn = sqlite3.connect("PraxisIQ.db")

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

print("\nTreatment Distribution:")
print(df["Primary_Treatment"].value_counts())

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

print("\nANOVA Results")
print("=" * 60)

print(f"F Statistic: {f_statistic:.4f}")
print(f"P Value    : {p_value:.6f}")

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

print("\nConclusion:")
print(conclusion)

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
    "reports/statistical_analysis.csv",
    index=False
)

print("\nSaved:")
print("reports/statistical_analysis.csv")
# ── Chi-Square: Review Category vs Rating Tier ──────────────────
from scipy.stats import chi2_contingency

conn2 = sqlite3.connect("PraxisIQ.db")
reviews = pd.read_sql_query("SELECT Label, Rating FROM Reviews", conn2)
conn2.close()

reviews['Rating_Tier'] = reviews['Rating'].apply(
    lambda r: 'Low (1-2)' if r <= 2 else ('Mid (3)' if r == 3 else 'High (4-5)')
)

contingency = pd.crosstab(reviews['Label'], reviews['Rating_Tier'])
chi2, p, dof, expected = chi2_contingency(contingency)

print("\nChi-Square Test — Review Category vs Rating Tier")
print("=" * 50)
print(f"Chi2 Statistic    : {chi2:.4f}")
print(f"P-Value           : {p:.6f}")
print(f"Degrees of Freedom: {dof}")

if p < 0.05:
    print("Result: Significant association between review category and rating.")
else:
    print("Result: No significant association found.")

chi2_results = pd.DataFrame({
    "Metric": ["Chi2 Statistic", "P-Value", "Degrees of Freedom"],
    "Value": [round(chi2, 4), round(p, 6), dof]
})

chi2_results.to_csv("reports/chi2_analysis.csv", index=False)
print("\nSaved: reports/chi2_analysis.csv")
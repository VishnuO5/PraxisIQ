import sqlite3
import pandas as pd

print("\nTrust & Safety Review Risk Mapping")
print("=" * 60)

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Review_ID,
        Label,
        Rating,
        Review_Text
    FROM Reviews
    """,
    conn
)

conn.close()

risk_map = {
    "Positive": "Safe",
    "Neutral": "Safe",

    "Communication": "Needs Review",
    "Waiting Time": "Needs Review",
    "Pricing": "Needs Review",
    "Staff": "Needs Review",

    "Treatment": "High Risk"
}

df["Risk_Level"] = df["Label"].map(risk_map)

summary = (
    df["Risk_Level"]
    .value_counts()
    .reset_index()
)

summary.columns = [
    "Risk_Level",
    "Count"
]

print(summary)

summary.to_csv(
    "reports/trust_safety_risk_summary.csv",
    index=False
)

print("\nSaved:")
print("reports/trust_safety_risk_summary.csv")
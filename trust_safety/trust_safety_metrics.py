import sqlite3
import pandas as pd

print("\nTrust & Safety Metrics")
print("=" * 60)

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Label
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

total_reviews = len(df)

safe_count = len(df[df["Risk_Level"] == "Safe"])
needs_review_count = len(df[df["Risk_Level"] == "Needs Review"])
high_risk_count = len(df[df["Risk_Level"] == "High Risk"])

metrics = pd.DataFrame({
    "Metric": [
        "Total Reviews",
        "Safe Reviews",
        "Needs Review",
        "High Risk Reviews",
        "Safe %",
        "Needs Review %",
        "High Risk %"
    ],
    "Value": [
        total_reviews,
        safe_count,
        needs_review_count,
        high_risk_count,
        round((safe_count / total_reviews) * 100, 2),
        round((needs_review_count / total_reviews) * 100, 2),
        round((high_risk_count / total_reviews) * 100, 2)
    ]
})

print("\nTrust & Safety Metrics:\n")
print(metrics)

metrics.to_csv(
    "reports/trust_safety_metrics.csv",
    index=False
)

print("\nSaved:")
print("reports/trust_safety_metrics.csv")
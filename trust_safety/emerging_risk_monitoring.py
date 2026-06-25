import sqlite3
import pandas as pd

print("\nEmerging Risk Monitoring")
print("=" * 60)

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Review_Date,
        Label
    FROM Reviews
    WHERE Label != 'Positive'
    """,
    conn
)

conn.close()

df["Month"] = df["Review_Date"].str[:7]

monthly_risk = (
    df.groupby(
        ["Month", "Label"]
    )
    .size()
    .reset_index(name="Review_Count")
)

print("\nMonthly Risk Trends:\n")
print(monthly_risk.head(20))

monthly_risk.to_csv(
    "reports/emerging_risk_monitoring.csv",
    index=False
)

print("\nSaved:")
print("reports/emerging_risk_monitoring.csv")
import sqlite3
import pandas as pd

print("\nRisk Escalation Engine")
print("=" * 60)

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Review_ID,
        Rating,
        Label,
        Review_Text
    FROM Reviews
    """,
    conn
)

conn.close()

def assign_severity(row):

    if row["Label"] == "Treatment" and row["Rating"] <= 2:
        return "Critical"

    elif row["Label"] in [
        "Communication",
        "Pricing",
        "Waiting Time",
        "Staff"
    ] and row["Rating"] <= 2:
        return "High"

    elif row["Label"] == "Neutral":
        return "Low"

    else:
        return "Medium"


df["Severity"] = df.apply(
    assign_severity,
    axis=1
)

severity_summary = (
    df["Severity"]
    .value_counts()
    .reset_index()
)

severity_summary.columns = [
    "Severity",
    "Count"
]

print("\nSeverity Distribution:\n")
print(severity_summary)

df.to_csv(
    "reports/risk_escalation_queue.csv",
    index=False
)

severity_summary.to_csv(
    "reports/severity_distribution.csv",
    index=False
)

print("\nSaved:")
print("reports/risk_escalation_queue.csv")
print("reports/severity_distribution.csv")
import sqlite3
import pandas as pd

print("\nTrust & Safety Case Management System")
print("=" * 70)

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

priority_map = {
    "Critical": "P1",
    "High": "P2",
    "Medium": "P3",
    "Low": "P4"
}

df["Priority"] = df["Severity"].map(
    priority_map
)

df["Case_ID"] = [
    f"CASE_{i:04d}"
    for i in range(1, len(df) + 1)
]

df["Status"] = "Open"

cases = df[
    [
        "Case_ID",
        "Review_ID",
        "Priority",
        "Severity",
        "Status",
        "Label",
        "Rating"
    ]
]

cases = cases.sort_values(
    by=["Priority", "Rating"]
)

print("\nTop Investigation Cases\n")
print(cases.head(20))

print("\nCase Summary\n")

print(
    cases["Priority"]
    .value_counts()
)

cases.to_csv(
    "reports/case_management_queue.csv",
    index=False
)

print("\nSaved:")
print("reports/case_management_queue.csv")
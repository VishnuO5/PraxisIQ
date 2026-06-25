import sqlite3
import pandas as pd

print("\nTrust & Safety Moderation Queue")
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

priority_order = {
    "High Risk": 1,
    "Needs Review": 2,
    "Safe": 3
}

df["Priority"] = df["Risk_Level"].map(priority_order)

moderation_queue = df.sort_values(
    by=["Priority", "Rating"],
    ascending=[True, True]
)

print("\nTop 20 Reviews Requiring Investigation:\n")
print(
    moderation_queue[
        [
            "Review_ID",
            "Risk_Level",
            "Rating",
            "Label"
        ]
    ].head(20)
)

moderation_queue.to_csv(
    "reports/moderation_queue.csv",
    index=False
)

print("\nSaved:")
print("reports/moderation_queue.csv")
import sqlite3
import pandas as pd

print("\nSuspicious Reviewer Detection")
print("=" * 50)

conn = sqlite3.connect("PraxisIQ.db")

query = """
SELECT
    Reviewer_Name,
    COUNT(*) AS Review_Count,
    AVG(Rating) AS Average_Rating
FROM Reviews
GROUP BY Reviewer_Name
HAVING COUNT(*) > 1
ORDER BY Review_Count DESC;
"""

df = pd.read_sql_query(query, conn)

conn.close()

print("\nRepeat Reviewers:\n")
print(df)

print("\nTotal Repeat Reviewers:")
print(len(df))

df.to_csv(
    "reports/suspicious_reviewer_detection.csv",
    index=False
)

print("\nSaved:")
print("reports/suspicious_reviewer_detection.csv")
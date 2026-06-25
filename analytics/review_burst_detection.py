import sqlite3
import pandas as pd

print("\nReview Burst Detection")
print("=" * 50)

conn = sqlite3.connect("PraxisIQ.db")

query = """
SELECT
    Review_Date,
    COUNT(*) AS Review_Count
FROM Reviews
GROUP BY Review_Date
ORDER BY Review_Count DESC;
"""

df = pd.read_sql_query(query, conn)

conn.close()

# Calculate average reviews per day
average_reviews = df["Review_Count"].mean()

# Burst threshold
threshold = average_reviews * 3

bursts = df[
    df["Review_Count"] > threshold
]

print("\nAverage Reviews Per Day:")
print(round(average_reviews, 2))

print("\nBurst Threshold:")
print(round(threshold, 2))

print("\nPotential Review Bursts:\n")
print(bursts)

print("\nTotal Burst Days:")
print(len(bursts))

bursts.to_csv(
    "reports/review_burst_detection.csv",
    index=False
)

print("\nSaved:")
print("reports/review_burst_detection.csv")
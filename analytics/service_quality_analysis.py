import sqlite3
import pandas as pd

print("\nService Quality Analysis")
print("=" * 50)

conn = sqlite3.connect("PraxisIQ.db")

query = """
SELECT
    Label,
    COUNT(*) AS Review_Count,
    ROUND(AVG(Rating),2) AS Average_Rating
FROM Reviews
GROUP BY Label
ORDER BY Average_Rating ASC;
"""

df = pd.read_sql_query(query, conn)

conn.close()

print("\nService Quality Findings:\n")
print(df)

total_reviews = df["Review_Count"].sum()

negative_categories = [
    "Communication",
    "Waiting Time",
    "Treatment",
    "Pricing",
    "Staff"
]

negative_count = df[
    df["Label"].isin(negative_categories)
]["Review_Count"].sum()

negative_percentage = round(
    (negative_count / total_reviews) * 100,
    2
)

print("\nTotal Reviews:")
print(total_reviews)

print("\nNegative Review Percentage:")
print(f"{negative_percentage}%")

df.to_csv(
    "reports/service_quality_analysis.csv",
    index=False
)

summary = pd.DataFrame({
    "Metric": [
        "Total Reviews",
        "Negative Review Percentage"
    ],
    "Value": [
        total_reviews,
        negative_percentage
    ]
})

summary.to_csv(
    "reports/service_quality_summary.csv",
    index=False
)

print("\nSaved:")
print("reports/service_quality_analysis.csv")
print("reports/service_quality_summary.csv")
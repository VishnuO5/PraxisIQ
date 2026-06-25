import sqlite3
import pandas as pd

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Patient_Id,
        Total_Visits
    FROM Patients
    """,
    conn
)

conn.close()

mean_visits = df["Total_Visits"].mean()
std_visits = df["Total_Visits"].std()

threshold = mean_visits + (2 * std_visits)

outliers = df[
    df["Total_Visits"] > threshold
]

print("\nVisit Outlier Detection")
print("=" * 40)

print(f"\nMean Visits: {mean_visits:.2f}")
print(f"Std Dev: {std_visits:.2f}")
print(f"Outlier Threshold: {threshold:.2f}")

print("\nOutlier Patients:")
print(outliers)
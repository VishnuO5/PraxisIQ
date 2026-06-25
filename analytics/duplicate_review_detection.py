import sqlite3
import pandas as pd

print("\nDuplicate Review Detection")
print("=" * 50)

# ==========================
# CONNECT DATABASE
# ==========================

conn = sqlite3.connect("PraxisIQ.db")

# ==========================
# FIND DUPLICATE REVIEWS
# ==========================

query = """
SELECT
    Review_Text,
    COUNT(*) AS Duplicate_Count
FROM Reviews
GROUP BY Review_Text
HAVING COUNT(*) > 1
ORDER BY Duplicate_Count DESC;
"""

df = pd.read_sql_query(query, conn)

conn.close()

# ==========================
# DISPLAY RESULTS
# ==========================

print("\nPotential Duplicate Reviews:\n")

print(df)

print("\nTotal Duplicate Review Patterns Found:")

print(len(df))

# ==========================
# SAVE RESULTS
# ==========================

df.to_csv(
    "reports/duplicate_review_detection.csv",
    index=False
)

print("\nSaved:")
print("reports/duplicate_review_detection.csv")
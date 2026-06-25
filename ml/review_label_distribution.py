import sqlite3
import pandas as pd

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT Label, COUNT(*) AS Count
    FROM Reviews
    GROUP BY Label
    ORDER BY Count DESC
    """,
    conn
)

print("\nReview Label Distribution\n")
print(df)

conn.close()
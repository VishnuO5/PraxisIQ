import sqlite3
import pandas as pd

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Review_Text,
        Label
    FROM Reviews
    ORDER BY RANDOM()
    LIMIT 30
    """,
    conn
)

print(df)

conn.close()
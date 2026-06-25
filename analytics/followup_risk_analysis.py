import sqlite3
import pandas as pd

conn = sqlite3.connect("PraxisIQ.db")

query = """
SELECT
    Patient_Id,
    Primary_Treatment,
    Follow_Up_Required,
    Follow_Up_Completed,
    Total_Visits
FROM Patients
WHERE
    Follow_Up_Required = 'Y'
    AND
    Follow_Up_Completed = 'N'
ORDER BY Total_Visits DESC;
"""

df = pd.read_sql_query(query, conn)

print("\nFollow-Up Risk Queue\n")
print(df)

print("\nTotal High-Risk Patients:")
print(len(df))

conn.close()
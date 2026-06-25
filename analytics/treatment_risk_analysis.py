import sqlite3
import pandas as pd

conn = sqlite3.connect("PraxisIQ.db")

query = """
SELECT
    Primary_Treatment,
    COUNT(*) AS High_Risk_Count
FROM Patients
WHERE
    Follow_Up_Required = 'Y'
    AND
    Follow_Up_Completed = 'N'
GROUP BY Primary_Treatment
ORDER BY High_Risk_Count DESC;
"""

df = pd.read_sql_query(query, conn)

print("\nTreatment Risk Analysis\n")
print(df)

conn.close()
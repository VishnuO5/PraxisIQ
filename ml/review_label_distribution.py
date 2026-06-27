import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, get_logger
log = get_logger(__name__)
import sqlite3
import pandas as pd

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query(
    """
    SELECT Label, COUNT(*) AS Count
    FROM Reviews
    GROUP BY Label
    ORDER BY Count DESC
    """,
    conn
)

log.info("Review Label Distribution")
log.info("\n%s", df.to_string())

conn.close()
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger
log = get_logger(__name__)
import sqlite3
import pandas as pd


log.info("\nDuplicate Review Detection")
log.info("=" * 50)

# ==========================
# CONNECT DATABASE
# ==========================

conn = sqlite3.connect(DB_PATH)

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

log.info("\nPotential Duplicate Reviews:\n")

log.info(df)

log.info("\nTotal Duplicate Review Patterns Found:")

log.info(len(df))

# ==========================
# SAVE RESULTS
# ==========================

df.to_csv(
    os.path.join(REPORTS_DIR, "duplicate_review_detection.csv"),
    index=False
)

log.info("\nSaved:")
log.info(os.path.join(REPORTS_DIR, "duplicate_review_detection.csv"))
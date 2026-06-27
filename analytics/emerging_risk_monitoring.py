"""
emerging_risk_monitoring.py
============================
Detects complaint categories that are accelerating over time.

Method:
  - Splits the review timeline into quarterly periods
  - Computes review volume per category per quarter
  - Calculates quarter-over-quarter (QoQ) growth rate
  - Flags any category with >50% QoQ growth in the most recent quarter
    as an "emerging risk"

Also computes a simple trend direction (Rising / Stable / Declining)
by comparing the last 2 quarters against the prior 2 quarters.

Outputs:
  - reports/emerging_risk_monitoring.csv   (quarterly breakdown)
  - reports/emerging_risk_summary.csv      (per-category trend summary)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger
log = get_logger(__name__)
import sqlite3
import pandas as pd




if not os.path.exists(DB_PATH):
    log.error(f"[ERROR] Database not found: {DB_PATH}")
    log.info("Run create_database.py first.")
    sys.exit(1)

os.makedirs(REPORTS_DIR, exist_ok=True)

log.info("\nEmerging Risk Monitoring")
log.info("=" * 60)

conn = sqlite3.connect(DB_PATH)

reviews = pd.read_sql_query(
    """
    SELECT
        Review_ID,
        Review_Date,
        Rating,
        Label
    FROM Reviews
    ORDER BY Review_Date
    """,
    conn,
)

conn.close()

reviews["Review_Date"] = pd.to_datetime(reviews["Review_Date"], format="mixed")
reviews["Quarter"]     = reviews["Review_Date"].dt.to_period("Q")

# ── COMPLAINT CATEGORIES ONLY ─────────────────────────────────────────────────

COMPLAINT_LABELS = ["Treatment", "Communication", "Waiting Time", "Pricing", "Staff"]
complaints = reviews[reviews["Label"].isin(COMPLAINT_LABELS)].copy()

log.info(f"\nTotal reviews          : {len(reviews)}")
log.info(f"Complaint reviews      : {len(complaints)}")
log.info(f"Date range             : {reviews['Review_Date'].min().date()} → {reviews['Review_Date'].max().date()}")

# ── QUARTERLY VOLUME PER CATEGORY ─────────────────────────────────────────────

quarterly = (
    complaints.groupby(["Quarter", "Label"])
    .agg(
        Count      = ("Review_ID", "count"),
        Avg_Rating = ("Rating",    "mean"),
    )
    .reset_index()
)
quarterly["Avg_Rating"] = quarterly["Avg_Rating"].round(2)
quarterly["Quarter_Str"] = quarterly["Quarter"].astype(str)

# Pivot for easy comparison
pivot = quarterly.pivot_table(
    index="Quarter", columns="Label", values="Count", fill_value=0
)

log.info(f"\nQuarters with complaint data: {len(pivot)}")

# ── QoQ GROWTH RATE ───────────────────────────────────────────────────────────

# Growth rate: (current - previous) / previous * 100
growth = pivot.pct_change() * 100
growth = growth.round(1).fillna(0)

log.info("\nQuarter-over-Quarter Growth Rate (%) by Category:")
log.info(growth.tail(8).to_string())

# ── TREND DIRECTION ───────────────────────────────────────────────────────────

trend_summary = []

for category in COMPLAINT_LABELS:
    if category not in pivot.columns:
        continue

    series = pivot[category]

    # Need at least 4 quarters for a meaningful trend comparison
    if len(series) < 4:
        recent_avg  = series.iloc[-2:].mean() if len(series) >= 2 else series.mean()
        earlier_avg = series.iloc[:-2].mean() if len(series) > 2 else recent_avg
    else:
        recent_avg  = series.iloc[-2:].mean()
        earlier_avg = series.iloc[-4:-2].mean()

    if earlier_avg == 0:
        trend_pct = 0.0
    else:
        trend_pct = round((recent_avg - earlier_avg) / earlier_avg * 100, 1)

    # Latest QoQ
    if len(growth) >= 1 and category in growth.columns:
        latest_qoq = growth[category].iloc[-1]
    else:
        latest_qoq = 0.0

    # Trend direction
    if trend_pct > 20:
        direction = "Rising ▲"
    elif trend_pct < -20:
        direction = "Declining ▼"
    else:
        direction = "Stable →"

    # Emerging risk flag
    emerging = latest_qoq > 50

    trend_summary.append({
        "Category":          category,
        "Total_Complaints":  int(series.sum()),
        "Recent_Avg_Qtr":    round(recent_avg, 1),
        "Earlier_Avg_Qtr":   round(earlier_avg, 1),
        "Trend_Pct":         trend_pct,
        "Latest_QoQ_Growth": latest_qoq,
        "Trend_Direction":   direction,
        "Emerging_Risk":     emerging,
    })

trend_df = pd.DataFrame(trend_summary).sort_values("Trend_Pct", ascending=False)

# ── PRINT RESULTS ─────────────────────────────────────────────────────────────

log.info("\nCategory Trend Summary:")
log.info(trend_df.to_string(index=False))

emerging = trend_df[trend_df["Emerging_Risk"]]
if len(emerging) > 0:
    log.warning(f"\n⚠  Emerging Risk Categories (latest QoQ > 50%): {len(emerging)}")
    for _, row in emerging.iterrows():
        log.info(f"   {row['Category']:20s} — QoQ: {row['Latest_QoQ_Growth']:+.1f}%  |  Trend: {row['Trend_Direction']}")
else:
    log.info("\nNo categories with >50% QoQ growth in the latest quarter.")

# ── SAVE ──────────────────────────────────────────────────────────────────────

quarterly_save = quarterly.sort_values(["Quarter_Str", "Label"])
quarterly_save.to_csv(os.path.join(REPORTS_DIR, "emerging_risk_monitoring.csv"), index=False)
trend_df.to_csv(os.path.join(REPORTS_DIR, "emerging_risk_summary.csv"), index=False)

log.info("\nSaved:")
log.info("  reports/emerging_risk_monitoring.csv")
log.info("  reports/emerging_risk_summary.csv")
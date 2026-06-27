"""
review_burst_detection.py
==========================
Detects abnormal surges in review submission volume.

Two complementary methods:

  Method 1 — Static threshold
    Flag any day where review count > mean + 2σ (same logic as visit outliers,
    consistent methodology across the project).

  Method 2 — Rolling 7-day window
    Flag days where the daily count exceeds 2× the trailing 7-day average.
    This catches gradual acceleration that the static threshold misses.

Also captures:
  - Which review categories dominated each burst day
  - Whether bursts skew negative (potential coordinated attack signal)

Outputs:
  - reports/review_burst_detection.csv
  - reports/review_burst_summary.csv
"""

import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    REPORTS_DIR,
    BURST_STATIC_SIGMA,
    BURST_ROLLING_WINDOW,
    BURST_ROLLING_MULTIPLIER,
    COMPLAINT_CATEGORIES,
    get_logger,
)

log = get_logger(__name__)

if not os.path.exists(DB_PATH):
    log.error("Database not found: %s", DB_PATH)
    log.error("Run create_database.py first.")
    sys.exit(1)

os.makedirs(REPORTS_DIR, exist_ok=True)

log.info("Review Burst Detection starting")

conn = sqlite3.connect(DB_PATH)
reviews = pd.read_sql_query(
    """
    SELECT Review_ID, Review_Date, Rating, Label
    FROM Reviews
    ORDER BY Review_Date
    """,
    conn,
)
conn.close()

reviews["Review_Date"] = pd.to_datetime(reviews["Review_Date"], format="mixed")
reviews["Review_Day"]  = reviews["Review_Date"].dt.date

# ── DAILY VOLUME ──────────────────────────────────────────────────────────────

daily = (
    reviews.groupby("Review_Day")
    .agg(
        Review_Count   = ("Review_ID", "count"),
        Avg_Rating     = ("Rating",    "mean"),
        Negative_Count = ("Label",     lambda x: x.isin(COMPLAINT_CATEGORIES).sum()),
    )
    .reset_index()
)

daily["Review_Day"]    = pd.to_datetime(daily["Review_Day"])
daily["Negative_Rate"] = (daily["Negative_Count"] / daily["Review_Count"] * 100).round(1)

# ── METHOD 1: STATIC THRESHOLD (mean + Nσ) ────────────────────────────────────

mean_daily       = daily["Review_Count"].mean()
std_daily        = daily["Review_Count"].std()
static_threshold = mean_daily + BURST_STATIC_SIGMA * std_daily

daily["Flag_Static"] = daily["Review_Count"] > static_threshold

# ── METHOD 2: ROLLING WINDOW ──────────────────────────────────────────────────

daily = daily.sort_values("Review_Day").reset_index(drop=True)
daily["Rolling_7d_Avg"] = (
    daily["Review_Count"]
    .rolling(window=BURST_ROLLING_WINDOW, min_periods=1)
    .mean()
    .shift(1)
    .fillna(daily["Review_Count"].mean())
    .round(2)
)

daily["Flag_Rolling"] = daily["Review_Count"] > (daily["Rolling_7d_Avg"] * BURST_ROLLING_MULTIPLIER)

# ── COMBINE FLAGS ─────────────────────────────────────────────────────────────

daily["Burst_Detected"] = daily["Flag_Static"] | daily["Flag_Rolling"]

# ── DOMINANT CATEGORY PER DAY ─────────────────────────────────────────────────

dominant = (
    reviews.assign(Review_Day=reviews["Review_Date"].dt.date)
    .groupby(["Review_Day", "Label"])
    .size()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
    .drop_duplicates("Review_Day")
    .rename(columns={"Label": "Dominant_Category"})
)
dominant["Review_Day"] = pd.to_datetime(dominant["Review_Day"])

daily = daily.merge(dominant[["Review_Day", "Dominant_Category"]], on="Review_Day", how="left")

# ── RESULTS ───────────────────────────────────────────────────────────────────

bursts = daily[daily["Burst_Detected"]].sort_values("Review_Count", ascending=False)

log.info("Date range    : %s → %s", daily["Review_Day"].min().date(), daily["Review_Day"].max().date())
log.info("Total days    : %d", len(daily))
log.info("Mean per day  : %.2f", mean_daily)
log.info("Std deviation : %.2f", std_daily)
log.info("Static threshold (mean+%dσ): %.2f reviews/day", BURST_STATIC_SIGMA, static_threshold)
log.info("Rolling window: %d days · multiplier: %.1f×", BURST_ROLLING_WINDOW, BURST_ROLLING_MULTIPLIER)
log.info("Burst days detected  : %d", len(bursts))
log.info("  Via static threshold : %d", daily["Flag_Static"].sum())
log.info("  Via rolling window   : %d", daily["Flag_Rolling"].sum())

if len(bursts) > 0:
    log.info("Burst Days Detail:")
    display_cols = [
        "Review_Day", "Review_Count", "Avg_Rating",
        "Negative_Rate", "Dominant_Category",
        "Rolling_7d_Avg", "Flag_Static", "Flag_Rolling"
    ]
    log.info("\n%s", bursts[display_cols].to_string(index=False))

    negative_bursts = bursts[bursts["Negative_Rate"] > 50]
    if len(negative_bursts) > 0:
        print(f"\n⚠  Negative-skewed bursts (>50% negative reviews): {len(negative_bursts)}")
        log.warning("These warrant priority investigation — potential coordinated negative campaign.")
    else:
        log.info("No negative-skewed bursts detected.")
else:
    log.info("No burst days detected.")

# ── MONTHLY TREND ─────────────────────────────────────────────────────────────

monthly = (
    reviews.groupby(reviews["Review_Date"].dt.to_period("M"))
    .agg(Monthly_Count=("Review_ID", "count"), Avg_Rating=("Rating", "mean"))
    .reset_index()
)
monthly["Review_Date"] = monthly["Review_Date"].astype(str)
monthly["Avg_Rating"]  = monthly["Avg_Rating"].round(2)

log.info("Monthly Review Volume:")
log.info("\n%s", monthly.to_string(index=False))

# ── SAVE ──────────────────────────────────────────────────────────────────────

save_cols = [
    "Review_Day", "Review_Count", "Avg_Rating", "Negative_Count",
    "Negative_Rate", "Dominant_Category", "Rolling_7d_Avg",
    "Flag_Static", "Flag_Rolling", "Burst_Detected"
]
daily[save_cols].to_csv(os.path.join(REPORTS_DIR, "review_burst_detection.csv"), index=False)

summary = pd.DataFrame({
    "Metric": [
        "Total Review Days", "Mean Reviews Per Day",
        f"Static Threshold (mean+{BURST_STATIC_SIGMA}σ)",
        "Burst Days (static)", "Burst Days (rolling 7d)",
        "Total Burst Days", "Negative-Skewed Bursts",
    ],
    "Value": [
        len(daily), round(mean_daily, 2), round(static_threshold, 2),
        int(daily["Flag_Static"].sum()), int(daily["Flag_Rolling"].sum()),
        int(len(bursts)), int(len(bursts[bursts["Negative_Rate"] > 50])),
    ]
})
summary.to_csv(os.path.join(REPORTS_DIR, "review_burst_summary.csv"), index=False)

log.info("Saved outputs:")
log.info("  %s/review_burst_detection.csv", REPORTS_DIR)
log.info("  %s/review_burst_summary.csv", REPORTS_DIR)
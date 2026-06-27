"""
service_quality_analysis.py
============================
Analyses service quality across complaint categories with trend analysis
and time-period comparisons.

Goes beyond simple GROUP BY averages to identify:
  - Which categories are getting worse over time (rising complaint volume)
  - Quarter-over-quarter trend direction per category
  - Whether low-rated categories are improving or declining
  - Service quality score — composite of volume, rating, and trend

Outputs:
  - reports/service_quality_analysis.csv   (per-category metrics)
  - reports/service_quality_summary.csv    (trend summary)
  - reports/service_quality_trends.csv     (quarterly breakdown)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger, COMPLAINT_CATEGORIES

log = get_logger(__name__)

import sqlite3
import pandas as pd
import numpy as np
from scipy import stats

# ── PRE-FLIGHT ────────────────────────────────────────────────────────────────

if not os.path.exists(DB_PATH):
    log.error(f"Database not found: {DB_PATH}")
    sys.exit(1)

os.makedirs(REPORTS_DIR, exist_ok=True)
log.info("Service Quality Analysis — starting")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────

conn = sqlite3.connect(DB_PATH)
reviews = pd.read_sql_query("""
    SELECT
        Review_ID,
        Reviewer_Name,
        Rating,
        Review_Date,
        Label,
        Review_Text
    FROM Reviews
""", conn)
conn.close()

reviews["Review_Date"] = pd.to_datetime(reviews["Review_Date"], errors="coerce")
reviews["Year"]        = reviews["Review_Date"].dt.year
reviews["Quarter"]     = reviews["Review_Date"].dt.to_period("Q").astype(str)
reviews["YearMonth"]   = reviews["Review_Date"].dt.to_period("M").astype(str)

log.info(f"Loaded {len(reviews)} reviews spanning {reviews['Year'].min()}–{reviews['Year'].max()}")

# ── STEP 1: OVERALL CATEGORY METRICS ─────────────────────────────────────────

overall = (
    reviews.groupby("Label")
    .agg(
        Review_Count   = ("Review_ID",   "count"),
        Avg_Rating     = ("Rating",       "mean"),
        Min_Rating     = ("Rating",       "min"),
        Max_Rating     = ("Rating",       "max"),
        One_Star_Count = ("Rating",       lambda x: (x == 1).sum()),
        Five_Star_Count= ("Rating",       lambda x: (x == 5).sum()),
        Std_Rating     = ("Rating",       "std"),
    )
    .reset_index()
)

overall["Avg_Rating"]      = overall["Avg_Rating"].round(2)
overall["Std_Rating"]      = overall["Std_Rating"].round(2)
overall["One_Star_Pct"]    = (overall["One_Star_Count"] / overall["Review_Count"] * 100).round(1)
overall["Share_Of_Total"]  = (overall["Review_Count"] / len(reviews) * 100).round(1)

# ── STEP 2: QUARTERLY TREND PER CATEGORY ─────────────────────────────────────

quarterly = (
    reviews.groupby(["Quarter", "Label"])
    .agg(
        Count      = ("Review_ID", "count"),
        Avg_Rating = ("Rating",    "mean"),
    )
    .reset_index()
)
quarterly["Avg_Rating"] = quarterly["Avg_Rating"].round(2)
quarterly = quarterly.sort_values(["Label", "Quarter"])

# ── STEP 3: TREND DIRECTION PER CATEGORY ─────────────────────────────────────
# Compare last 2 quarters vs prior 2 quarters for each category

def get_trend(group):
    """
    Returns trend direction based on complaint volume change.
    Compares average quarterly volume in last 2 quarters vs prior 2 quarters.
    """
    group = group.sort_values("Quarter")
    if len(group) < 3:
        return "Insufficient Data"

    recent    = group.tail(2)["Count"].mean()
    prior     = group.iloc[:-2]["Count"].mean() if len(group) > 2 else recent

    if prior == 0:
        return "New Category"
    change_pct = (recent - prior) / prior * 100

    if change_pct >= 30:
        return "RISING ↑"
    elif change_pct >= 10:
        return "INCREASING"
    elif change_pct <= -30:
        return "DECLINING ↓"
    elif change_pct <= -10:
        return "DECREASING"
    else:
        return "STABLE"

trend_map = (
    quarterly
    .groupby("Label")
    .apply(get_trend)
    .reset_index()
    .rename(columns={0: "Trend_Direction"})
)

# ── STEP 4: LINEAR REGRESSION ON RATING OVER TIME ────────────────────────────
# Is the average rating for each category improving or worsening?

def rating_slope(group):
    """Returns slope of rating over time (positive = improving)."""
    group = group.sort_values("Quarter")
    if len(group) < 3:
        return None
    x = np.arange(len(group))
    y = group["Avg_Rating"].values
    slope, _, r, p, _ = stats.linregress(x, y)
    return round(slope, 4)

rating_slopes = (
    quarterly
    .groupby("Label")
    .apply(rating_slope)
    .reset_index()
    .rename(columns={0: "Rating_Slope"})
)

rating_slopes["Rating_Direction"] = rating_slopes["Rating_Slope"].apply(
    lambda s: "Improving" if s and s > 0.01
    else "Worsening" if s and s < -0.01
    else "Stable" if s is not None
    else "Insufficient Data"
)

# ── STEP 5: COMPOSITE SERVICE QUALITY SCORE ───────────────────────────────────
# Higher score = worse service quality (more attention needed)
# Score = (5 - Avg_Rating) * log(Review_Count + 1) * one_star_weight

overall["Quality_Risk_Score"] = (
    (5 - overall["Avg_Rating"])
    * np.log1p(overall["Review_Count"])
    * (1 + overall["One_Star_Pct"] / 100)
).round(2)

# ── COMBINE ───────────────────────────────────────────────────────────────────

final = (
    overall
    .merge(trend_map,     on="Label", how="left")
    .merge(rating_slopes, on="Label", how="left")
)

final = final.sort_values("Quality_Risk_Score", ascending=False).reset_index(drop=True)

# ── PRINT RESULTS ─────────────────────────────────────────────────────────────

print("\nService Quality Analysis")
print("=" * 80)
print(f"\n{'Category':<16} {'Count':>6} {'Avg★':>6} {'1★%':>6} {'Trend':>12} {'Rating Dir':>12} {'Risk Score':>11}")
print("-" * 80)

for _, row in final.iterrows():
    trend     = row.get("Trend_Direction", "N/A") or "N/A"
    rating_d  = row.get("Rating_Direction", "N/A") or "N/A"
    print(
        f"{row['Label']:<16} "
        f"{int(row['Review_Count']):>6} "
        f"{row['Avg_Rating']:>6.2f} "
        f"{row['One_Star_Pct']:>5.1f}% "
        f"{trend:>12} "
        f"{rating_d:>12} "
        f"{row['Quality_Risk_Score']:>11.2f}"
    )

print("\n── Key Findings ──")

complaints = final[final["Label"].isin(COMPLAINT_CATEGORIES)]
if not complaints.empty:
    worst = complaints.iloc[0]
    print(f"Highest risk category : {worst['Label']} "
          f"(score {worst['Quality_Risk_Score']:.2f}, "
          f"avg rating {worst['Avg_Rating']:.2f}★)")

rising = final[final["Trend_Direction"] == "RISING ↑"]
if not rising.empty:
    print(f"Rising complaint categories: {', '.join(rising['Label'].tolist())}")
else:
    print("No rapidly rising complaint categories detected.")

worsening = final[final["Rating_Direction"] == "Worsening"]
if not worsening.empty:
    print(f"Worsening rating trend : {', '.join(worsening['Label'].tolist())}")
else:
    print("No categories showing worsening rating trend.")

# ── SAVE ──────────────────────────────────────────────────────────────────────

final.to_csv(os.path.join(REPORTS_DIR, "service_quality_analysis.csv"), index=False)
quarterly.to_csv(os.path.join(REPORTS_DIR, "service_quality_trends.csv"), index=False)

summary = final[["Label", "Review_Count", "Avg_Rating", "One_Star_Pct",
                  "Trend_Direction", "Rating_Direction", "Quality_Risk_Score"]]
summary.to_csv(os.path.join(REPORTS_DIR, "service_quality_summary.csv"), index=False)

log.info("Saved: reports/service_quality_analysis.csv")
log.info("Saved: reports/service_quality_trends.csv")
log.info("Saved: reports/service_quality_summary.csv")
log.info("Pipeline complete.")
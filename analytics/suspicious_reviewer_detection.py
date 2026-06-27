"""
suspicious_reviewer_detection.py
=================================
Detects potentially suspicious reviewer behaviour using four signals:

  1. Velocity      — multiple reviews submitted on the same day
  2. Rating extreme — reviewer gives only 1-star or only 5-star ratings
                      across all their reviews (no variance)
  3. Repeat volume  — reviewer has submitted 3+ reviews total
  4. Sentiment flip — reviewer gave both very low (≤2) AND very high (≥4)
                      ratings (contradictory behaviour pattern)

Each signal contributes to a Suspicion_Score (0–4).
Score ≥ 2 → flagged for manual review.

Output:
  - reports/suspicious_reviewer_detection.csv
  - reports/suspicious_reviewer_summary.csv
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

log.info("\nSuspicious Reviewer Detection")
log.info("=" * 60)

conn = sqlite3.connect(DB_PATH)

reviews = pd.read_sql_query(
    """
    SELECT
        Review_ID,
        Reviewer_Name,
        Review_Date,
        Rating,
        Label,
        Review_Text
    FROM Reviews
    """,
    conn,
)

conn.close()

reviews["Review_Date"] = pd.to_datetime(reviews["Review_Date"], format="mixed")
reviews["Review_Day"]  = reviews["Review_Date"].dt.date

total_reviews = len(reviews)
log.info(f"\nTotal reviews loaded: {total_reviews}")

# ── PER-REVIEWER AGGREGATION ──────────────────────────────────────────────────

agg = reviews.groupby("Reviewer_Name").agg(
    Review_Count      = ("Review_ID",    "count"),
    Avg_Rating        = ("Rating",        "mean"),
    Min_Rating        = ("Rating",        "min"),
    Max_Rating        = ("Rating",        "max"),
    Unique_Days       = ("Review_Day",    "nunique"),
    Unique_Labels     = ("Label",         "nunique"),
).reset_index()

agg["Rating_Range"] = agg["Max_Rating"] - agg["Min_Rating"]

# ── SIGNAL FLAGS ──────────────────────────────────────────────────────────────

# Signal 1: Same-day velocity — submitted >1 review on the same calendar day
same_day = (
    reviews.groupby(["Reviewer_Name", "Review_Day"])
    .size()
    .reset_index(name="Reviews_On_Day")
)
max_same_day = same_day.groupby("Reviewer_Name")["Reviews_On_Day"].max().reset_index()
max_same_day.columns = ["Reviewer_Name", "Max_Reviews_Same_Day"]

agg = agg.merge(max_same_day, on="Reviewer_Name", how="left")
agg["Flag_Velocity"] = (agg["Max_Reviews_Same_Day"] > 1).astype(int)

# Signal 2: No rating variance — all reviews are identical score (only 1-star or only 5-star)
agg["Flag_No_Variance"] = (
    (agg["Review_Count"] > 1) & (agg["Rating_Range"] == 0)
).astype(int)

# Signal 3: High repeat volume — 3 or more reviews from one reviewer
agg["Flag_High_Volume"] = (agg["Review_Count"] >= 3).astype(int)

# Signal 4: Sentiment flip — same reviewer gave both ≤2 AND ≥4 ratings
flip_reviewers = (
    reviews.groupby("Reviewer_Name")
    .apply(lambda g: (g["Rating"] <= 2).any() and (g["Rating"] >= 4).any())
    .reset_index()
)
flip_reviewers.columns = ["Reviewer_Name", "Flag_Sentiment_Flip"]
flip_reviewers["Flag_Sentiment_Flip"] = flip_reviewers["Flag_Sentiment_Flip"].astype(int)

agg = agg.merge(flip_reviewers, on="Reviewer_Name", how="left")

# ── SUSPICION SCORE ───────────────────────────────────────────────────────────

agg["Suspicion_Score"] = (
    agg["Flag_Velocity"] +
    agg["Flag_No_Variance"] +
    agg["Flag_High_Volume"] +
    agg["Flag_Sentiment_Flip"]
)

def suspicion_tier(score):
    if score >= 3:
        return "High — Manual Review Required"
    elif score == 2:
        return "Medium — Monitor"
    elif score == 1:
        return "Low — Noted"
    else:
        return "Clean"

agg["Suspicion_Tier"] = agg["Suspicion_Score"].apply(suspicion_tier)

# ── RESULTS ───────────────────────────────────────────────────────────────────

flagged = agg[agg["Suspicion_Score"] >= 2].sort_values(
    "Suspicion_Score", ascending=False
).reset_index(drop=True)

log.info(f"\nReviewers analysed       : {len(agg)}")
log.info(f"Clean (score 0)          : {len(agg[agg['Suspicion_Score'] == 0])}")
log.info(f"Low suspicion (score 1)  : {len(agg[agg['Suspicion_Score'] == 1])}")
log.info(f"Medium suspicion (score 2): {len(agg[agg['Suspicion_Score'] == 2])}")
log.info(f"High suspicion  (score 3+): {len(agg[agg['Suspicion_Score'] >= 3])}")

log.info(f"\nFlagged for review (score ≥ 2): {len(flagged)}")

if len(flagged) > 0:
    display_cols = [
        "Reviewer_Name", "Review_Count", "Avg_Rating",
        "Rating_Range", "Max_Reviews_Same_Day",
        "Flag_Velocity", "Flag_No_Variance",
        "Flag_High_Volume", "Flag_Sentiment_Flip",
        "Suspicion_Score", "Suspicion_Tier"
    ]
    log.info("\nFlagged Reviewers:\n")
    log.info(flagged[display_cols].to_string(index=False))
else:
    log.info("\nNo reviewers flagged at score ≥ 2.")

# ── SIGNAL BREAKDOWN ──────────────────────────────────────────────────────────

log.info("\nSignal Breakdown (how many reviewers triggered each flag):")
log.info(f"  Velocity (same-day multiple reviews) : {agg['Flag_Velocity'].sum()}")
log.info(f"  No rating variance (all same score)  : {agg['Flag_No_Variance'].sum()}")
log.info(f"  High volume (3+ reviews)             : {agg['Flag_High_Volume'].sum()}")
log.info(f"  Sentiment flip (low AND high ratings): {agg['Flag_Sentiment_Flip'].sum()}")

# ── SAVE ──────────────────────────────────────────────────────────────────────

save_cols = [
    "Reviewer_Name", "Review_Count", "Avg_Rating", "Rating_Range",
    "Max_Reviews_Same_Day", "Unique_Days", "Unique_Labels",
    "Flag_Velocity", "Flag_No_Variance", "Flag_High_Volume", "Flag_Sentiment_Flip",
    "Suspicion_Score", "Suspicion_Tier"
]

agg[save_cols].sort_values("Suspicion_Score", ascending=False).to_csv(
    os.path.join(REPORTS_DIR, "suspicious_reviewer_detection.csv"), index=False
)

summary = pd.DataFrame({
    "Metric": [
        "Total Reviewers",
        "Flagged (score ≥ 2)",
        "Flag Rate (%)",
        "Velocity Flags",
        "No Variance Flags",
        "High Volume Flags",
        "Sentiment Flip Flags",
    ],
    "Value": [
        len(agg),
        len(flagged),
        round(len(flagged) / len(agg) * 100, 1),
        int(agg["Flag_Velocity"].sum()),
        int(agg["Flag_No_Variance"].sum()),
        int(agg["Flag_High_Volume"].sum()),
        int(agg["Flag_Sentiment_Flip"].sum()),
    ]
})

summary.to_csv(os.path.join(REPORTS_DIR, "suspicious_reviewer_summary.csv"), index=False)

log.info("\nSaved:")
log.info("  reports/suspicious_reviewer_detection.csv")
log.info("  reports/suspicious_reviewer_summary.csv")
"""
account_risk_scoring.py
========================
Account-level enforcement scoring — Phase 2 (content-level → account-level
enforcement).

Everything else in this project scores individual reviews. This script is
the one place that scores *accounts* (Reviewer_Name) — identifying and
acting on disruptive users, not just disruptive content.

It does not re-derive suspicion signals from scratch — it reuses two
pipelines that already exist and already ran successfully:
  - analytics/suspicious_reviewer_detection.py  -> reports/suspicious_reviewer_detection.csv
  - analytics/review_burst_detection.py         -> reports/review_burst_detection.csv

and adds exactly one new idea: mapping a composite account score to an
enforcement action (None -> Warning -> Restricted -> Suspended), the way a
real strikes ladder works. Weights and thresholds are defined once, in
config.py (ACCOUNT_RISK_WEIGHTS / ACCOUNT_STRIKE_THRESHOLDS), not here.

Output: reports/account_risk_scores.csv — one row per Reviewer_Name.

Run standalone:
    python analytics/account_risk_scoring.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    REPORTS_DIR,
    ACCOUNT_RISK_WEIGHTS,
    ACCOUNT_STRIKE_THRESHOLDS,
    ACCOUNT_ACTION_DESCRIPTIONS,
    ACCOUNT_LOW_RATING_AVG_THRESHOLD,
    get_logger,
)

log = get_logger(__name__)


def _action_for_score(score: float) -> str:
    """Map a composite account risk score to an enforcement action, using
    the thresholds in config.ACCOUNT_STRIKE_THRESHOLDS. Highest tier that
    the score clears wins (Suspended > Restricted > Warning > None)."""
    if score >= ACCOUNT_STRIKE_THRESHOLDS["Suspended"]:
        return "Suspended"
    if score >= ACCOUNT_STRIKE_THRESHOLDS["Restricted"]:
        return "Restricted"
    if score >= ACCOUNT_STRIKE_THRESHOLDS["Warning"]:
        return "Warning"
    return "None"


def build_account_risk_scores() -> pd.DataFrame:
    suspicious_path = os.path.join(REPORTS_DIR, "suspicious_reviewer_detection.csv")
    burst_path = os.path.join(REPORTS_DIR, "review_burst_detection.csv")

    if not os.path.exists(suspicious_path) or not os.path.exists(burst_path):
        raise FileNotFoundError(
            "account_risk_scoring.py depends on suspicious_reviewer_detection.csv "
            "and review_burst_detection.csv. Run run_all.py first (or the two "
            "underlying scripts) so those reports exist."
        )

    accounts = pd.read_csv(suspicious_path)
    burst = pd.read_csv(burst_path)

    burst_days = set(
        pd.to_datetime(burst.loc[burst["Burst_Detected"] == True, "Review_Day"]).dt.strftime("%Y-%m-%d")
    )
    log.info("Loaded %d confirmed burst days for overlap check", len(burst_days))

    import sqlite3
    con = sqlite3.connect(DB_PATH)
    reviews = pd.read_sql("SELECT Reviewer_Name, Review_Date FROM Reviews", con)
    con.close()
    reviews["Review_Date"] = pd.to_datetime(reviews["Review_Date"]).dt.strftime("%Y-%m-%d")
    reviews["On_Burst_Day"] = reviews["Review_Date"].isin(burst_days)
    burst_overlap_by_reviewer = (
        reviews.groupby("Reviewer_Name")["On_Burst_Day"].any().rename("Burst_Day_Overlap")
    )

    accounts = accounts.merge(burst_overlap_by_reviewer, on="Reviewer_Name", how="left")
    accounts["Burst_Day_Overlap"] = accounts["Burst_Day_Overlap"].fillna(False)

    accounts["Flag_Low_Avg_Rating"] = accounts["Avg_Rating"] <= ACCOUNT_LOW_RATING_AVG_THRESHOLD

    accounts["Account_Risk_Score"] = (
        (accounts["Review_Count"] - 1).clip(lower=0) * ACCOUNT_RISK_WEIGHTS["review_count"]
        + accounts["Flag_Low_Avg_Rating"].astype(int) * ACCOUNT_RISK_WEIGHTS["avg_low_rating_flag"]
        + accounts["Flag_No_Variance"].astype(int) * ACCOUNT_RISK_WEIGHTS["rating_variance_low"]
        + accounts["Burst_Day_Overlap"].astype(int) * ACCOUNT_RISK_WEIGHTS["burst_day_overlap"]
    ).round(2)

    accounts["Enforcement_Action"] = accounts["Account_Risk_Score"].apply(_action_for_score)
    accounts["Action_Description"] = accounts["Enforcement_Action"].map(ACCOUNT_ACTION_DESCRIPTIONS)

    accounts = accounts.sort_values("Account_Risk_Score", ascending=False).reset_index(drop=True)

    cols = [
        "Reviewer_Name", "Review_Count", "Avg_Rating", "Flag_Low_Avg_Rating",
        "Flag_No_Variance", "Burst_Day_Overlap", "Account_Risk_Score",
        "Enforcement_Action", "Action_Description",
    ]
    return accounts[cols]


def main():
    log.info("Building account-level enforcement risk scores...")
    result = build_account_risk_scores()

    out_path = os.path.join(REPORTS_DIR, "account_risk_scores.csv")
    result.to_csv(out_path, index=False)

    action_counts = result["Enforcement_Action"].value_counts().to_dict()
    log.info("Accounts scored: %d", len(result))
    log.info("Enforcement action breakdown: %s", action_counts)
    log.info("Saved -> %s", out_path)


if __name__ == "__main__":
    main()

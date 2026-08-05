"""
appeals_workflow.py
====================
Appeals & reinstatement workflow — Phase 3 (detection → enforcement →
appeal lifecycle).

Every other module in this project stops at detection: a review gets
scored, tiered, and queued. Real content-enforcement systems don't stop
there — flagged content/users can appeal, and some appeals get overturned.
This module adds that missing half of the lifecycle:

    Detection -> Enforcement -> Appeal -> Reinstatement

IMPORTANT — MODELED SIMULATION, NOT REAL DATA:
This dataset has no real appeals history (no user ever actually appealed
anything here — it's a synthetic dental-review dataset). The appeal/
overturn rates are documented assumptions defined once in config.py
(APPEAL_RATE_ASSUMPTION, APPEAL_OVERTURN_RATE_ASSUMPTION) and sampled
deterministically (APPEAL_RANDOM_STATE) so results are reproducible.
This script demonstrates the *mechanism* — how an appeals queue would be
built, tracked, and reported on — not a claimed real-world outcome. Every
output file and the dashboard section built from it must say so.

Output:
    reports/appeals_queue.csv    — one row per review, appeal status/outcome
    reports/appeals_summary.csv  — Metric,Value summary (same convention as
                                    review_burst_summary.csv etc.)

Run standalone:
    python trust_safety/appeals_workflow.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    REPORTS_DIR,
    APPEAL_ELIGIBLE_SEVERITIES,
    APPEAL_RATE_ASSUMPTION,
    APPEAL_OVERTURN_RATE_ASSUMPTION,
    APPEAL_RANDOM_STATE,
    get_logger,
)

log = get_logger(__name__)

NOT_ELIGIBLE = "Not Eligible"
NOT_APPEALED = "Not Appealed"
APPEALED = "Appealed"
OUTCOME_NA = "N/A"
OUTCOME_UPHELD = "Upheld"
OUTCOME_OVERTURNED = "Overturned"


def build_appeals_queue() -> pd.DataFrame:
    src_path = os.path.join(REPORTS_DIR, "risk_escalation_queue.csv")
    if not os.path.exists(src_path):
        raise FileNotFoundError(
            "appeals_workflow.py depends on reports/risk_escalation_queue.csv. "
            "Run trust_safety/trust_safety_pipeline.py (or run_all.py) first."
        )

    queue = pd.read_csv(src_path)
    rng = np.random.RandomState(APPEAL_RANDOM_STATE)

    queue["Appeal_Status"] = NOT_ELIGIBLE
    queue["Appeal_Outcome"] = OUTCOME_NA

    eligible_mask = queue["Severity"].isin(APPEAL_ELIGIBLE_SEVERITIES)
    eligible_idx = queue.index[eligible_mask].to_numpy()

    n_eligible = len(eligible_idx)
    n_appealed = int(round(n_eligible * APPEAL_RATE_ASSUMPTION))
    appealed_idx = rng.choice(eligible_idx, size=n_appealed, replace=False) if n_appealed > 0 else np.array([], dtype=int)

    queue.loc[eligible_idx, "Appeal_Status"] = NOT_APPEALED
    queue.loc[appealed_idx, "Appeal_Status"] = APPEALED
    queue.loc[appealed_idx, "Appeal_Outcome"] = OUTCOME_UPHELD  # default; overturned subset overwrites below

    n_overturned = int(round(n_appealed * APPEAL_OVERTURN_RATE_ASSUMPTION))
    overturned_idx = rng.choice(appealed_idx, size=n_overturned, replace=False) if n_overturned > 0 else np.array([], dtype=int)
    queue.loc[overturned_idx, "Appeal_Outcome"] = OUTCOME_OVERTURNED

    queue["Data_Note"] = "MODELED SIMULATION — appeal/overturn assumptions from config.py, not real appeals data"

    cols = [
        "Case_ID", "Review_ID", "Reviewer_Name", "Review_Date", "Severity",
        "Priority", "Risk_Score", "Appeal_Status", "Appeal_Outcome", "Data_Note",
    ]
    cols = [c for c in cols if c in queue.columns]
    return queue[cols]


def build_summary(appeals: pd.DataFrame) -> pd.DataFrame:
    eligible = appeals[appeals["Appeal_Status"] != NOT_ELIGIBLE]
    appealed = appeals[appeals["Appeal_Status"] == APPEALED]
    overturned = appealed[appealed["Appeal_Outcome"] == OUTCOME_OVERTURNED]

    n_eligible = len(eligible)
    n_appealed = len(appealed)
    n_overturned = len(overturned)

    rows = [
        ("Eligible for Appeal (Critical/High)", n_eligible),
        ("Appealed (modeled)", n_appealed),
        ("Appeal Rate Used (%)", round(APPEAL_RATE_ASSUMPTION * 100, 1)),
        ("Overturned on Appeal (modeled)", n_overturned),
        ("Overturn Rate Used (%)", round(APPEAL_OVERTURN_RATE_ASSUMPTION * 100, 1)),
        ("Upheld on Appeal (modeled)", n_appealed - n_overturned),
        ("Net Cases Reinstated (modeled)", n_overturned),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def main():
    log.info("Building appeals & reinstatement workflow (MODELED SIMULATION)...")
    appeals = build_appeals_queue()
    summary = build_summary(appeals)

    appeals_path = os.path.join(REPORTS_DIR, "appeals_queue.csv")
    summary_path = os.path.join(REPORTS_DIR, "appeals_summary.csv")
    appeals.to_csv(appeals_path, index=False)
    summary.to_csv(summary_path, index=False)

    log.info("Eligible: %d | Appealed: %d | Overturned: %d",
              (appeals["Appeal_Status"] != NOT_ELIGIBLE).sum(),
              (appeals["Appeal_Status"] == APPEALED).sum(),
              (appeals["Appeal_Outcome"] == OUTCOME_OVERTURNED).sum())
    log.info("Saved -> %s", appeals_path)
    log.info("Saved -> %s", summary_path)


if __name__ == "__main__":
    main()

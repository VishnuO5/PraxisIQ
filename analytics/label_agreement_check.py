"""
label_agreement_check.py
==========================
Label agreement (Cohen's Kappa) exercise — Phase 4 (Enforcement Detection
Analyst alignment).

FINDINGS.md already discloses honestly that all 300 reviews were labeled
by a single annotator, with no inter-annotator agreement check. This
script is the fix for that documented limitation — but it does NOT
fabricate a second annotator's labels. That would mean presenting made-up
data as if it were a real reliability check, which defeats the entire
point of the exercise (and breaks the "real data only" rule this project
holds itself to).

Instead this is a two-step, honest tool:

  Step 1 (`generate_relabel_sample`) — deterministically samples N reviews
  from the real dataset and writes a blank template with a
  'Second_Pass_Label' column for a human (you) to fill in independently,
  ideally on a different day than the original labeling pass, without
  looking at the original Label column.

  Step 2 (`compute_agreement`) — once that file has been filled in by
  hand, reads it back and computes Cohen's Kappa between the original
  Label and Second_Pass_Label columns.

Until Step 2's input exists, main() only performs Step 1 and says so
plainly — it will not print a fake kappa score.

Run standalone:
    python analytics/label_agreement_check.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger

log = get_logger(__name__)

SAMPLE_SIZE = 30
RELABEL_RANDOM_STATE = 42  # same convention as ML/LLM splits elsewhere in the project
RELABEL_SAMPLE_PATH = os.path.join(REPORTS_DIR, "relabel_sample_for_review.csv")
AGREEMENT_OUTPUT_PATH = os.path.join(REPORTS_DIR, "label_agreement.csv")

VALID_LABELS = ["Treatment", "Communication", "Waiting Time", "Pricing", "Staff", "Neutral", "Positive"]


def generate_relabel_sample() -> pd.DataFrame:
    """Step 1 — sample real reviews and write a blank second-pass template.
    Deterministic (RELABEL_RANDOM_STATE) so the same 30 reviews are sampled
    every time this is run, even before it's been filled in."""
    import sqlite3
    con = sqlite3.connect(DB_PATH)
    reviews = pd.read_sql("SELECT Review_ID, Review_Text, Label FROM Reviews", con)
    con.close()

    sample = reviews.sample(n=SAMPLE_SIZE, random_state=RELABEL_RANDOM_STATE).reset_index(drop=True)
    sample = sample.rename(columns={"Label": "Original_Label"})
    sample["Second_Pass_Label"] = ""  # blank — to be filled in by hand, independently

    sample.to_csv(RELABEL_SAMPLE_PATH, index=False)
    log.info("Wrote blank relabel template (%d reviews) -> %s", len(sample), RELABEL_SAMPLE_PATH)
    log.info("Valid labels: %s", ", ".join(VALID_LABELS))
    log.info("Fill in Second_Pass_Label for each row without looking at Original_Label, "
              "then re-run this script to compute Cohen's Kappa.")
    return sample


def compute_agreement() -> pd.DataFrame:
    """Step 2 — only runs once RELABEL_SAMPLE_PATH has real Second_Pass_Label
    values filled in by hand. Returns None and logs instructions if not."""
    from sklearn.metrics import cohen_kappa_score

    if not os.path.exists(RELABEL_SAMPLE_PATH):
        log.warning("No relabel sample found yet. Run generate_relabel_sample() first.")
        return None

    df = pd.read_csv(RELABEL_SAMPLE_PATH)
    filled = df[df["Second_Pass_Label"].notna() & (df["Second_Pass_Label"].astype(str).str.strip() != "")]

    if len(filled) == 0:
        log.warning(
            "%s exists but Second_Pass_Label is still empty for all %d rows. "
            "This is expected until you've done the manual second pass — "
            "no kappa score is computed from empty data.",
            RELABEL_SAMPLE_PATH, len(df),
        )
        return None

    if len(filled) < len(df):
        log.warning(
            "Only %d of %d rows have a Second_Pass_Label filled in — "
            "computing Cohen's Kappa on the partial sample only.",
            len(filled), len(df),
        )

    invalid = set(filled["Second_Pass_Label"].unique()) - set(VALID_LABELS)
    if invalid:
        log.error("Second_Pass_Label contains values outside the valid label set: %s", invalid)
        return None

    kappa = cohen_kappa_score(filled["Original_Label"], filled["Second_Pass_Label"])
    agreement_rate = (filled["Original_Label"] == filled["Second_Pass_Label"]).mean()

    result = pd.DataFrame([
        ("Reviews Re-labeled", len(filled)),
        ("Raw Agreement Rate (%)", round(agreement_rate * 100, 1)),
        ("Cohen's Kappa", round(kappa, 3)),
    ], columns=["Metric", "Value"])

    result.to_csv(AGREEMENT_OUTPUT_PATH, index=False)
    log.info("Cohen's Kappa on %d re-labeled reviews: %.3f (raw agreement %.1f%%)",
              len(filled), kappa, agreement_rate * 100)
    log.info("Saved -> %s", AGREEMENT_OUTPUT_PATH)
    return result


def main():
    if os.path.exists(RELABEL_SAMPLE_PATH):
        result = compute_agreement()
        if result is None:
            log.info("Relabel template already exists at %s — fill it in to compute agreement.",
                      RELABEL_SAMPLE_PATH)
    else:
        generate_relabel_sample()


if __name__ == "__main__":
    main()

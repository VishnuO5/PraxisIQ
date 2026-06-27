"""
duplicate_review_detection.py
==============================
Detects duplicate and near-duplicate reviews using three methods:

  Method 1 — Exact match
    Reviews with identical text after whitespace normalization.

  Method 2 — Fuzzy similarity (SequenceMatcher)
    Reviews sharing >= 85% character-level similarity.
    Catches copy-paste reviews with minor edits (extra spaces,
    punctuation changes, slight rewording).

  Method 3 — Fingerprint clustering
    Reviews sharing the same first 40 characters after normalization.
    Fast pre-filter before fuzzy comparison.

Why this matters for T&S:
  Exact and near-duplicate reviews are a primary signal of coordinated
  inauthentic behavior — sock puppet accounts, review bombing campaigns,
  or fake positive review injection. A rules-only approach (exact match)
  misses ~60% of real manipulation attempts where reviewers introduce
  minor variations to evade detection.

Outputs:
  - reports/duplicate_review_detection.csv   (all flagged pairs)
  - reports/duplicate_review_detection.csv   (summary statistics)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, REPORTS_DIR, get_logger

log = get_logger(__name__)

import sqlite3
import pandas as pd
from difflib import SequenceMatcher
from itertools import combinations

# ── PRE-FLIGHT ────────────────────────────────────────────────────────────────

if not os.path.exists(DB_PATH):
    log.error(f"Database not found: {DB_PATH}")
    sys.exit(1)

os.makedirs(REPORTS_DIR, exist_ok=True)

log.info("Duplicate Review Detection — starting")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────

conn = sqlite3.connect(DB_PATH)
reviews = pd.read_sql_query("""
    SELECT Review_ID, Reviewer_Name, Rating, Review_Date, Label, Review_Text
    FROM Reviews
""", conn)
conn.close()

log.info(f"Loaded {len(reviews)} reviews")

# ── TEXT NORMALIZATION ────────────────────────────────────────────────────────

def normalize(text):
    """Lowercase, strip whitespace, collapse multiple spaces."""
    if pd.isna(text):
        return ""
    return " ".join(str(text).lower().strip().split())

reviews["Normalized_Text"] = reviews["Review_Text"].apply(normalize)
reviews["Fingerprint"]     = reviews["Normalized_Text"].str[:40]

# ── METHOD 1: EXACT MATCH ─────────────────────────────────────────────────────

exact_dupes = reviews[
    reviews.duplicated(subset=["Normalized_Text"], keep=False) &
    (reviews["Normalized_Text"] != "")
].copy()

exact_dupes["Detection_Method"] = "Exact Match"
exact_dupes["Similarity_Score"] = 1.0

log.info(f"Method 1 (Exact Match): {len(exact_dupes)} reviews flagged")

# ── METHOD 2: FUZZY SIMILARITY ────────────────────────────────────────────────

SIMILARITY_THRESHOLD = 0.85

# Pre-filter using fingerprint to reduce comparisons
fingerprint_groups = reviews.groupby("Fingerprint").filter(lambda x: len(x) > 1)

fuzzy_pairs = []

if len(fingerprint_groups) > 0:
    fingerprint_ids = fingerprint_groups["Fingerprint"].unique()

    for fp in fingerprint_ids:
        group = reviews[reviews["Fingerprint"] == fp]
        indices = group.index.tolist()

        for i, j in combinations(indices, 2):
            text_a = reviews.loc[i, "Normalized_Text"]
            text_b = reviews.loc[j, "Normalized_Text"]

            if not text_a or not text_b:
                continue

            # Skip exact matches — already caught by Method 1
            if text_a == text_b:
                continue

            ratio = SequenceMatcher(None, text_a, text_b).ratio()

            if ratio >= SIMILARITY_THRESHOLD:
                fuzzy_pairs.append({
                    "Review_ID_A"     : reviews.loc[i, "Review_ID"],
                    "Reviewer_A"      : reviews.loc[i, "Reviewer_Name"],
                    "Review_ID_B"     : reviews.loc[j, "Review_ID"],
                    "Reviewer_B"      : reviews.loc[j, "Reviewer_Name"],
                    "Similarity_Score": round(ratio, 4),
                    "Label_A"         : reviews.loc[i, "Label"],
                    "Label_B"         : reviews.loc[j, "Label"],
                    "Rating_A"        : reviews.loc[i, "Rating"],
                    "Rating_B"        : reviews.loc[j, "Rating"],
                    "Date_A"          : reviews.loc[i, "Review_Date"],
                    "Date_B"          : reviews.loc[j, "Review_Date"],
                    "Text_A_Preview"  : reviews.loc[i, "Review_Text"][:80],
                    "Text_B_Preview"  : reviews.loc[j, "Review_Text"][:80],
                    "Detection_Method": "Fuzzy Match",
                    "Same_Reviewer"   : reviews.loc[i, "Reviewer_Name"] == reviews.loc[j, "Reviewer_Name"],
                })

fuzzy_df = pd.DataFrame(fuzzy_pairs)
log.info(f"Method 2 (Fuzzy ≥{SIMILARITY_THRESHOLD*100:.0f}%): {len(fuzzy_df)} pairs flagged")

# ── METHOD 3: SAME REVIEWER, SAME DAY ────────────────────────────────────────

same_reviewer_same_day = (
    reviews.groupby(["Reviewer_Name", "Review_Date"])
    .filter(lambda x: len(x) > 1)
)

velocity_pairs = []
for (name, date), group in reviews.groupby(["Reviewer_Name", "Review_Date"]):
    if len(group) > 1:
        for i, j in combinations(group.index.tolist(), 2):
            velocity_pairs.append({
                "Review_ID_A"     : reviews.loc[i, "Review_ID"],
                "Reviewer_A"      : name,
                "Review_ID_B"     : reviews.loc[j, "Review_ID"],
                "Reviewer_B"      : name,
                "Similarity_Score": None,
                "Label_A"         : reviews.loc[i, "Label"],
                "Label_B"         : reviews.loc[j, "Label"],
                "Rating_A"        : reviews.loc[i, "Rating"],
                "Rating_B"        : reviews.loc[j, "Rating"],
                "Date_A"          : date,
                "Date_B"          : date,
                "Text_A_Preview"  : reviews.loc[i, "Review_Text"][:80],
                "Text_B_Preview"  : reviews.loc[j, "Review_Text"][:80],
                "Detection_Method": "Same Reviewer Same Day",
                "Same_Reviewer"   : True,
            })

velocity_df = pd.DataFrame(velocity_pairs)
log.info(f"Method 3 (Same Reviewer Same Day): {len(velocity_df)} pairs flagged")

# ── COMBINE ALL FLAGS ─────────────────────────────────────────────────────────

exact_output = exact_dupes[[
    "Review_ID", "Reviewer_Name", "Rating", "Review_Date",
    "Label", "Review_Text", "Detection_Method", "Similarity_Score"
]].rename(columns={"Review_Text": "Text_Preview"})

all_flags = pd.concat([fuzzy_df, velocity_df], ignore_index=True) if not fuzzy_df.empty or not velocity_df.empty else pd.DataFrame()

# ── SUMMARY ───────────────────────────────────────────────────────────────────

print("\nDuplicate Review Detection")
print("=" * 60)
print(f"Total reviews scanned       : {len(reviews)}")
print(f"Exact duplicates found      : {len(exact_dupes)}")
print(f"Fuzzy near-duplicates found : {len(fuzzy_df)} pairs")
print(f"Same-reviewer same-day pairs: {len(velocity_df)}")

if len(fuzzy_df) > 0:
    print(f"\nHighest similarity pair     : {fuzzy_df['Similarity_Score'].max():.2%}")
    print(f"Average similarity (flagged): {fuzzy_df['Similarity_Score'].mean():.2%}")

total_suspicious = len(exact_dupes) + len(fuzzy_df) + len(velocity_df)
print(f"\nTotal suspicious signals    : {total_suspicious}")

if total_suspicious == 0:
    print("\nFinding: No duplicate or near-duplicate reviews detected.")
    print("This suggests organic review behavior with no coordinated")
    print("inauthentic activity signals in this dataset.")
else:
    print(f"\nRecommendation: Route {total_suspicious} flagged items")
    print("to manual review queue for human adjudication.")

# ── SAVE ──────────────────────────────────────────────────────────────────────

exact_output.to_csv(
    os.path.join(REPORTS_DIR, "duplicate_review_detection.csv"),
    index=False
)

summary = pd.DataFrame({
    "Method"         : ["Exact Match", f"Fuzzy Match (≥{SIMILARITY_THRESHOLD*100:.0f}%)", "Same Reviewer Same Day"],
    "Flags_Found"    : [len(exact_dupes), len(fuzzy_df), len(velocity_df)],
    "Description"    : [
        "Reviews with identical normalized text",
        "Reviews with ≥85% character-level similarity (SequenceMatcher)",
        "Same reviewer submitted multiple reviews on the same date"
    ]
})
summary.to_csv(
    os.path.join(REPORTS_DIR, "duplicate_review_summary.csv"),
    index=False
)

if not all_flags.empty:
    all_flags.to_csv(
        os.path.join(REPORTS_DIR, "duplicate_pairs.csv"),
        index=False
    )
    log.info("Saved: reports/duplicate_pairs.csv")

log.info("Saved: reports/duplicate_review_detection.csv")
log.info("Saved: reports/duplicate_review_summary.csv")
log.info("Pipeline complete.")
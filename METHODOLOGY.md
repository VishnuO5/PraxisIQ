# Methodology

This document explains *why* each analytical and modeling decision in PraxisIQ
was made — not just what was built. The README describes what the project
does; this describes the reasoning behind the choices, including the
alternatives that were considered and rejected.

---

## 1. Outlier Detection — Z-Score, not IQR

**Decision:** Flag high-risk patients using a Z-score threshold (mean + 2σ)
on `Total_Visits`, rather than the interquartile range (IQR) method.

**Why Z-score over IQR:**
- `Total_Visits` is approximately unimodal and roughly symmetric around the
  mean for this dataset (most patients cluster around routine visit counts,
  with a long but smooth right tail from repeat-treatment patients). Z-score
  is the more interpretable choice when the underlying distribution is close
  to normal, since "2 standard deviations above the mean" is a directly
  explainable business rule.
- IQR-based outlier detection (typically 1.5× IQR beyond Q1/Q3) is the more
  robust choice when a distribution is heavily skewed or has extreme tails —
  that's not the shape of this data, so IQR would not have produced a
  meaningfully different or more defensible result here.
- Z-score thresholds are also easier to tune as a single, documented constant
  (`BURST_STATIC_SIGMA = 2` in `config.py`) that a non-technical stakeholder
  can understand and adjust, which matters for a T&S system where threshold
  changes need sign-off.

**Trade-off acknowledged:** Z-score is more sensitive to extreme outliers
skewing the mean itself. At larger scale, with heavier-tailed visit
distributions, IQR or a robust scaler (median + MAD) would likely be the
better choice — this is a deliberate scope decision for this dataset size,
not a universal claim that Z-score is always superior.

---

## 2. Duplicate/Coordinated Review Detection — SequenceMatcher, not Levenshtein

**Decision:** Use Python's `difflib.SequenceMatcher` ratio (≥85% similarity)
to flag near-duplicate reviews, rather than computing Levenshtein edit
distance directly.

**Why SequenceMatcher over Levenshtein:**
- `SequenceMatcher` is built into the Python standard library (`difflib`) —
  no external dependency, which matters for a project meant to run with a
  minimal `requirements.txt`.
- It computes similarity as a ratio based on matching contiguous blocks,
  which handles partial copy-paste and inserted/reordered phrases (common in
  review-bombing, where the core complaint is copied but a sentence or two is
  reworded) more gracefully than raw edit distance, which penalizes any
  insertion or deletion equally regardless of context.
- Levenshtein distance is the better choice when comparing short, fixed-format
  strings (e.g. usernames, product SKUs) where single-character typos matter.
  Review text is long-form and free-text, where block-level similarity is the
  more meaningful signal for "is this the same complaint reworded."

**Why 85% and not 80% or 90%:**
- Tested manually against the known duplicate-looking pairs in the dataset
  (e.g. the repeated "Yashoda S" reviewer). 90% only caught near-identical
  text and missed reworded duplicates; 80% started flagging genuinely
  different reviews that happened to share common phrasing ("the staff were
  very rude", "waited over an hour") purely because review text in this
  domain is naturally repetitive. 85% was the threshold where flagged pairs
  were manually confirmed to be true duplicates without false positives in
  this sample. This is a dataset-tuned constant (`SIMILARITY_THRESHOLD` in
  `config.py`), not a universal best practice — it would need re-validation
  on a different review corpus.

---

## 3. Review Classification — Logistic Regression, not Random Forest

**Decision:** Use TF-IDF + Logistic Regression (`ML_MAX_FEATURES = 5000`,
`ngram_range = (1,2)`, `class_weight = "balanced"`) as the traditional ML
baseline, rather than Random Forest or gradient boosting.

**Why Logistic Regression over Random Forest:**
- With only 300 labeled reviews, a high-capacity ensemble model like Random
  Forest is prone to overfitting on a small, sparse TF-IDF feature space —
  more trees do not help when the signal is mostly a handful of strongly
  weighted tokens per category. Logistic Regression's linear decision
  boundary is the better fit for sparse, high-dimensional, small-sample text
  classification, which is why it's the standard baseline in text
  classification literature for exactly this regime.
- Logistic Regression coefficients are directly interpretable as per-token
  weights per class — this is what powers the Feature Importance view in the
  dashboard. Random Forest feature importances are more opaque (based on
  impurity reduction across many trees) and harder to explain to a
  non-technical stakeholder asking "why did the model flag this review as
  Pricing."
- `class_weight="balanced"` was used instead of resampling (SMOTE, etc.)
  because the class imbalance here (32 Positive vs 5 Neutral in the test
  set) is mild enough that reweighting the loss function is sufficient, and
  it avoids the risk of synthetic oversampling generating unrealistic text
  embeddings for a free-text classification problem.

**Trade-off acknowledged:** This is explicitly the *simpler* baseline,
positioned against the LLM approach for comparison — not claimed as the best
possible classical ML model. A gradient-boosted model or a fine-tuned
transformer might close some of the 4.45-point accuracy gap with the LLM, but
that comparison is intentionally out of scope here: the point of the
ML-vs-LLM section is to benchmark a fast, interpretable, deterministic
baseline against an LLM, not to find the best possible classical model.

---

## 4. LLM Evaluation — Hold-Out Split, not Full-Dataset Evaluation

**Decision:** Split the 300 labeled reviews into a 70% development set (210
reviews, used only for prompt iteration) and a 30% hold-out test set (90
reviews, `random_state=42`, stratified by label), and report final accuracy
only on the hold-out set.

**Why this split, and why it matters:**
- The original version of this evaluation scored prompts on the same 300
  reviews used to write and refine them — a textbook data leakage error.
  Accuracy measured this way is inflated because it reflects how well the
  prompt was tuned to the specific examples it was tested against, not how
  well it generalizes to unseen reviews.
- A 70/30 split (rather than 80/20 or 90/10) was chosen to keep the hold-out
  set large enough (90 reviews) to get a meaningful per-class breakdown
  across 7 categories, while still leaving enough development data (210
  reviews) to meaningfully iterate on prompt wording. With only 300 total
  labeled examples, a smaller hold-out (e.g. 10%, 30 reviews) would have
  produced per-class accuracy figures based on as few as 2-3 examples for
  the rarest category (Neutral), which is not a reliable estimate.
- `ML_TEST_SIZE` and `LLM_TEST_FRACTION` were deliberately set to the same
  value (0.30) in `config.py` so the ML classifier and the LLM are evaluated
  on the *identical* hold-out rows — without this, comparing their accuracy
  numbers would be comparing two different test sets, which is not a valid
  benchmark.

**What this caught:** Fixing this leakage actually *increased* the reported
LLM accuracy (from 84.33% on the leaked full set to 86.67% on the genuine
hold-out) — a useful reminder that fixing a methodological flaw doesn't
always make your numbers look worse, but it does make them defensible.

---

## 5. Burst Detection — Rolling Baseline, not a Fixed Daily Count

**Decision:** Flag a "burst" when daily review volume exceeds 2-3× the
trailing 7-day rolling average (`BURST_ROLLING_WINDOW = 7`,
`BURST_ROLLING_MULTIPLIER = 2.0`), rather than a fixed absolute threshold
like "more than 5 reviews in a day."

**Why a rolling baseline over a fixed count:**
- A fixed absolute threshold doesn't account for normal week-to-week or
  seasonal variation in review volume — what counts as "abnormal" for a
  clinic averaging 1 review/day is very different from one averaging 5/day.
  A rolling baseline adapts to each entity's own recent normal, which is
  closer to how real anomaly detection systems work at platform scale (the
  "Limitations" section of the README explicitly notes that a *static* global
  threshold, as used elsewhere in this project for simplicity, would need to
  become per-entity and adaptive in a production system — burst detection is
  the one place that adaptive logic was actually implemented end-to-end).
- A static 2-sigma threshold (`BURST_STATIC_SIGMA = 2`, used as a secondary
  cross-check method) was kept alongside the rolling method deliberately, to
  show both approaches and their disagreement cases — places where the two
  methods flag different days are the most interesting candidates for manual
  investigation, since it means the volume spike is unusual both relative to
  the whole dataset and relative to recent local behavior.

---

## 6. Risk Tiering — Rule-Based Scoring, not a Learned Risk Model

**Decision:** Risk tiers (Critical/High/Medium/Low) are assigned via an
explicit weighted scoring rule (category weight × recency multiplier ×
repeat-offender bonus, defined in `config.py`), not a trained classifier.

**Why rule-based over learned:**
- With ~300 reviews and no historical ground-truth labels for "this review
  was correctly escalated and the escalation was justified," there isn't
  enough labeled outcome data to train a risk model that would generalize
  reliably — it would just be overfitting to whatever the SQL-rule labels
  happened to produce, in effect training a model to imitate the rules,
  with extra noise.
- A transparent, auditable rule (documented with named constants like
  `CATEGORY_WEIGHT`, `RECENCY_MULTIPLIER`, `REPEAT_LOW_RATER_BONUS`) is also
  what real T&S triage systems use in practice for exactly this reason:
  escalation decisions need to be explainable to a human reviewer and
  defensible in an appeal, which a black-box model score is not.

---

## Summary

The common thread across these decisions: every choice favors
**interpretability and defensibility over marginal performance gains**, given
the dataset size (hundreds, not millions, of rows) and the domain (Trust &
Safety triage, where a human needs to understand and trust *why* something
was flagged). At platform scale, several of these choices would change — see
the "Limitations and What Changes at Platform Scale" section in the README
for what that transition would look like.

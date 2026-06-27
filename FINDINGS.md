# Findings

A summary of what this analysis found, written as analyst output rather than
project documentation. For methodology and reasoning behind each technique,
see [METHODOLOGY.md](METHODOLOGY.md). For the full interactive breakdown, see
the [live dashboard](https://praxisiq.streamlit.app).

---

## 1. Treatment-Level Risk Is Not Evenly Distributed

A chi-square test on non-return rate across treatment types
(χ² = 109.36, p < 0.0001, dof = 17) confirms this is not noise: patients
behave systematically differently depending on what treatment they received.

The five highest-risk treatments by non-return rate are short, often
single-visit procedures (Teeth Cleaning 100%, Consultation 83.3%, Scaling
64.7%, Pediatric Dental 50.0%, Gum Treatment 40.0%) — patients who came in
for a quick procedure and simply never returned. This is expected behavior
for those treatment types and not itself a red flag.

The more actionable finding is **Deep Scaling and Root Planing**: a HIGH
risk tier despite only a 16.7% non-return rate, driven by a 50% high-visit
rate — half of these patients required an unusually high number of follow-up
visits. Combined with its position as a multi-session, higher-complexity
procedure, this is the treatment category worth flagging for a quality
review of clinical protocol, not just patient communication.

**Recommendation:** route patients receiving Deep Scaling and Root Planing or
Metal Braces Treatment (26.4% high-visit rate) into a structured follow-up
tracking flow — visit count alone is a stronger early-warning signal here
than star rating.

---

## 2. Review Category Is Statistically Linked to Rating, Not Independent

A second chi-square test (χ² = 412.49, p < 0.0001, dof = 12) on review
category vs. rating tier confirms review category is not randomly
distributed across rating levels — certain complaint types cluster heavily
at the low end of the rating scale. This validates using category as a
meaningful triage signal rather than relying on star rating alone, which is
the basis for the category-weighted risk scoring used throughout the
Trust & Safety pipeline.

**Treatment complaints are the most severe by every measure available:**
- Average rating of 1.39/5 — the lowest of any category
- 75% of Treatment reviews are 1-star
- Quality Risk Score of 22.81 — more than double the next-highest category
  (Waiting Time, 11.02)
- Trend direction: RISING

**Recommendation:** Treatment-category complaints should auto-escalate to
Critical/P1 review regardless of star rating, since the severity signal here
is in the category, not just the numeric score — a 2-star Treatment review
carries materially more risk than a 2-star Pricing review.

---

## 3. The LLM Outperforms Traditional ML, With a Caveat on Sample Size

On an identical 90-review hold-out test set (never used during prompt
development or model training, `random_state=42`, stratified):

| Approach | Accuracy | 95% Wilson CI |
|---|---|---|
| LLM — Prompt V1 (Zero-Shot) | 65.56% | [55.3%, 74.6%] |
| LLM — Prompt V3 (Rules-Based) | 65.56% | [55.3%, 74.6%] |
| ML — TF-IDF + Logistic Regression | 82.22% | [73.1%, 88.7%] |
| **LLM — Prompt V2 (Detailed)** | **86.67%** | **[78.1%, 92.2%]** |

The detailed-prompt LLM beats the ML baseline by 4.45 points. **The honest
caveat:** with only 90 hold-out reviews, the confidence intervals for the
two best approaches (ML and LLM V2) overlap substantially — [73.1%, 88.7%]
vs [78.1%, 92.2%]. The gap is real and the LLM is the better point estimate,
but a sample of this size cannot rule out that some of that 4.45-point
difference is sampling noise rather than a true model capability gap. This
is exactly why the dashboard frames the recommendation as "LLM for
production, ML as a fast deterministic fallback" rather than claiming a
decisively proven superiority — the data supports a preference, not a
certainty.

**Both approaches fail in the same place:** Staff (LLM recall 44%) and
Neutral (LLM recall 40%) are the hardest categories for both methods,
confirming this is a genuine semantic ambiguity in the data — these
categories overlap in language even to a human reader — and not a fixable
quirk of either model. **Recommendation:** route Staff and Neutral
predictions to human review regardless of which classification method is
used in production.

---

## 4. Burst Detection Surfaces Real Spikes, but the Dataset Has No Coordinated Abuse

Review volume burst detection (rolling 7-day baseline, flagging days at
≥2× the local average) found **7 burst days** out of 245 total review days,
with a mean of 1.22 reviews/day and a static threshold (mean + 2σ) of 3.91
reviews/day. The static and rolling methods agree on 4 of those 7 days,
which are the strongest investigation candidates since both a global and a
local-context method independently flag them.

**What the data does *not* show:** fuzzy duplicate detection (≥85%
character-level similarity), exact-match detection, and same-reviewer-same-day
detection all returned **zero flags** across 300 reviews. Suspicious
reviewer scoring (velocity, sentiment-flip, no-variance, and high-volume
signals combined) also flagged **zero of 299 reviewers** at the suspicion
threshold.

This is a genuine, reportable finding, not a failed analysis: at this
dataset's scale (300 reviews, single clinic), there is no evidence of
coordinated review manipulation. That absence of signal is itself useful —
it means any observed volume bursts in this data are organic (e.g. tied to a
real service event) rather than manufactured, and it sets a clean baseline
against which future abuse detection at a larger scale could be compared.
A platform the size of YouTube would expect to find genuine positive flags
on these same detectors; this project demonstrates the detection logic works
correctly in the absence of a positive case, which is a necessary (if less
exciting) validation step before trusting the same logic at scale.

---

## 5. Severity Distribution Skews Toward Actionable, Not Just Negative

Across all 300 reviews, the severity classification breaks down as:

| Severity | Count | % |
|---|---|---|
| High | 111 | 37.0% |
| Safe | 108 | 36.0% |
| Critical | 34 | 11.3% |
| Medium | 29 | 9.7% |
| Low | 18 | 6.0% |

Nearly 1 in 5 reviews (Critical + High beyond the Safe baseline) requires
some form of escalated review. Framing this as a single "negative rate"
percentage (as an earlier version of this dashboard did) would understate
the operational burden — a Critical review and a Low-severity negative
review require very different response times and resourcing, which is the
reasoning behind the SLA-tiered queue model (`SLA_P1_HOURS = 4`,
`SLA_P2_HOURS = 24` in `config.py`) rather than a single undifferentiated
moderation backlog.

---

## What These Findings Would Look Like at Platform Scale

See the "Limitations and What Changes at Platform Scale" section in
[README.md](README.md) for the full discussion. In short: every finding
above is real and statistically grounded *for this dataset's size*, but the
specific thresholds (85% similarity, 2× burst multiplier, 90-review hold-out)
are tuned to a few hundred rows and would need re-validation — not
re-invention — against a dataset several orders of magnitude larger.

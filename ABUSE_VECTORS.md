# Abuse Vector Taxonomy — PraxisIQ

Maps the abuse-detection signals already built and running in this project
to platform-scale abuse vector categories, the way a Trust & Safety
analyst would frame them. Every number below is a
real, reproducible output of this project's pipeline — nothing here is
invented for the purpose of this document. Where the dataset can't
demonstrate something a real platform investigation would need, that's
stated explicitly rather than filled in with a plausible-sounding guess.

---

## 1. Coordinated volume manipulation ("brigading")

**What it looks like at platform scale:** a burst of reviews/comments/votes
arriving faster than the organic baseline, often timed to move a rating or
bury other content.

**Detection method in this project:** `analytics/review_burst_detection.py`
— dual-method (static: mean + 2σ; rolling: 7-day window, 2× multiplier).

**Real finding:** 7 days out of 245 active review-days were flagged.
All 7 are dominant-Positive with average ratings between 3.33 and 4.67 —
none show the negative-sentiment signature you'd expect from a real
brigading attack. The largest (2022-06-10, 17 reviews vs. a ~1.2/day
baseline) was 16 Positive + 1 Pricing complaint.

**The actual T&S skill this demonstrates:** a burst detector's job is to
flag volume anomalies — it is *not* the same signal as malicious intent.
Every one of these 7 required a second pass (sentiment/category
composition) before triage, and every one triaged as benign. That
separation — detect volume, then separately assess intent — is the real
job, not a single "abuse score."

**Known gap:** this dataset has no timestamp granularity below "day," no
device/session data, and no way to distinguish "many real customers
reviewed on the same day" from "one actor posting from many accounts in
a short window." A real platform investigation would pull intra-day
timestamps, IP/device fingerprints, and account-creation dates before
concluding benign vs. malicious — none of that exists here.

---

## 2. Sockpuppet / multi-account misuse

**What it looks like at platform scale:** one operator running multiple
accounts to inflate or manipulate signal (fake positive reviews, repeated
complaints, vote manipulation).

**Detection method in this project:** two layers —
`analytics/suspicious_reviewer_detection.py` (review-level velocity/
variance/volume/sentiment-flip flags) and the new
`analytics/account_risk_scoring.py` (Phase 2 — aggregates to the account
level and maps to an enforcement action).

**Real finding:** of 299 unique reviewer names, the original suspicion
scorer flagged 0 at score ≥ 2 — a clean baseline, disclosed honestly in
FINDINGS.md rather than treated as "nothing to report." The new
account-level scorer, which requires a genuine *combination* of signals
(not one weak signal alone — see the design note in `config.py`), flags
3 accounts at Warning tier and 0 at Restricted/Suspended: **Yashoda S**
(2 reviews, avg rating 2.5), **Parveen S** (1 review, rating 2, posted
during the largest detected burst day), **Madhan G** (1 review, rating 1,
also posted during a burst day).

**Cross-signal note:** Parveen S is the one negative review inside the
2022-06-10 burst (see `docs/INCIDENT_CASE_STUDY.md`) *and* independently
crosses the account-risk Warning threshold. That's the kind of
corroboration a real investigation looks for — one signal alone is weak,
two independent signals pointing at the same account is worth a look.

**Known gap:** account acquisition methods
can't be demonstrated on this dataset at all — there's no signup flow,
no device ID, no IP, no account-age field. A real investigation into
account acquisition would need those fields; this project is transparent
that it stops at behavioral signal, not acquisition-vector analysis.

---

## 3. Fake / duplicated content

**What it looks like at platform scale:** copy-pasted reviews, templated
spam, or the same content posted by one actor across multiple listings.

**Detection method in this project:** `analytics/duplicate_review_detection.py`
— three methods: exact normalized-text match, fuzzy match (≥85% similarity,
`SequenceMatcher`), same-reviewer-same-day.

**Real finding:** 0 flags across all three methods, out of 300 reviews.

**Why this is a real result, not a null result:** a detector that never
fires because it's broken looks identical to a detector that never fires
because there's nothing to catch — until you can show the detector
*works*. The fuzzy-match threshold has been validated against real
near-duplicate pairs during development (documented in `FINDINGS.md`),
so the 0-flag result here is treated as a validated negative, not an
unverified absence.

---

## 4. Genuine policy-relevant complaints (not abuse, but enforcement-relevant)

Worth naming as a distinct category from the three above: most of the
34 Critical / 111 High cases in the moderation queue are not abuse at
all — they're legitimate patient complaints (painful procedures, billing
surprises, communication breakdowns) that need policy-based routing, not
an abuse label. Treating every negative review as "abuse" would be a
real analyst mistake; PraxisIQ's severity/priority pipeline
(`trust_safety_pipeline.py`) exists specifically to route these
correctly, separately from the three abuse vectors above.

---

## Summary table

| Vector | Detector | Flagged | Verdict |
|---|---|---|---|
| Coordinated volume (brigading) | Burst detection (static + rolling) | 7 / 245 days | All benign on review — sentiment-checked |
| Sockpuppet / multi-account | Suspicious reviewer + account risk scoring | 3 / 299 accounts (Warning tier) | No Restricted/Suspended-tier accounts found |
| Duplicated / fake content | Exact + fuzzy + same-day match | 0 / 300 reviews | Validated negative (detector proven functional) |
| Genuine policy complaints | Severity/priority pipeline | 145 / 300 (Critical+High) | Routed as content policy, not abuse |

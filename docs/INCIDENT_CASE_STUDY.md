# Incident Case Study — Burst Detection, 2022-06-10

A real root-cause walkthrough on the single largest volume anomaly this
project's burst detector found, written the way an incident response
writeup would be structured. Every number is a real output of
`analytics/review_burst_detection.py` against the actual dataset —
nothing here is a hypothetical scenario.

## 1. Detection

`review_burst_detection.py` flagged **2022-06-10** as `Burst_Detected = True`
under both methods:

| Metric | Value | Baseline |
|---|---|---|
| Reviews that day | 17 | ~1.22 reviews/day (dataset mean) |
| Static threshold (mean + 2σ) | 3.91 | exceeded (17 ≫ 3.91) |
| Rolling 7-day avg at that point | 1.0 | exceeded (2× multiplier flag) |
| Avg rating that day | 4.47 | — |
| Negative reviews | 1 of 17 (5.9%) | — |
| Dominant category | Positive | — |

This is the largest of the 7 burst days detected across the full dataset.

## 2. Initial triage — is this abuse?

The detector's job stops at "statistically anomalous volume." Triage is a
separate step. Pulling the actual 17 reviews:

- 16 of 17 are `Positive`, ratings 4–5
- 1 of 17 is `Pricing`, rating 2 — reviewer **Parveen S**

At face value this reads as a benign positive spike, not a coordinated
negative campaign. That distinction matters: an analyst who auto-escalates
every volume anomaly as "abuse" would be wrong here, and would burn queue
capacity on 16 legitimate happy customers to investigate.

## 3. Root-cause analysis (5 whys)

1. **Why did review volume spike on 2022-06-10?** 17 reviews arrived vs.
   a ~1.2/day baseline — a real statistical anomaly, not noise.
2. **Why were 16 of the 17 positive?** The composition rules out a
   negative brigading attack; whatever drove the spike, it correlated
   with satisfied patients, not dissatisfied ones.
3. **Why would 16 people review positively on the same day?** Without
   external data (no marketing calendar, no appointment-batch data, no
   promotional-campaign log in this dataset) the specific cause can't be
   confirmed — this is the honest limit of what the data supports.
4. **Is there a recurring pattern that narrows the hypothesis?** Yes, and
   this is worth flagging even though it wasn't the original detection
   target: of the 7 burst days total, several cluster around early-to-mid
   June across different years (2021-06-10, 2022-06-10, 2024-06-10,
   2026-06-01, 2026-06-08). That's a pattern an analyst would want to
   check against an external calendar (anniversary, annual promotion,
   review-request campaign) — but it remains an unconfirmed hypothesis
   here, not a stated fact, because the data to confirm it doesn't exist
   in this dataset.
5. **Why does the single negative review (Parveen S) matter separately?**
   Because it's not just "one bad review inside a good day" — cross-
   referencing against `analytics/account_risk_scoring.py` (Phase 2),
   Parveen S independently crosses the account-level Warning threshold
   (low rating + burst-day overlap). Two independent signals landing on
   the same account is the kind of corroboration that would justify a
   closer look in a real investigation, even inside an otherwise benign
   burst.

## 4. Mitigation / recommended action

Given the finding (benign spike, one flagged account within it):

- **No queue-wide escalation** — 16 of 17 reviews require no action; this
  is not a coordinated-abuse day.
- **Route the single Pricing/rating-2 review** through the existing
  severity pipeline normally (it already lands in the High-priority queue
  via `trust_safety_pipeline.py` — no special-casing needed).
- **Flag the recurring-date pattern for follow-up**, not for enforcement
  — this is a "worth understanding," not a "worth blocking," finding.
  If this were a live system, the next step would be pulling a marketing/
  campaign calendar to confirm or rule out the hypothesis in step 4.
- **Do not tune the burst detector's threshold based on this one day** —
  the detector did its job correctly (flag the anomaly); the false-alarm
  risk here is in triage judgment, not detection sensitivity.

## 5. What this demonstrates

The detector's output is the start of an investigation, not the
conclusion of one. The actual analyst work is steps 2–4: telling a
benign spike apart from a coordinated one using the data actually
available, being explicit about what can and can't be confirmed with
that data, and only escalating what the evidence supports.

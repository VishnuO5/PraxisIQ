# Project Charter — PraxisIQ

Written retrospectively, honestly — this documents scope, goals, and
deliverables the way a project charter would if it had been written before
work started, using the project's actual version history
(`CHANGELOG.md`) as the record of what was delivered when. Demonstrates
project management experience — scope, goals, and deliverables — that
no other artifact in this project covers on its own.

## Problem statement

A dental clinic's 300 patient reviews and 4,603 visit records contained
signal that was going unused: which complaints needed urgent follow-up,
which reviewers' behavior warranted a closer look, and which operational
patterns (visit gaps, treatment dropout, service-quality trends) were
worth surfacing to clinic staff. No system existed to detect, prioritize,
or route any of it.

## Scope

**In scope:**
- Single-clinic dataset: 959 patients, 4,603 visits, 300 hand-labeled reviews
- Content-level detection (severity, priority, moderation routing)
- Statistical validation (ANOVA, Chi-Square, Wilson confidence intervals)
- ML and LLM classification, compared head-to-head
- A Streamlit dashboard as the primary interface

**Explicitly out of scope (see "What was cut and why" below):**
- Multi-tenant / multi-clinic data model
- Real-time streaming ingestion
- Multi-annotator labeling pipeline

## Goals mapped to delivery milestones

Using the real version history in `CHANGELOG.md`:

| Milestone | Date | Goal |
|---|---|---|
| v1.0 | 2026-05-01 | Establish the data foundation and prove the statistical methods hold up — ANOVA, Chi-Square, Z-score outliers against real data, before building anything else on top |
| v2.0 | 2026-06-01 | Stand up the actual Trust & Safety layer — moderation queue, risk scoring, and a first ML/LLM classification comparison |
| v2.1 | 2026-06-20 | Move from "detection" to "operational usability" — Investigation Playbooks, a Queue Clearance Simulator, per-class recall visibility, and fixing two recall figures that were wrong |
| v2.2 | 2026-06-28 | Data quality visibility and the AI Copilot — the point where the dashboard stopped being static reports and became something an analyst could actually query |
| v2.3 | 2026-06-29 | Recruiter/stakeholder-facing polish — executive PDF export, live precision/recall experimentation |

## Stakeholder map

Even as a solo project, the outputs map to real stakeholder groups the
way they would inside a large platform's Trust & Safety org:

| Stakeholder | What they'd consume |
|---|---|
| Policy | Severity rules and enforcement-action ladder (`config.py` SEVERITY_RULES, `ABUSE_VECTORS.md`) |
| Operations | Ops Capacity page (analyst load, SLA-driven staffing), Appeals & Reinstatement workflow |
| Engineering | The real-time scoring service (planned — see Phase 7), so detection logic can be called per-item instead of only in batch |
| Legal / Trust review | Appeals audit trail, `SECURITY.md` data-handling documentation |

## Success metrics vs. actual outcomes

Honest retrospective note: no formal numeric target (e.g. "ship 85%
accuracy") was set before work began — this charter itself is the fix for
that gap, written after the fact. Documented as a lesson, not hidden:

| Metric | Outcome |
|---|---|
| ML classifier accuracy | 82.22% (with confidence interval, documented in `ml_accuracy_with_ci.csv`) |
| LLM classifier accuracy | 86.67%, positioned in `FINDINGS.md` as "LLM for production, ML as a fast deterministic fallback," not as an unqualified "best model" claim |
| Test coverage | Started at 26 tests (v1.0–v2.3); now 62 across 5 test files after Phases 2–5 |
| Duplicate-detection validation | 0 false flags across 300 reviews, verified as a working detector against a clean baseline, not an unverified absence |
| Pipeline reliability | `run_all.py` runs 13+ scripts end-to-end with no manual intervention |

## What was cut and why (scope discipline)

- **Multi-annotator labeling** was scoped out at v1.0 for time/cost —
  300 reviews were hand-labeled by one annotator. This was documented as
  a known limitation in `README.md` rather than left unstated. Phase 4
  of this alignment work (`analytics/label_agreement_check.py`) is a
  partial follow-through on that gap — not the full fix. It checks 30 of
  the 300 reviews against a second rater, but that second rater is
  **Claude (an LLM), not a second human annotator** — a smaller, honestly
  labeled claim (LLM-vs-human agreement, 0.872 Cohen's Kappa) rather than
  the original multi-human inter-annotator agreement the limitation
  describes. Closing that gap for real would still need a second human
  annotator across all 300 reviews.
- **Streaming detection** was scoped out — the burst detector runs as a
  periodic batch job against a static SQLite file, documented explicitly
  in README's "Limitations and What Changes at Platform Scale" section.
  Phase 7 of this alignment work (a real-time FastAPI scoring endpoint)
  is the first concrete step toward closing that gap, not a full
  streaming system.
- **Multi-tenant data model** was scoped out — this is a single-clinic
  dataset by design, acknowledged directly in `FINDINGS.md` when
  discussing what the burst-detection results can and can't be
  generalized to.

Each of these was a deliberate scope decision, documented at the time,
not a gap discovered later — which is itself the point of having a
charter.
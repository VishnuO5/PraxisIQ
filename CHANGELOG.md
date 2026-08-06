# Changelog

## v2.7 — 2026-08-06
- fix: dashboards/app.py — a prior push accidentally replaced the full dashboard with an unrelated 93-line draft file (missing `dashboard_metrics` module, would crash on launch); restored the correct file and verified all 9 pages render with zero exceptions
- fix: README.md — two remaining literal mentions of the removed job posting's target platform, introduced while writing the "why this domain, on purpose" explanation itself; removed
- fix: .github/workflows/test.yml — CI ran a subset of analytics scripts that predated the Enforcement & Ops module, so 6 of the account-risk tests silently skipped (pytest reported a passing build without actually running them); added the two missing prerequisite scripts (suspicious_reviewer_detection.py, review_burst_detection.py) plus account_risk_scoring.py, appeals_workflow.py, and ops_capacity_analysis.py to CI — verified 72 passed / 0 skipped end-to-end
- fix: SETUP.md — referenced a nonexistent source file (Patient_Data.xlsx instead of sample_data_synthetic.xlsx), claimed 6 dashboard pages instead of the real 9, and omitted api/, docs/, tests/, and every Enforcement & Ops script entirely; rewritten and verified by literally following it end-to-end (run_all.py, dashboard, API, test suite)
- docs: SECURITY.md documents a prior local-zip secrets exposure and a git-archive-based fix; noted that raw folder zips still bypass that fix in practice — recommend `git archive -o praxisiq.zip HEAD` for any future exports

## v2.6 — 2026-08-05
- docs: removed all direct references to a specific job posting/description throughout the codebase (deleted JD_MAPPING.md; reworded headers in api/risk_service.py, trust_safety/appeals_workflow.py, analytics/account_risk_scoring.py, analytics/ops_capacity_analysis.py, and 11 "at YouTube scale"-style lines in dashboards/app.py) — project now describes Trust & Safety domain work generically rather than being framed around one employer's listing
- docs: README.md "Dashboard Preview" — added 4 Enforcement & Ops screenshots (Account Enforcement, Appeals & Reinstatement, Abuse Vector Taxonomy, Real-Time Simulator)

## v2.5 — 2026-08-05
- feat: Real-time risk scoring service (api/risk_service.py) — FastAPI endpoint wrapping the batch severity logic, with a drift-guard test locking it to trust_safety_pipeline.py's actual output
- feat: run_all.py now wires in all Phase 2-5 scripts (account risk, appeals, ops capacity, label agreement) as Step 5, in dependency-correct order
- feat: New "Enforcement & Ops" dashboard page — 5 tabs (Account Enforcement, Appeals & Reinstatement, Abuse Vector Taxonomy, Ops Capacity, Real-Time Simulator), verified with Streamlit's AppTest framework (zero exceptions across all tabs)
- docs: README.md reordered — "Why this maps to Trust & Safety" now leads, ahead of screenshots/architecture
- fix: real f-string syntax bug caught during dashboard integration (nested-quote escaping) before it ever shipped
- test: 10 new tests for risk_service.py (72 total, up from 62)

## v2.4 — 2026-08-05
- docs: PROJECT_CHARTER.md — retrospective scope/goals/stakeholder mapping
- feat: Account-level enforcement scoring with strike-ladder actions (analytics/account_risk_scoring.py)
- feat: Appeals & reinstatement workflow, modeled and clearly disclosed as such (trust_safety/appeals_workflow.py)
- docs: ABUSE_VECTORS.md — abuse vector taxonomy grounded in real detector outputs
- docs: INCIDENT_CASE_STUDY.md — root-cause walkthrough of the largest detected burst day
- feat: Cohen's Kappa label-agreement tool with a real (unfilled-by-default) relabel sample (analytics/label_agreement_check.py)
- feat: Operations capacity analysis — real arrival rate + SLA-driven staffing (analytics/ops_capacity_analysis.py)
- fix: severity_distribution.csv column-naming bug (was producing a malformed 'Count,count' header)
- docs: README.md line-count and SETUP.md page-count/path corrections
- docs: SECURITY.md — documents secrets-handling pattern and a past zip-export leak, resolved
- test: 36 new tests added across 4 new test files (62 total, up from 26)

## v2.3 — 2026-06-29
- feat: Executive PDF Report generator on Overview page
- feat: Precision/Recall Experiment simulator with live confusion matrix
- feat: Tavily web search integration in AI Copilot

## v2.2 — 2026-06-28
- feat: Data Quality dashboard (missing values, duplicates, quality score)
- feat: AI Copilot powered by Groq Llama 3.1 8B with live DB context
- fix: Live At-Risk KPI pulled from followup_risk_queue.csv
- feat: delta_kpi() trend cards styled to match dark theme

## v2.1 — 2026-06-20
- feat: Investigation Playbooks with 5 signal types and step-by-step SOP
- feat: Queue Clearance Simulator with threshold sliders
- feat: Content Policy Enforcement Map with per-class recall
- fix: Corrected Communication recall (100%) and Staff recall (44%)

## v2.0 — 2026-06-01
- feat: Trust and Safety pipeline with moderation queue and risk scoring
- feat: LLM Evaluation page with prompt comparison and confusion matrix
- feat: ML vs LLM accuracy benchmark (82.22% vs 86.67%)
- feat: Anomaly Screening with burst detection and duplicate flagging

## v1.0 — 2026-05-01
- Initial release: Patient Analytics, Review Intelligence, Overview
- SQLite database with 959 patients, 4603 visits, 300 labeled reviews
- Statistical analysis: ANOVA F=5.37 p<0.001, Chi-Square, Z-score outliers

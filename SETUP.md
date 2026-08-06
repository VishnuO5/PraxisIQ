# PraxisIQ — Local Setup Guide

Get the full project running locally in under 10 minutes.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Git | any | https://git-scm.com/ |
| Ollama | latest | https://ollama.com/download |

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/VishnuO5/PraxisIQ.git
cd PraxisIQ/Data
```

---

## Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

For running the test suite too:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

---

## Step 3 — Set up Ollama (for LLM evaluation only)

Ollama runs the Qwen2.5 7B model locally. Required only if you want to re-run the LLM evaluation pipeline. The Streamlit dashboard works without it.

```bash
# 1. Install Ollama from https://ollama.com/download
# 2. Pull the model (downloads ~4.7 GB)
ollama pull qwen2.5:7b
# 3. Verify it's running
ollama list
```

Ollama must be running in the background before executing `llm/llm_evaluation_final.py`.

---

## Step 4 — Run the full pipeline (recommended, one command)

The SQLite database and all `reports/` CSVs are excluded from git (data privacy) and rebuilt locally. `run_all.py` builds the database from the source Excel file, runs every SQL and analytics script, the Trust & Safety pipeline, account risk scoring, appeals workflow, ops capacity analysis, and the ML classifier — in dependency-correct order — and verifies every expected output file exists at the end:

```bash
python run_all.py
```

Takes under 30 seconds. If any step fails, it tells you which one and stops there.

<details>
<summary>Manual step-by-step (equivalent to run_all.py, if you want to run pieces individually)</summary>

```bash
# 1. Build the database from the source Excel file
python create_database.py
# Expected output: 959 patients · 4,603 visits · 300 reviews loaded.

# 2. SQL analytics
python analytics/run_sql_analytics.py

# 3. Analytics scripts
python analytics/statistical_analysis.py
python analytics/treatment_risk_analysis.py
python analytics/visit_outlier_detection.py
python analytics/review_burst_detection.py
python analytics/suspicious_reviewer_detection.py
python analytics/duplicate_review_detection.py
python analytics/followup_risk_analysis.py
python analytics/emerging_risk_monitoring.py
python analytics/service_quality_analysis.py

# 4. Trust & Safety pipeline (moderation queue, risk scores)
python trust_safety/trust_safety_pipeline.py

# 5. Enforcement, appeals, ops capacity
python analytics/account_risk_scoring.py
python trust_safety/appeals_workflow.py
python analytics/ops_capacity_analysis.py
python analytics/label_agreement_check.py   # safe to skip if incomplete — see METHODOLOGY.md

# 6. ML classifier
python ml/review_classifier_v2.py
```

Optional, not run by `run_all.py` (requires Ollama running, takes ~15 minutes):

```bash
python llm/llm_evaluation_final.py
```

</details>

---

## Step 5 — Launch the dashboard

```bash
streamlit run dashboards/app.py
```

Opens at **http://localhost:8501**. Nine pages: Overview, Patient Analytics, Review Intelligence, Anomaly Screening, Trust & Safety, Enforcement & Ops, LLM Evaluation, Investigation Playbooks, Data Quality.

---

## Step 6 — (Optional) Run the real-time risk scoring API

```bash
uvicorn api.risk_service:app --reload
```

Opens at **http://localhost:8000**, interactive docs at **http://localhost:8000/docs**. Wraps the same severity/scoring logic as the batch pipeline as a per-item HTTP endpoint — see `api/risk_service.py` for the request schema, and `tests/test_risk_service.py` for the test that proves it matches the batch pipeline's output exactly.

---

## Step 7 — (Optional) Run the test suite

```bash
python -m pytest tests/ -v
```

72 tests. Requires Step 4 (`run_all.py`) to have been run first — several tests validate against real `reports/` output, not fixtures.

---

## Project structure

```
PraxisIQ/Data/
├── config.py                    # Central config — all thresholds, paths, model params
├── create_database.py           # Builds PraxisIQ.db from sample_data_synthetic.xlsx
├── run_all.py                   # Runs the entire pipeline end-to-end, one command
├── requirements.txt
├── requirements-dev.txt         # Adds pytest, for running tests/
├── .gitignore
├── dashboards/
│   └── app.py                   # Streamlit dashboard — 9 pages
├── api/
│   └── risk_service.py          # FastAPI real-time scoring service
├── analytics/                   # Standalone analysis scripts
│   ├── run_sql_analytics.py
│   ├── statistical_analysis.py
│   ├── treatment_risk_analysis.py
│   ├── visit_outlier_detection.py
│   ├── review_burst_detection.py
│   ├── suspicious_reviewer_detection.py
│   ├── duplicate_review_detection.py
│   ├── followup_risk_analysis.py
│   ├── emerging_risk_monitoring.py
│   ├── service_quality_analysis.py
│   ├── account_risk_scoring.py
│   ├── ops_capacity_analysis.py
│   └── label_agreement_check.py
├── trust_safety/
│   ├── trust_safety_pipeline.py # Unified T&S pipeline — risk scoring + moderation queue
│   └── appeals_workflow.py      # Detection → Enforcement → Appeal → Reinstatement
├── ml/
│   └── review_classifier_v2.py  # TF-IDF + Logistic Regression classifier (82.22%)
├── llm/
│   ├── llm_evaluation_final.py  # LLM prompt evaluation (Qwen2.5 7B, 86.67%)
│   ├── prompt_v1.txt
│   ├── prompt_v2.txt
│   └── prompt_v3.txt
├── sql/                         # 11 patient-analytics SQL queries
├── sql/trust_safety/            # 7 T&S SQL queries (CTEs, window functions)
├── tests/                       # 72 tests — pytest
├── docs/
│   └── INCIDENT_CASE_STUDY.md   # Root-cause 5-whys walkthrough of a real anomaly
├── reports/                     # CSV outputs from pipeline runs (gitignored)
└── assets/                      # Dashboard screenshots
```

---

## Logs

All pipeline scripts write to `logs/praxisiq.log` (auto-created, excluded from git).
View live logs during a run:

```bash
# Windows
Get-Content logs\praxisiq.log -Wait

# Mac/Linux
tail -f logs/praxisiq.log
```

---

## Live demo

**https://praxisiq.streamlit.app** — deployed on Streamlit Cloud, auto-updates on push to `main`.


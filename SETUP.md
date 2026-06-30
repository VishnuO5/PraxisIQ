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

## Step 4 — Build the database

The SQLite database is not included in the repo (excluded by `.gitignore` for data privacy). Build it from the source Excel file:

```bash
python create_database.py
```

This reads `sample_data_synthetic.xlsx` and creates `PraxisIQ.db` in the project root.
Expected output: `959 patients · 4,603 visits · 300 reviews loaded.`

---

## Step 5 — Run the analytics pipeline

Generate all CSV reports used by the dashboard:

```bash
# Trust & Safety pipeline (moderation queue, risk scores)
python trust_safety/trust_safety_pipeline.py

# Anomaly detection
python analytics/review_burst_detection.py
python analytics/visit_outlier_detection.py
python analytics/suspicious_reviewer_detection.py
python analytics/duplicate_review_detection.py
python analytics/emerging_risk_monitoring.py

# Patient analytics
python analytics/followup_risk_analysis.py
python analytics/treatment_risk_analysis.py
python analytics/service_quality_analysis.py
python analytics/statistical_analysis.py

# ML classifier (optional — trains and evaluates TF-IDF + Logistic Regression)
python ml/review_classifier_v2.py

# LLM evaluation (optional — requires Ollama running, takes ~15 minutes)
python llm/llm_evaluation_final.py
```

All outputs are saved to `reports/`.

---

## Step 6 — Launch the dashboard

```bash
streamlit run dashboards/app.py
```

Opens at **http://localhost:8501**

---

## Project structure

```
PraxisIQ/Data/
├── config.py                    # Central config — all thresholds, paths, model params
├── create_database.py           # Builds PraxisIQ.db from sample_data_synthetic.xlsx
├── requirements.txt
├── .gitignore
├── dashboards/
│   └── app.py                   # Streamlit dashboard — 6 pages
├── analytics/                   # Standalone analysis scripts
│   ├── review_burst_detection.py
│   ├── visit_outlier_detection.py
│   ├── suspicious_reviewer_detection.py
│   ├── duplicate_review_detection.py
│   ├── emerging_risk_monitoring.py
│   ├── followup_risk_analysis.py
│   ├── treatment_risk_analysis.py
│   ├── service_quality_analysis.py
│   └── statistical_analysis.py
├── trust_safety/
│   └── trust_safety_pipeline.py # Unified T&S pipeline — risk scoring + moderation queue
├── ml/
│   └── review_classifier_v2.py  # TF-IDF + Logistic Regression classifier (82.22%)
├── llm/
│   ├── llm_evaluation_final.py  # LLM prompt evaluation (Qwen2.5 7B, 86.67%)
│   ├── prompt_v1.txt
│   ├── prompt_v2.txt
│   └── prompt_v3.txt
├── sql/trust_safety/            # 7 T&S SQL queries (CTEs, window functions)
├── reports/                     # CSV outputs from pipeline runs
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
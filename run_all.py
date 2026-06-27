"""
run_all.py
==========
Single entry point that runs the entire PraxisIQ pipeline in sequence.

Usage:
    python run_all.py

Steps:
    1. Build database from Patient_Data.xlsx
    2. Run SQL analytics
    3. Run all analytics scripts
    4. Run Trust & Safety pipeline
    5. Verify all expected outputs exist
"""

import os
import sys
import time
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# ── COLORS FOR TERMINAL OUTPUT ────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def step(number, text):
    print(f"{BOLD}[{number}] {text}{RESET}")

def success(text):
    print(f"  {GREEN}✓ {text}{RESET}")

def failure(text):
    print(f"  {RED}✗ {text}{RESET}")

def warning(text):
    print(f"  {YELLOW}⚠ {text}{RESET}")

def run_script(label, script_path):
    """Run a Python script and return True if it succeeded."""
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=ROOT
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            success(f"{label} ({elapsed:.1f}s)")
            return True
        else:
            failure(f"{label} — exit code {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().splitlines()[-5:]:
                    print(f"      {RED}{line}{RESET}")
            return False
    except Exception as e:
        failure(f"{label} — {e}")
        return False

# ── PIPELINE ──────────────────────────────────────────────────────────────────

header("PraxisIQ — Full Pipeline Runner")
print(f"  Root : {ROOT}")
print(f"  Python: {sys.executable}")

total_start = time.time()
results = {}

# ── STEP 1: DATABASE ──────────────────────────────────────────────────────────
step(1, "Building database from Patient_Data.xlsx")

if not os.path.exists("Patient_Data.xlsx"):
    failure("Patient_Data.xlsx not found — cannot continue")
    sys.exit(1)

results["create_database"] = run_script(
    "Database builder", "create_database.py"
)

if not results["create_database"]:
    failure("Database creation failed — stopping pipeline")
    sys.exit(1)

# ── STEP 2: SQL ANALYTICS ─────────────────────────────────────────────────────
step(2, "Running SQL analytics")

results["run_sql_analytics"] = run_script(
    "SQL analytics runner", "analytics/run_sql_analytics.py"
)

# ── STEP 3: PYTHON ANALYTICS SCRIPTS ─────────────────────────────────────────
step(3, "Running analytics scripts")

analytics_scripts = [
    ("Statistical analysis",          "analytics/statistical_analysis.py"),
    ("Treatment risk analysis",       "analytics/treatment_risk_analysis.py"),
    ("Visit outlier detection",       "analytics/visit_outlier_detection.py"),
    ("Review burst detection",        "analytics/review_burst_detection.py"),
    ("Suspicious reviewer detection", "analytics/suspicious_reviewer_detection.py"),
    ("Duplicate review detection",    "analytics/duplicate_review_detection.py"),
    ("Follow-up risk analysis",       "analytics/followup_risk_analysis.py"),
    ("Emerging risk monitoring",      "analytics/emerging_risk_monitoring.py"),
    ("Service quality analysis",      "analytics/service_quality_analysis.py"),
]

for label, path in analytics_scripts:
    results[path] = run_script(label, path)

# ── STEP 4: TRUST & SAFETY PIPELINE ──────────────────────────────────────────
step(4, "Running Trust & Safety pipeline")

results["trust_safety_pipeline"] = run_script(
    "Trust & Safety pipeline", "trust_safety/trust_safety_pipeline.py"
)

# ── STEP 5: ML CLASSIFIER ────────────────────────────────────────────────────
step(5, "Running ML classifier")

results["ml_classifier"] = run_script(
    "ML classifier (TF-IDF + Logistic Regression)", "ml/review_classifier_v2.py"
)

# ── STEP 6: VERIFY OUTPUTS ───────────────────────────────────────────────────
step(6, "Verifying expected outputs")

expected_outputs = [
    "reports/statistical_analysis.csv",
    "reports/treatment_risk_analysis.csv",
    "reports/visit_outliers.csv",
    "reports/review_burst_detection.csv",
    "reports/suspicious_reviewer_detection.csv",
    "reports/duplicate_review_detection.csv",
    "reports/service_quality_analysis.csv",
    "reports/trust_safety_metrics.csv",
    "reports/moderation_queue.csv",
    "reports/case_management_queue.csv",
    "reports/trust_safety_risk_summary.csv",
    "reports/severity_distribution.csv",
    "reports/llm_prompt_evaluation.csv",
]

all_outputs_exist = True
for output in expected_outputs:
    if os.path.exists(output):
        success(f"Found: {output}")
    else:
        warning(f"Missing: {output}")
        all_outputs_exist = False

# ── SUMMARY ───────────────────────────────────────────────────────────────────

total_elapsed = time.time() - total_start
passed = sum(1 for v in results.values() if v)
failed = sum(1 for v in results.values() if not v)

header("Pipeline Summary")
print(f"  Scripts run    : {len(results)}")
print(f"  {GREEN}Passed         : {passed}{RESET}")
if failed > 0:
    print(f"  {RED}Failed         : {failed}{RESET}")
print(f"  Outputs verified: {'All present' if all_outputs_exist else 'Some missing — check above'}")
print(f"  Total time     : {total_elapsed:.1f}s")

if failed == 0 and all_outputs_exist:
    print(f"\n{GREEN}{BOLD}  Pipeline complete. Run the dashboard:{RESET}")
    print(f"  {BOLD}streamlit run dashboards/app.py{RESET}\n")
else:
    print(f"\n{YELLOW}{BOLD}  Pipeline finished with issues. Check failed scripts above.{RESET}\n")
"""
create_database.py
==================
Builds PraxisIQ.db from Patient_Data.xlsx.

Run this first before launching the dashboard:
    python create_database.py

Requirements:
    pip install pandas openpyxl
"""

import os
import sys
import sqlite3
import pandas as pd

EXCEL_FILE = "Patient_Data.xlsx"
DB_FILE    = "PraxisIQ.db"

# ── PRE-FLIGHT CHECKS ────────────────────────────────────────────────────────

if not os.path.exists(EXCEL_FILE):
    print(f"\n[ERROR] '{EXCEL_FILE}' not found in the current directory.")
    print(f"        Make sure you're running this from the project root:")
    print(f"        cd path/to/PraxisIQ && python create_database.py\n")
    sys.exit(1)

print(f"\nPraxisIQ — Database Builder")
print("=" * 50)
print(f"Source  : {EXCEL_FILE}")
print(f"Output  : {DB_FILE}")

# ── LOAD EXCEL SHEETS ────────────────────────────────────────────────────────

try:
    print("\nLoading sheets from Excel...")
    patients = pd.read_excel(EXCEL_FILE, sheet_name="Patients")
    visits   = pd.read_excel(EXCEL_FILE, sheet_name="Visits")
    reviews  = pd.read_excel(EXCEL_FILE, sheet_name="Reviews")
    print(f"  Patients : {len(patients)} rows")
    print(f"  Visits   : {len(visits)} rows")
    print(f"  Reviews  : {len(reviews)} rows")
except FileNotFoundError:
    print(f"\n[ERROR] Could not find '{EXCEL_FILE}'.")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] Failed to read Excel file: {e}")
    print("  Make sure the file is not open in Excel and has sheets named 'Patients', 'Visits', 'Reviews'.")
    sys.exit(1)

# ── VALIDATE REQUIRED COLUMNS ────────────────────────────────────────────────

required = {
    "Patients": ["Primary_Treatment"],
    "Visits"  : ["Treatment_Type"],
    "Reviews" : ["Review_Text", "Label", "Rating", "Review_Date"],
}

all_ok = True
for sheet, cols in required.items():
    df = {"Patients": patients, "Visits": visits, "Reviews": reviews}[sheet]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print(f"\n[ERROR] Sheet '{sheet}' is missing columns: {missing}")
        all_ok = False

if not all_ok:
    print("\nDatabase creation aborted due to missing columns.")
    sys.exit(1)

# ── TREATMENT NAME STANDARDIZATION ──────────────────────────────────────────

treatment_map = {
    "root Canal"                : "Root Canal",
    "Root Canal "               : "Root Canal",
    "Aligners"                  : "Aligner",
    "Braces"                    : "Metal Braces Treatment",
    "Ceramic Braces Treatment"  : "Metal Braces Treatment",
    "Deep Cleaning"             : "Deep Scaling and Root Planing",
    "Gum Surgery"               : "Gum Treatment",
    "Scaling "                  : "Scaling",
    "Scaling and Filling"       : "Scaling",
    "Scaling and Polishing"     : "Scaling and Polishing",
    "Teeth Cleaning"            : "Teeth Cleaning",
    "Wisdom Tooth Extraction"   : "Tooth Extraction",
}

patients["Primary_Treatment"] = (
    patients["Primary_Treatment"]
    .str.strip()
    .replace(treatment_map)
)

visits["Treatment_Type"] = (
    visits["Treatment_Type"]
    .str.strip()
    .replace(treatment_map)
)

print("\nStandardized Treatment Names:")
print(" ", sorted(patients["Primary_Treatment"].dropna().unique()))

# ── CREATE DATABASE ──────────────────────────────────────────────────────────

try:
    conn = sqlite3.connect(DB_FILE)

    patients.to_sql("Patients", conn, if_exists="replace", index=False)
    visits.to_sql("Visits",     conn, if_exists="replace", index=False)
    reviews.to_sql("Reviews",   conn, if_exists="replace", index=False)

    for table in ["Patients", "Visits", "Reviews"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows written to database")

    conn.close()

    print(f"\n[SUCCESS] {DB_FILE} created successfully.")
    print(f"\nNext step: streamlit run dashboards/app.py\n")

except sqlite3.Error as e:
    print(f"\n[ERROR] Database write failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    sys.exit(1)
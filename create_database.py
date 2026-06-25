import pandas as pd
import sqlite3

# Read Excel sheets
patients = pd.read_excel("Patient_Data.xlsx", sheet_name="Patients")
visits = pd.read_excel("Patient_Data.xlsx", sheet_name="Visits")
reviews = pd.read_excel("Patient_Data.xlsx", sheet_name="Reviews")

# ── TREATMENT NAME STANDARDIZATION ──────────────────────────────────────────
# Maps all variants to one clean standard name
treatment_map = {
    "root Canal":                    "Root Canal",
    "Root Canal ":                   "Root Canal",
    "Aligners":                      "Aligner",
    "Braces":                        "Metal Braces Treatment",
    "Ceramic Braces Treatment":      "Metal Braces Treatment",
    "Deep Cleaning":                 "Deep Scaling and Root Planing",
    "Gum Surgery":                   "Gum Treatment",
    "Scaling ":                      "Scaling",
    "Scaling and Filling":           "Scaling",
    "Scaling and Polishing":         "Scaling and Polishing",
    "Teeth Cleaning":                "Teeth Cleaning",
    "Wisdom Tooth Extraction":       "Tooth Extraction",
}

# Apply to Patients sheet
patients["Primary_Treatment"] = (
    patients["Primary_Treatment"]
    .str.strip()
    .replace(treatment_map)
)

# Apply to Visits sheet
visits["Treatment_Type"] = (
    visits["Treatment_Type"]
    .str.strip()
    .replace(treatment_map)
)

# ── VERIFY STANDARDIZATION ───────────────────────────────────────────────────
print("\nStandardized Treatment Names:")
print(sorted(patients["Primary_Treatment"].unique()))

# ── CREATE DATABASE ──────────────────────────────────────────────────────────
conn = sqlite3.connect("PraxisIQ.db")

patients.to_sql("Patients", conn, if_exists="replace", index=False)
visits.to_sql("Visits", conn, if_exists="replace", index=False)
reviews.to_sql("Reviews", conn, if_exists="replace", index=False)

print("\nDatabase created successfully!")
print("Patients rows:", len(patients))
print("Visits rows:", len(visits))
print("Reviews rows:", len(reviews))

conn.close()
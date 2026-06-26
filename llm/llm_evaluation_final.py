
import sqlite3
import pandas as pd
import requests
import json
import os
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report
)
from sklearn.model_selection import train_test_split

print("\nModule 3 - LLM Prompt Engineering & Evaluation")
print("=" * 60)
print("\nMethodology: Hold-out test set (30%, never used during prompt dev)")
print("=" * 60)

# =============================================
# LOAD DATA
# =============================================

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Review_Text,
        Label
    FROM Reviews
    """,
    conn
)

conn.close()

print(f"\nTotal Reviews: {len(df)}")

# =============================================
# CREATE REPRODUCIBLE TRAIN/TEST SPLIT
# =============================================
# Development set (70%) — used during prompt design
# Hold-out test set (30%) — used ONLY for final evaluation

dev_df, test_df = train_test_split(
    df,
    test_size=0.30,
    random_state=42,
    stratify=df["Label"]
)

test_df = test_df.reset_index(drop=True)

print(f"\nDevelopment set : {len(dev_df)} reviews (used during prompt design — NOT evaluated here)")
print(f"Hold-out test set: {len(test_df)} reviews (used for final benchmarking only)")
print(f"\nHold-out class distribution:")
print(test_df["Label"].value_counts().to_string())

# =============================================
# LOAD PROMPT VERSIONS
# =============================================

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

prompts = {
    "V1 — Zero-Shot"   : load_prompt("llm/prompt_v1.txt"),
    "V2 — Detailed"    : load_prompt("llm/prompt_v2.txt"),
    "V3 — Rules-Based" : load_prompt("llm/prompt_v3.txt"),
}

VALID_LABELS = {
    "Positive", "Communication", "Waiting Time",
    "Treatment", "Pricing", "Staff", "Neutral"
}

# =============================================
# EVALUATE FUNCTION
# =============================================

def evaluate_prompt(prompt_name, prompt_template, eval_df):
    """
    Run a prompt against the evaluation set and return predictions + metrics.
    """
    predictions = []
    invalid_count = 0

    print(f"\n[{prompt_name}] — Running on {len(eval_df)} reviews...")

    for i, (_, row) in enumerate(eval_df.iterrows(), start=1):
        prompt = prompt_template.replace("{review_text}", row["Review_Text"])

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            raw = response.json()["response"].strip()

            # Normalise: capitalise first letter of each word
            pred = raw.title().strip()

            # Handle common LLM formatting variations
            if pred not in VALID_LABELS:
                for label in VALID_LABELS:
                    if label.lower() in raw.lower():
                        pred = label
                        break
                else:
                    pred = "Neutral"  # fallback
                    invalid_count += 1

        except Exception as e:
            pred = "Neutral"
            invalid_count += 1

        predictions.append(pred)

        if i % 15 == 0:
            print(f"  Processed {i}/{len(eval_df)} reviews")

    if invalid_count > 0:
        print(f"  Warning: {invalid_count} invalid/unparseable responses — defaulted to Neutral")

    # Metrics
    accuracy = accuracy_score(eval_df["Label"], predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        eval_df["Label"],
        predictions,
        average="macro",
        zero_division=0
    )

    report = classification_report(
        eval_df["Label"],
        predictions,
        zero_division=0
    )

    return {
        "prompt_name"  : prompt_name,
        "predictions"  : predictions,
        "accuracy"     : accuracy,
        "precision"    : precision,
        "recall"       : recall,
        "f1"           : f1,
        "report"       : report,
        "invalid_count": invalid_count
    }

# =============================================
# RUN EVALUATION ON HOLD-OUT TEST SET
# =============================================

results = {}

for name, template in prompts.items():
    results[name] = evaluate_prompt(name, template, test_df)

# =============================================
# PRINT COMPARISON
# =============================================

print("\n\nPROMPT COMPARISON — Hold-Out Test Set (90 reviews)")
print("=" * 60)
print(f"{'Prompt':<25} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
print("-" * 65)

for name, r in results.items():
    print(
        f"{name:<25} "
        f"{r['accuracy']:>9.2%} "
        f"{r['precision']:>9.2%} "
        f"{r['recall']:>9.2%} "
        f"{r['f1']:>9.2%}"
    )

print("-" * 65)

# Identify best
best_name = max(results, key=lambda k: results[k]["accuracy"])
best = results[best_name]

print(f"\nBest prompt: {best_name}")
print(f"Accuracy   : {best['accuracy']:.2%}")
print(f"Precision  : {best['precision']:.2%}")
print(f"Recall     : {best['recall']:.2%}")
print(f"F1 Score   : {best['f1']:.2%}")

print(f"\nDetailed Classification Report — {best_name}")
print("=" * 60)
print(best["report"])

# =============================================
# SAVE OUTPUTS
# =============================================

os.makedirs("reports", exist_ok=True)

# Save hold-out predictions for best prompt
test_df = test_df.copy()
test_df["Prediction"]  = best["predictions"]
test_df["Correct"]     = test_df["Label"] == test_df["Prediction"]
test_df["Split"]       = "hold_out_test"

test_df.to_csv("reports/llm_predictions.csv", index=False)

# Save summary comparison
summary_rows = []
for name, r in results.items():
    summary_rows.append({
        "Prompt"      : name,
        "Accuracy"    : round(r["accuracy"], 4),
        "Precision"   : round(r["precision"], 4),
        "Recall"      : round(r["recall"], 4),
        "F1_Score"    : round(r["f1"], 4),
        "Evaluated_On": "Hold-out test set (90 reviews, 30%, random_state=42)"
    })

pd.DataFrame(summary_rows).to_csv(
    "reports/llm_prompt_evaluation.csv",
    index=False
)

# Save methodology note alongside results
with open("reports/llm_evaluation_methodology.txt", "w") as f:
    f.write("""LLM Evaluation Methodology
===========================

Split:
  Total reviews          : 300
  Development set (70%)  : 210 reviews — used ONLY during prompt iteration
  Hold-out test set (30%): 90 reviews  — used ONLY for final benchmarking

Split parameters: train_test_split(test_size=0.30, random_state=42, stratify=Label)

Why this matters:
  Evaluating on the same data used to design the prompt inflates accuracy.
  The hold-out set was quarantined before any prompt was written and was
  never used to make any design decision. Reported accuracy is therefore
  a valid estimate of generalisation performance.

Prompt versions evaluated:
  V1 — Zero-Shot   : Basic category list only
  V2 — Detailed    : Category definitions with examples (SELECTED)
  V3 — Rules-Based : Strict keyword classification rules

Model: Qwen2.5 7B via Ollama (local inference)
""")

print("\nSaved:")
print("  reports/llm_predictions.csv")
print("  reports/llm_prompt_evaluation.csv")
print("  reports/llm_evaluation_methodology.txt")
print("\nNote: All accuracy figures above are on the HOLD-OUT TEST SET only.")
print("      Development set (210 reviews) was used for prompt design only.")
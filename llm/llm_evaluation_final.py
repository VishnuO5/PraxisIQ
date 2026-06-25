import sqlite3
import pandas as pd
import requests

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report
)

print("\nModule 3 - Real LLM Prompt Evaluation")
print("=" * 60)

# =====================================
# LOAD DATA
# =====================================

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

# =====================================
# LOAD BEST PROMPT (V2)
# =====================================

with open(
    "llm/prompt_v2.txt",
    "r",
    encoding="utf-8"
) as f:
    prompt_template = f.read()

# =====================================
# GENERATE PREDICTIONS
# =====================================

predictions = []

print("\nGenerating predictions...")

for i, review in enumerate(df["Review_Text"], start=1):

    prompt = prompt_template.replace(
        "{review_text}",
        review
    )

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False
        }
    )

    prediction = response.json()["response"].strip()

    predictions.append(prediction)

    if i % 25 == 0:
        print(f"Processed {i}/{len(df)} reviews")

# =====================================
# METRICS
# =====================================

accuracy = accuracy_score(
    df["Label"],
    predictions
)

precision, recall, f1, _ = precision_recall_fscore_support(
    df["Label"],
    predictions,
    average="macro",
    zero_division=0
)

print("\nResults")
print("=" * 60)

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")

print("\nClassification Report")
print("=" * 60)

report = classification_report(
    df["Label"],
    predictions,
    zero_division=0
)

print(report)

# =====================================
# SAVE REVIEW PREDICTIONS
# =====================================

df["Prediction"] = predictions

df.to_csv(
    "reports/llm_predictions.csv",
    index=False
)

# =====================================
# SAVE SUMMARY
# =====================================

summary = pd.DataFrame({
    "Metric": [
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score"
    ],
    "Value": [
        round(accuracy, 4),
        round(precision, 4),
        round(recall, 4),
        round(f1, 4)
    ]
})

summary.to_csv(
    "reports/llm_prompt_evaluation.csv",
    index=False
)

print("\nSaved:")
print("reports/llm_predictions.csv")
print("reports/llm_prompt_evaluation.csv")
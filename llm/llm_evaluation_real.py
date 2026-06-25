import sqlite3
import pandas as pd
import requests
from sklearn.metrics import accuracy_score

print("\nLLM Prompt Evaluation - Prompt V3")
print("=" * 50)

# =========================
# LOAD REVIEWS
# =========================

conn = sqlite3.connect("PraxisIQ.db")

df = pd.read_sql_query(
    """
    SELECT
        Review_Text,
        Label
    FROM Reviews
    LIMIT 20
    """,
    conn
)

conn.close()

print(f"\nLoaded {len(df)} reviews")

# =========================
# LOAD PROMPT V3
# =========================

with open(
    "llm/prompt_v3.txt",
    "r",
    encoding="utf-8"
) as f:
    prompt_template = f.read()

predictions = []

# =========================
# RUN OLLAMA
# =========================

print("\nGenerating predictions...\n")

for review in df["Review_Text"]:

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

# =========================
# EVALUATE
# =========================

accuracy = accuracy_score(
    df["Label"],
    predictions
)

df["Prediction"] = predictions

# =========================
# RESULTS
# =========================

print("\nPrediction Distribution:")
print("-" * 50)
print(pd.Series(predictions).value_counts())

print("\nAccuracy:")
print("-" * 50)
print(f"{round(accuracy * 100, 2)}%")

print("\nSample Predictions:")
print("-" * 50)

print(
    df[
        [
            "Review_Text",
            "Label",
            "Prediction"
        ]
    ].head(10)
)

print("\nEvaluation Complete.")
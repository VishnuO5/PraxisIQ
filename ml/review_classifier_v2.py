import os
import sys
import sqlite3
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from scipy.stats import norm as _norm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    REPORTS_DIR,
    ML_TEST_SIZE,
    ML_RANDOM_STATE,
    ML_MAX_FEATURES,
    ML_NGRAM_RANGE,
    ML_MAX_ITER,
    ML_CLASS_WEIGHT,
    get_logger,
)

log = get_logger(__name__)

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT Review_Text, Label FROM Reviews", conn)
conn.close()

X = df["Review_Text"]
y = df["Label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=ML_TEST_SIZE,
    random_state=ML_RANDOM_STATE,
    stratify=y
)

vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=ML_MAX_FEATURES,
    ngram_range=ML_NGRAM_RANGE
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf  = vectorizer.transform(X_test)

model = LogisticRegression(
    max_iter=ML_MAX_ITER,
    class_weight=ML_CLASS_WEIGHT
)

model.fit(X_train_tfidf, y_train)
y_pred   = model.predict(X_test_tfidf)
accuracy = accuracy_score(y_test, y_pred)

# ── CONFIDENCE INTERVAL ON ACCURACY ──────────────────────────────────────────
# Wilson score interval — more accurate than normal approximation
# especially for proportions near 0 or 1 and small sample sizes.
# n = number of test samples, p = accuracy

n           = len(y_test)
z           = _norm.ppf(0.975)        # 95% confidence, two-tailed
p           = accuracy
denominator = 1 + z**2 / n
centre      = (p + z**2 / (2 * n)) / denominator
margin      = (z * ((p * (1 - p) / n) + z**2 / (4 * n**2))**0.5) / denominator
ci_lower    = round((centre - margin) * 100, 1)
ci_upper    = round((centre + margin) * 100, 1)

log.info("Review Classification V2 starting")
log.info(
    "Accuracy: %.2f%% (95%% CI: %.1f%% – %.1f%%, n=%d, Wilson interval)",
    round(accuracy * 100, 2), ci_lower, ci_upper, n
)
log.info(
    "Interpretation: If this model were re-evaluated on a new random "
    "sample of %d reviews from the same population, we would expect "
    "accuracy to fall between %.1f%% and %.1f%% 95%% of the time.",
    n, ci_lower, ci_upper
)
log.info("Classification Report:")
log.info("\n%s", classification_report(y_test, y_pred))
log.info("Confusion Matrix:")
log.info("\n%s", confusion_matrix(y_test, y_pred))

# ── SAVE ACCURACY WITH CI TO REPORTS ─────────────────────────────────────────
os.makedirs(REPORTS_DIR, exist_ok=True)
pd.DataFrame({
    "Metric": ["Accuracy", "CI_Lower_95", "CI_Upper_95", "Sample_Size", "CI_Method"],
    "Value" : [round(accuracy * 100, 2), ci_lower, ci_upper, n, "Wilson Score Interval"]
}).to_csv(os.path.join(REPORTS_DIR, "ml_accuracy_with_ci.csv"), index=False)
log.info("Saved: reports/ml_accuracy_with_ci.csv")
import os
import sys
import sqlite3
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DB_PATH,
    ML_TEST_SIZE,
    ML_RANDOM_STATE,
    ML_MAX_FEATURES,
    ML_NGRAM_RANGE,
    ML_MAX_ITER,
    ML_CLASS_WEIGHT,
)

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

print("\nReview Classification V2")
print("=" * 50)
print(f"\nAccuracy: {round(accuracy * 100, 2)}%")
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))
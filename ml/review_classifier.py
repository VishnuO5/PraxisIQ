import sqlite3
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# Connect to database
conn = sqlite3.connect("PraxisIQ.db")

# Load reviews
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

print("\nDataset Shape:")
print(df.shape)

# Features and Target
X = df["Review_Text"]
y = df["Label"]

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=3000
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Model
model = LogisticRegression(
    max_iter=1000
)

model.fit(
    X_train_tfidf,
    y_train
)

# Predictions
y_pred = model.predict(X_test_tfidf)

# Metrics
accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\nAccuracy:")
print(round(accuracy * 100, 2))

print("\nClassification Report:\n")
print(
    classification_report(
        y_test,
        y_pred
    )
)

print("\nConfusion Matrix:\n")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)
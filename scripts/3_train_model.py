"""
3_train_model.py

Trains a Random Forest classifier on the landmark data collected by
2_collect_data.py, and saves the trained model to gesture_model.pkl.

Usage:
    python 3_train_model.py
"""

import os
import pandas as pd
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "gesture_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "gesture_model.pkl")


def main():
    print(f"Loading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows.")

    if "session_id" not in df.columns:
        raise ValueError(
            "No 'session_id' column found in gesture_data.csv. "
            "This CSV was recorded with an older version of 2_collect_data.py. "
            "See the migration note below before running this script."
        )

    print("Rows per gesture:")
    print(df["label"].value_counts())
    print(f"\nNumber of distinct recording sessions: {df['session_id'].nunique()}")

    X = df.drop(columns=["label", "session_id"])
    y = df["label"]
    groups = df["session_id"]

    # Split by session, not by row: every row from a given session_id ends up
    # entirely in train OR entirely in test, never split across both. This
    # stops near-duplicate consecutive frames from the same recording run
    # from leaking between train and test and inflating accuracy.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    print(f"Train sessions: {groups.iloc[train_idx].nunique()}  |  Test sessions: {groups.iloc[test_idx].nunique()}")

    print("\nTraining RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nTest accuracy: {acc:.4f}")
    print("\nConfusion matrix (rows=actual, cols=predicted):")
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print("Labels:", labels)
    print(cm)

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, labels=labels))

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {os.path.abspath(MODEL_PATH)}")
    print(f"Record this accuracy ({acc:.2%}) for your submission form / demo narration.")


if __name__ == "__main__":
    main()
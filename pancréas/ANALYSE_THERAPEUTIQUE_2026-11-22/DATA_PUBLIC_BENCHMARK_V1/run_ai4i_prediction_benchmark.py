#!/usr/bin/env python
"""Run a transparent, time-ordered prediction benchmark separate from T0 analysis."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


HERE = Path(__file__).resolve().parent
CSV = HERE / "source" / "ai4i2020.csv"
OUT = HERE / "prediction_benchmark_v1"
OUT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


df = pd.read_csv(CSV)
target_name = "Machine failure"
target_leakage = {"TWF", "HDF", "PWF", "OSF", "RNF", target_name}
features = [
    "Type", "Air temperature [K]", "Process temperature [K]",
    "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
]
expected_failure_flags = target_leakage - {target_name}
if not expected_failure_flags.issubset(df.columns) or not set(features).issubset(df.columns):
    raise ValueError("Dataset schema differs from the documented AI4I 2020 schema.")
if df["UDI"].duplicated().any() or not df["UDI"].is_monotonic_increasing:
    raise ValueError("UDI order is not unique and increasing; chronological split assumptions must be revisited.")

y_all = df[target_name].astype(int).to_numpy()
numeric_features = [c for c in features if c != "Type"]
categorical_features = ["Type"]
numeric_preprocess = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale", StandardScaler()),
])
categorical_preprocess = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("encode", OneHotEncoder(handle_unknown="ignore")),
])
preprocess = ColumnTransformer([
    ("numeric", numeric_preprocess, numeric_features),
    ("categorical", categorical_preprocess, categorical_features),
])
folds = [(0, 4000, 4000, 6000), (0, 6000, 6000, 8000), (0, 8000, 8000, 10000)]
models = {
    "most_frequent_baseline": DummyClassifier(strategy="most_frequent"),
    "logistic_regression_balanced": Pipeline([
        ("preprocess", preprocess),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=20261122)),
    ]),
    "random_forest_balanced": Pipeline([
        ("preprocess", preprocess),
        ("model", RandomForestClassifier(
            n_estimators=300, class_weight="balanced", min_samples_leaf=2,
            random_state=20261122, n_jobs=1,
        )),
    ]),
}

records = []
predictions = []
for fold_number, (train_start, train_end, test_start, test_end) in enumerate(folds, 1):
    X_train = df.iloc[train_start:train_end][features]
    y_train = y_all[train_start:train_end]
    X_test = df.iloc[test_start:test_end][features]
    y_test = y_all[test_start:test_end]
    if len(np.unique(y_test)) != 2 or len(np.unique(y_train)) != 2:
        raise ValueError(f"Fold {fold_number} lacks one class in train or test.")
    for name, estimator in models.items():
        estimator.fit(X_train, y_train)
        if hasattr(estimator, "predict_proba"):
            probabilities = estimator.predict_proba(X_test)[:, 1]
        else:
            probabilities = np.full(len(y_test), float(y_train.mean()))
        predictions_binary = (probabilities >= 0.5).astype(int)
        matrix = confusion_matrix(y_test, predictions_binary, labels=[0, 1])
        records.append({
            "fold": fold_number,
            "model": name,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "train_uid_min": int(df.iloc[train_start]["UDI"]),
            "train_uid_max": int(df.iloc[train_end - 1]["UDI"]),
            "test_uid_min": int(df.iloc[test_start]["UDI"]),
            "test_uid_max": int(df.iloc[test_end - 1]["UDI"]),
            "train_failure_prevalence": float(y_train.mean()),
            "test_failure_prevalence": float(y_test.mean()),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
            "average_precision": float(average_precision_score(y_test, probabilities)),
            "balanced_accuracy_at_0_5": float(balanced_accuracy_score(y_test, predictions_binary)),
            "precision_at_0_5": float(precision_score(y_test, predictions_binary, zero_division=0)),
            "recall_at_0_5": float(recall_score(y_test, predictions_binary, zero_division=0)),
            "f1_at_0_5": float(f1_score(y_test, predictions_binary, zero_division=0)),
            "tn": int(matrix[0, 0]), "fp": int(matrix[0, 1]),
            "fn": int(matrix[1, 0]), "tp": int(matrix[1, 1]),
        })
        predictions.extend({
            "fold": fold_number,
            "model": name,
            "UDI": int(df.iloc[test_start + i]["UDI"]),
            "observed_failure": int(y_test[i]),
            "predicted_probability": float(probabilities[i]),
            "predicted_at_0_5": int(predictions_binary[i]),
        } for i in range(len(y_test)))

summary = pd.DataFrame.from_records(records)
summary.to_csv(OUT / "fold_metrics.csv", index=False, float_format="%.10g")
pd.DataFrame.from_records(predictions).to_csv(OUT / "holdout_predictions.csv", index=False, float_format="%.10g")
manifest = {
    "status": "complete",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "dataset_sha256": sha256(CSV),
    "rows": len(df),
    "target": target_name,
    "positive_rows": int(y_all.sum()),
    "positive_prevalence": float(y_all.mean()),
    "features": features,
    "excluded_identifier": "UDI (used only to preserve order and define forward holdouts)",
    "excluded_label_leakage_columns": sorted(expected_failure_flags),
    "split": "three expanding-window forward holdouts; each test block is the next 2,000 observations; no random shuffle",
    "threshold": "0.5 for classification metrics; ROC-AUC and average precision use predicted probability",
    "models": ["most_frequent_baseline", "logistic_regression_balanced", "random_forest_balanced"],
    "limitations": [
        "This AI4I dataset is synthetic, not a real factory cohort.",
        "These are prediction benchmark metrics; they do not validate T0, TLog, causal effects, or medical use.",
        "The pipeline itself is not used as a classifier in this benchmark; its analysis runs are a separate experiment.",
        "Forward splitting is based on UDI order; UDI is an identifier, not a validated physical clock.",
    ],
    "python": sys.version,
    "platform": platform.platform(),
    "scikit_learn": sklearn.__version__,
    "numpy": np.__version__,
    "pandas": pd.__version__,
    "script_sha256": sha256(Path(__file__).resolve()),
    "model_parameters": {
        "most_frequent_baseline": {"strategy": "most_frequent"},
        "logistic_regression_balanced": {"max_iter": 2000, "class_weight": "balanced", "random_state": 20261122},
        "random_forest_balanced": {
            "n_estimators": 300, "class_weight": "balanced", "min_samples_leaf": 2,
            "random_state": 20261122, "n_jobs": 1,
        },
    },
    "summary_csv_sha256": sha256(OUT / "fold_metrics.csv"),
    "predictions_csv_sha256": sha256(OUT / "holdout_predictions.csv"),
}
(OUT / "benchmark_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(summary.to_string(index=False))
print(json.dumps({k: manifest[k] for k in ["status", "positive_rows", "positive_prevalence", "split", "limitations"]}, indent=2, ensure_ascii=False))

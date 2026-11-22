#!/usr/bin/env python
"""Leakage-aware chronological hourly rental-count benchmark."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


HERE = Path(__file__).resolve().parent
DATA = HERE / "source" / "hour.csv"
OUT = HERE / "prediction_benchmark_v3"
FEATURES = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit", "temp", "atemp", "hum", "windspeed"]
CATEGORICAL = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit"]
CONTINUOUS = ["temp", "atemp", "hum", "windspeed"]
TARGET = "cnt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    frame = pd.read_csv(DATA, parse_dates=["dteday"])
    if len(frame) != 17379 or not frame["instant"].is_monotonic_increasing:
        raise ValueError("Source row count/order differs from the frozen protocol.")
    if not np.array_equal(frame["casual"].to_numpy() + frame["registered"].to_numpy(), frame[TARGET].to_numpy()):
        raise ValueError("Expected casual + registered == cnt; leakage exclusion must be reviewed.")
    if frame[FEATURES + [TARGET]].isna().any().any():
        raise ValueError("Unexpected missing value in selected columns.")
    n = len(frame)
    folds = [
        ("expanding_50_to_75", 0, int(n * 0.50), int(n * 0.50), int(n * 0.75)),
        ("expanding_75_to_100", 0, int(n * 0.75), int(n * 0.75), n),
    ]
    def make_preprocessor():
        return ColumnTransformer(
            [
                ("calendar_and_codes", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
                ("weather_measurements", "passthrough", CONTINUOUS),
            ],
            sparse_threshold=0.0,
        )
    models = {
        "dummy_mean": DummyRegressor(strategy="mean"),
        "weekday_hour_mean": None,
        "ridge_onehot": make_pipeline(make_preprocessor(), StandardScaler(), Ridge(alpha=10.0)),
        "random_forest_onehot": make_pipeline(make_preprocessor(), RandomForestRegressor(n_estimators=300, min_samples_leaf=2, max_features=0.9, n_jobs=1, random_state=20261123)),
        "hist_gradient_boosting_onehot": make_pipeline(make_preprocessor(), HistGradientBoostingRegressor(max_iter=250, learning_rate=0.06, l2_regularization=1.0, random_state=20261123)),
    }
    metric_rows = []
    prediction_rows = []
    for fold_name, train_start, train_end, test_start, test_end in folds:
        train = frame.iloc[train_start:train_end]
        test = frame.iloc[test_start:test_end]
        x_train, y_train = train[FEATURES], train[TARGET]
        x_test, y_test = test[FEATURES], test[TARGET]
        for name, base_model in models.items():
            if name == "weekday_hour_mean":
                calendar_mean = train.groupby(["weekday", "hr"])[TARGET].mean()
                pred = np.array([
                    calendar_mean.get((int(weekday), int(hour)), float(y_train.mean()))
                    for weekday, hour in zip(x_test["weekday"], x_test["hr"])
                ])
            else:
                import copy
                model = copy.deepcopy(base_model)
                model.fit(x_train, y_train)
                pred = model.predict(x_test)
            pred = np.maximum(0.0, pred)
            metric_rows.append({
                "fold": fold_name, "model": name, "train_rows": len(train), "test_rows": len(test),
                "test_first_instant": int(test["instant"].iloc[0]), "test_last_instant": int(test["instant"].iloc[-1]),
                "mae": mean_absolute_error(y_test, pred), "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
                "r2": r2_score(y_test, pred),
            })
            if name in {"dummy_mean", "weekday_hour_mean", "random_forest_onehot", "hist_gradient_boosting_onehot"}:
                prediction_rows.extend({
                    "fold": fold_name, "model": name, "instant": int(ix), "actual_cnt": float(actual), "predicted_cnt": float(estimate)
                } for ix, actual, estimate in zip(test["instant"], y_test, pred))
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(OUT / "fold_metrics.csv", index=False, float_format="%.10g")
    pd.DataFrame(prediction_rows).to_csv(OUT / "selected_holdout_predictions.csv", index=False, float_format="%.10g")
    manifest = {
        "status": "complete", "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_file": Path(__file__).name, "script_sha256": sha256(Path(__file__)),
        "protocol_file": "PROTOCOLE_BENCHMARK_PREDICTION_V3_FR.md",
        "protocol_sha256": sha256(HERE / "PROTOCOLE_BENCHMARK_PREDICTION_V3_FR.md"),
        "source_csv": "source/hour.csv", "source_csv_sha256": sha256(DATA), "rows": n,
        "target": TARGET, "features": FEATURES,
        "excluded_columns": {"instant": "record/time index", "casual": "part of target identity: casual + registered = cnt", "registered": "part of target identity: casual + registered = cnt", "dteday": "parsed only for chronological integrity"},
        "task_limit": "Retrospective same-hour estimation with measured weather; not a forecast available before the hour.",
        "folds": [{"name": f[0], "train_start_index": f[1], "train_end_index_exclusive": f[2], "test_start_index": f[3], "test_end_index_exclusive": f[4]} for f in folds],
        "categorical_fields_onehot": CATEGORICAL,
        "continuous_fields_passthrough": CONTINUOUS,
        "models": {"dummy_mean": "training mean baseline", "weekday_hour_mean": "training-only mean for each weekday x hour group; global training mean for a missing group", "ridge_onehot": "one-hot categories, median-imputed continuous, standardized transformed inputs, Ridge(alpha=10)", "random_forest_onehot": "one-hot categories and raw continuous features; 300 trees, min_samples_leaf=2, max_features=0.9, seed=20261123", "hist_gradient_boosting_onehot": "one-hot categories and raw continuous features; 250 iterations, learning_rate=0.06, L2=1, seed=20261123"},
        "metrics": metrics.to_dict(orient="records"), "python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
        "interpretation_limit": "Public historical dataset; no external operational validation; no causal conclusion.",
    }
    (OUT / "benchmark_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"source_sha256={manifest['source_csv_sha256']}")


if __name__ == "__main__":
    main()

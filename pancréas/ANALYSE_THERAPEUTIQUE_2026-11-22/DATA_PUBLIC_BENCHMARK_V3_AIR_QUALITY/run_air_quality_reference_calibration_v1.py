#!/usr/bin/env python
"""Chronological prediction benchmark for UCI Air Quality reference readings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "AirQualityUCI.csv"
OUT = HERE / "reference_calibration_v1"
PROTOCOL = HERE.parents[2] / "PROTOCOLE_CALIBRATION_REFERENCE_AIR_QUALITY_V1_FR.md"
TARGET = "CO(GT)"
FEATURES = ["PT08.S1(CO)", "PT08.S2(NMHC)", "PT08.S3(NOx)", "PT08.S4(NO2)", "PT08.S5(O3)", "T", "RH", "AH"]
SENTINEL = -200
FOLDS = [
    {"name": "fold_1", "train_end": "2004-08-31", "test_start": "2004-09-01", "test_end": "2004-10-31"},
    {"name": "fold_2", "train_end": "2004-10-31", "test_start": "2004-11-01", "test_end": "2004-12-31"},
    {"name": "fold_3", "train_end": "2004-12-31", "test_start": "2005-01-01", "test_end": "2005-04-04"},
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_frame() -> pd.DataFrame:
    frame = pd.read_csv(SOURCE, sep=";", decimal=",", encoding="latin-1")
    frame = frame.loc[:, [c for c in frame.columns if not str(c).startswith("Unnamed:") and frame[c].notna().any()]]
    frame = frame.loc[~frame.isna().all(axis=1)].copy()
    frame["timestamp"] = pd.to_datetime(
        frame["Date"].astype(str).str.strip() + " " + frame["Time"].astype(str).str.strip(),
        format="%d/%m/%Y %H.%M.%S", errors="raise",
    )
    numeric = [TARGET, *FEATURES]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="raise").replace(SENTINEL, np.nan)
    return frame


def build_plan(frame: pd.DataFrame) -> dict:
    complete = frame[[TARGET, *FEATURES]].notna().all(axis=1)
    support = []
    for fold in FOLDS:
        train_mask = frame["timestamp"] <= pd.Timestamp(fold["train_end"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        test_mask = frame["timestamp"].between(
            pd.Timestamp(fold["test_start"]),
            pd.Timestamp(fold["test_end"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1),
        )
        support.append({
            **fold,
            "train_complete_rows": int((train_mask & complete).sum()),
            "test_complete_rows": int((test_mask & complete).sum()),
            "train_source_rows": int(train_mask.sum()),
            "test_source_rows": int(test_mask.sum()),
        })
    return {
        "title": "UCI Air Quality reference reading calibration V1",
        "status": "coverage_plan_frozen_before_model_scores",
        "source_sha256": sha256(SOURCE),
        "script_sha256": sha256(Path(__file__)),
        "protocol_sha256": sha256(PROTOCOL),
        "target": TARGET,
        "target_interpretation": "co-located reference-analyzer reading; not latent ground truth",
        "features": FEATURES,
        "sentinel_policy": "-200 -> NaN; complete case per target and fixed feature set; no imputation",
        "split_policy": "expanding chronological train periods and fixed, later calendar test windows; no random shuffle",
        "fold_support": support,
        "models": [
            {"name": "train_median", "specification": "DummyRegressor(strategy=median)"},
            {"name": "ridge", "specification": "StandardScaler(train-only) + Ridge(alpha=1.0)"},
            {"name": "hist_gradient_boosting", "specification": "HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, max_leaf_nodes=15, early_stopping=False, random_state=20261124)"},
        ],
        "metrics": ["MAE", "RMSE", "R2"],
        "interpretive_limit": "Predicts reference readings on this dataset; time degradation alone does not identify instrument drift or a cause.",
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true", help="write coverage plan without fitting models")
    args = parser.parse_args()
    if not SOURCE.is_file() or not PROTOCOL.is_file():
        raise FileNotFoundError("Local UCI source or frozen protocol missing")
    frame = load_frame()
    plan = build_plan(frame)
    OUT.mkdir(parents=True, exist_ok=True)
    plan_path = OUT / "benchmark_plan_v1.json"
    if plan_path.exists():
        old = json.loads(plan_path.read_text(encoding="utf-8"))
        frozen = ("source_sha256", "protocol_sha256", "target", "features", "sentinel_policy", "split_policy", "fold_support", "models", "metrics")
        for key in frozen:
            if old.get(key) != plan.get(key):
                raise RuntimeError(f"Frozen calibration plan mismatch at {key}; refusing overwrite")
        plan["script_sha256"] = sha256(Path(__file__))
    else:
        write_json(plan_path, plan)
    if args.prepare_only:
        print(json.dumps({"status": "prepared_only", "plan": str(plan_path), "fold_support": plan["fold_support"], "source_sha256": plan["source_sha256"]}, indent=2, ensure_ascii=False))
        return

    complete = frame[[TARGET, *FEATURES]].notna().all(axis=1)
    metrics, predictions = [], []
    models = {
        "train_median": lambda: DummyRegressor(strategy="median"),
        "ridge": lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "hist_gradient_boosting": lambda: HistGradientBoostingRegressor(
            max_iter=100, learning_rate=0.1, max_leaf_nodes=15, early_stopping=False, random_state=20261124,
        ),
    }
    for fold in FOLDS:
        train_end = pd.Timestamp(fold["train_end"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        test_start = pd.Timestamp(fold["test_start"])
        test_end = pd.Timestamp(fold["test_end"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        train_mask = complete & (frame["timestamp"] <= train_end)
        test_mask = complete & frame["timestamp"].between(test_start, test_end)
        train, test = frame.loc[train_mask], frame.loc[test_mask]
        if len(train) < 100 or len(test) < 50:
            raise RuntimeError(f"Insufficient complete rows in {fold['name']}: train={len(train)}, test={len(test)}")
        x_train, y_train = train[FEATURES], train[TARGET]
        x_test, y_test = test[FEATURES], test[TARGET]
        for model_name, factory in models.items():
            model = factory().fit(x_train, y_train)
            pred = np.asarray(model.predict(x_test), dtype=float)
            metrics.append({
                "fold": fold["name"], "model": model_name,
                "train_rows": len(train), "test_rows": len(test),
                "mae": float(mean_absolute_error(y_test, pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
                "r2": float(r2_score(y_test, pred)),
                "baseline_median_mae": None,
            })
            predictions.extend({"fold": fold["name"], "model": model_name, "timestamp": ts.isoformat(), "reference_CO_GT": float(y), "predicted_reference_CO_GT": float(yhat)}
                               for ts, y, yhat in zip(test["timestamp"], y_test, pred))
    metric_df = pd.DataFrame(metrics)
    baseline_mae = metric_df.loc[metric_df["model"] == "train_median", ["fold", "mae"]].set_index("fold")["mae"]
    metric_df["baseline_median_mae"] = metric_df["fold"].map(baseline_mae)
    metric_df["mae_skill_vs_train_median"] = 1.0 - metric_df["mae"] / metric_df["baseline_median_mae"]
    metric_path = OUT / "fold_metrics.csv"
    prediction_path = OUT / "holdout_predictions.csv"
    metric_df.to_csv(metric_path, index=False, float_format="%.10g")
    pd.DataFrame(predictions).to_csv(prediction_path, index=False, float_format="%.10g")
    report_lines = [
        "# Air Quality — estimation chronologique de la lecture de référence",
        "",
        "La cible est `CO(GT)`, une lecture de l’analyseur colocalisé telle que fournie par UCI; ce n’est pas une vérité latente sans incertitude.",
        "Les valeurs `-200` sont absentes, sans imputation. Les huit caractéristiques et trois fenêtres chronologiques sont gelées dans `benchmark_plan_v1.json`.",
        "Cette estimation classique est distincte des sorties descriptives de la rotation UNIVERSAL_LOG.",
        "",
        "## Résultats par période future",
        "",
        "| Pli | Modèle | n train | n test | MAE | RMSE | R² | MAE médiane train | Skill MAE |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metric_df.itertuples(index=False):
        report_lines.append(f"| {row.fold} | {row.model} | {row.train_rows} | {row.test_rows} | {row.mae:.5f} | {row.rmse:.5f} | {row.r2:.5f} | {row.baseline_median_mae:.5f} | {row.mae_skill_vs_train_median:.5f} |")
    report_lines += [
        "",
        "## Limites d’interprétation",
        "",
        "Une baisse de performance au fil du temps ne localise pas automatiquement une dérive instrumentale. Elle peut aussi venir d’une évolution des conditions, d’une relation capteur-référence qui change, de l’échantillonnage ou d’autres limites du jeu. Les erreurs sont comparées aux flux et à la disponibilité avant toute attribution. Ces sorties ne valident pas l’universalité du pipeline.",
        "",
    ]
    report_path = OUT / "RESULTS_REFERENCE_CALIBRATION_V1_FR.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    manifest = {
        "status": "complete", "source_sha256": plan["source_sha256"],
        "script_sha256": sha256(Path(__file__)), "protocol_sha256": sha256(PROTOCOL),
        "plan_sha256": sha256(plan_path), "metrics_sha256": sha256(metric_path),
        "predictions_sha256": sha256(prediction_path), "report_sha256": sha256(report_path),
        "rows_evaluated": int(metric_df["test_rows"].sum()),
        "license_note": "Derived results retained locally until the UCI research-only/noncommercial versus CC BY 4.0 wording is clarified.",
    }
    write_json(OUT / "benchmark_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

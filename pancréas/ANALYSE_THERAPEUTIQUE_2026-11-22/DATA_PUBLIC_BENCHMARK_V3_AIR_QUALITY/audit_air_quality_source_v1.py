#!/usr/bin/env python
"""Audit UCI Air Quality structure before deciding whether full pipeline input is admissible."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
CSV = HERE / "source" / "AirQualityUCI.csv"
OUT = HERE / "source_quality_audit_v1.json"
REPORT = HERE / "RESULTS_SOURCE_QUALITY_AUDIT_V1_FR.md"
PLOT = HERE / "AIR_QUALITY_MISSINGNESS_BY_MONTH_V1.png"
SENTINEL = -200


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    raw_frame = pd.read_csv(CSV, sep=";", decimal=",", encoding="latin-1")
    raw_parsed_rows = int(len(raw_frame))
    frame = raw_frame.loc[:, [c for c in raw_frame.columns if not str(c).startswith("Unnamed:") and raw_frame[c].notna().any()]]
    blank_rows = int(frame.isna().all(axis=1).sum())
    frame = frame.loc[~frame.isna().all(axis=1)].reset_index(drop=True)
    timestamp = pd.to_datetime(
        frame["Date"].astype(str).str.strip() + " " + frame["Time"].astype(str).str.strip(),
        format="%d/%m/%Y %H.%M.%S",
        errors="coerce",
    )
    numeric_columns = [c for c in frame.columns if c not in {"Date", "Time"}]
    numeric = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    per_column = {}
    for col in numeric_columns:
        series = numeric[col]
        missing = series.isna() | series.eq(SENTINEL)
        valid = series.loc[~missing]
        unique = np.sort(valid.unique())
        diffs = np.diff(unique)
        valid_month_counts = {
            str(period): int(count)
            for period, count in timestamp.loc[valid.index].dt.to_period("M").value_counts().sort_index().items()
        }
        per_column[col] = {
            "n_source_values": int(len(series)),
            "n_sentinel_minus_200": int(series.eq(SENTINEL).sum()),
            "n_other_non_numeric_or_missing": int(series.isna().sum()),
            "n_valid_after_sentinel_mask": int((~missing).sum()),
            "n_unique_valid": int(valid.nunique()),
            "valid_min": float(valid.min()) if len(valid) else None,
            "valid_max": float(valid.max()) if len(valid) else None,
            "valid_rows_at_min": int(valid.eq(valid.min()).sum()) if len(valid) else 0,
            "valid_rows_at_max": int(valid.eq(valid.max()).sum()) if len(valid) else 0,
            "smallest_positive_step": float(diffs[diffs > 0].min()) if np.any(diffs > 0) else None,
            "first_valid_timestamp": timestamp.loc[valid.index].min().isoformat() if len(valid) else None,
            "last_valid_timestamp": timestamp.loc[valid.index].max().isoformat() if len(valid) else None,
            "valid_rows_per_calendar_month": valid_month_counts,
        }
    diffs_hours = timestamp.diff().dt.total_seconds().div(3600)
    gap_counts = {
        str(int(k)): int(v)
        for k, v in diffs_hours.dropna().value_counts().sort_index().items()
    }
    bin_edges = pd.date_range(timestamp.min().floor("h"), timestamp.max().ceil("h"), periods=101)
    time_bin = pd.cut(timestamp, bins=bin_edges, include_lowest=True, labels=False)
    per_column_empty_bins = {}
    for col in numeric_columns:
        valid_mask = numeric[col].notna() & numeric[col].ne(SENTINEL) & time_bin.notna()
        counts = pd.DataFrame({"bin": time_bin[valid_mask], "value": numeric.loc[valid_mask, col]}).groupby("bin")["value"].count()
        per_column_empty_bins[col] = int(100 - counts.reindex(range(100), fill_value=0).gt(0).sum())
    complete_rows = int((~(numeric.isna() | numeric.eq(SENTINEL)).any(axis=1)).sum())
    complete_mask = ~(numeric.isna() | numeric.eq(SENTINEL)).any(axis=1)
    complete_case_month_counts = {
        str(period): int(count)
        for period, count in timestamp.loc[complete_mask].dt.to_period("M").value_counts().sort_index().items()
    }
    month_series = timestamp.dt.to_period("M")
    month_labels = [str(x) for x in sorted(month_series.unique())]
    missing_matrix = np.zeros((len(numeric_columns), len(month_labels)), dtype=float)
    for row_index, col in enumerate(numeric_columns):
        missing_mask = numeric[col].isna() | numeric[col].eq(SENTINEL)
        rates = missing_mask.groupby(month_series).mean()
        for col_index, month in enumerate(month_labels):
            missing_matrix[row_index, col_index] = float(rates.get(pd.Period(month, freq="M"), np.nan))
    fig, ax = plt.subplots(figsize=(max(13, len(month_labels) * 0.75), 7.2), constrained_layout=True)
    image = ax.imshow(missing_matrix, vmin=0, vmax=1, aspect="auto", cmap="magma")
    ax.set_xticks(np.arange(len(month_labels)), month_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(numeric_columns)), numeric_columns)
    ax.set_title("Part manquante par flux et mois — le code source -200 est masqué")
    ax.set_xlabel("Mois de l'horodatage source")
    ax.set_ylabel("Flux source")
    fig.colorbar(image, ax=ax, label="Part des lignes manquantes (0 à 1)")
    fig.savefig(PLOT, dpi=170)
    plt.close(fig)
    report = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_csv": "source/AirQualityUCI.csv",
        "source_csv_sha256": sha256(CSV),
        "audit_script_sha256": sha256(Path(__file__).resolve()),
        "raw_parsed_table_rows_including_blank_trailing_rows": raw_parsed_rows,
        "fully_blank_rows_excluded_from_observation_count": blank_rows,
        "nonempty_dated_source_records": int(len(frame)),
        "uci_page_claimed_instance_count": 9358,
        "source_columns": [str(c) for c in frame.columns],
        "timestamp": {
            "parse_failures": int(timestamp.isna().sum()),
            "first_in_file": timestamp.iloc[0].isoformat() if pd.notna(timestamp.iloc[0]) else None,
            "last_in_file": timestamp.iloc[-1].isoformat() if pd.notna(timestamp.iloc[-1]) else None,
            "monotone_in_file": bool(timestamp.is_monotonic_increasing),
            "unique_timestamps": int(timestamp.nunique()),
            "duplicate_timestamps": int(timestamp.duplicated().sum()),
            "adjacent_gap_hours_counts": gap_counts,
            "uci_page_reported_period": "March 2004 to February 2005",
        },
        "sentinel_code": SENTINEL,
        "numeric_flow_count": len(numeric_columns),
        "numeric_flows": per_column,
        "complete_rows_across_all_numeric_flows_after_sentinel_mask": complete_rows,
        "complete_case_first_timestamp": timestamp.loc[complete_mask].min().isoformat() if complete_rows else None,
        "complete_case_last_timestamp": timestamp.loc[complete_mask].max().isoformat() if complete_rows else None,
        "complete_case_rows_per_calendar_month": complete_case_month_counts,
        "empty_time_bins_out_of_100_by_flow_after_sentinel_mask": per_column_empty_bins,
        "missingness_plot": PLOT.name,
        "preprocessing_decision": "No imputation, interpolation, filtering, or row reordering performed by this audit. A full multi-flow pipeline plan is deferred until per-flow missingness and common-support adequacy are reviewed.",
        "interpretive_boundary": "The audit establishes file structure only. Sentinel frequency or channel limits do not prove a sensor fault, causal threshold, or pipeline result.",
        "license_note": "UCI page states research-only/noncommercial use and also displays CC BY 4.0; raw file is retained locally pending clarification.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        "# Audit structure source — UCI Air Quality V1",
        "",
        f"Fichier brut : {len(frame):,} enregistrements datés et `{len(numeric_columns)}` flux numériques, SHA-256 `{sha256(CSV)}`. L'UCI annonce 9 358 instances; ce CSV contient 9 357 lignes non vides et 114 lignes finales entièrement vides après import tabulaire.",
        "",
        "## Horodatages",
        "",
        f"- Lignes entièrement vides dans le tableau importé, exclues du décompte des enregistrements : {blank_rows}.",
        f"- Échecs de lecture d'horodatage parmi les enregistrements non vides : {timestamp.isna().sum()}.",
        f"- Horodatage croissant dans l'ordre du fichier : {timestamp.is_monotonic_increasing}.",
        f"- Horodatages répétés parmi les enregistrements non vides : {timestamp.duplicated().sum()}.",
        f"- Période du fichier : {timestamp.min()} à {timestamp.max()}; la page UCI indique « March 2004 to February 2005 ».",
        f"- Lignes entièrement exploitables sur tous les flux numériques après masquage de `-200` : {complete_rows}.",
        f"- Intervalle couvert par les lignes complètes communes : {timestamp.loc[complete_mask].min()} à {timestamp.loc[complete_mask].max()}.",
        f"- `NMHC(GT)` contient {per_column['NMHC(GT)']['n_sentinel_minus_200']} sentinelles `-200`; ses valeurs valides par mois sont {per_column['NMHC(GT)']['valid_rows_per_calendar_month']}. Aucune valeur valide n'apparaît après mai 2004 dans le fichier.",
        "- Les horodatages restent consécutifs sur toute la période. L'absence tardive de `NMHC(GT)` est une absence dans ce flux, pas une heure disparue de l'ensemble du CSV.",
        "",
        "## Flux numériques et valeurs sentinelles",
        "",
        "| Flux | `-200` | Valides | Distinctes valides | Min valide | Max valide |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for col, item in per_column.items():
        md_lines.append(
            f"| `{col}` | {item['n_sentinel_minus_200']} | {item['n_valid_after_sentinel_mask']} | "
            f"{item['n_unique_valid']} | {item['valid_min']} | {item['valid_max']} |"
        )
    md_lines += [
        "",
        "## Capacité de couverture par temps",
        "",
        f"Carte de chaleur : `{PLOT.name}`. Une case plus claire représente une plus grande part de `-200` ou de valeurs manquantes; ce visuel décrit la disponibilité enregistrée, pas une cause.",
        "",
        "Nombre de 100 bins calendaires vides par flux après exclusion descriptive de `-200` (aucune valeur n'est remplacée) :",
        "",
    ]
    md_lines.extend(f"- `{key}` : {value}/100" for key, value in per_column_empty_bins.items())
    md_lines += ["", "Nombre de lignes complètes communes par mois (après masquage du sentinelle) :", ""]
    md_lines.extend(f"- {key} : {value}" for key, value in complete_case_month_counts.items())
    md_lines += [
        "",
        "Aucun remplissage ni filtrage n'a été appliqué. Si des flux ont des périodes de validité différentes, une comparaison multivariée sur des points de support différents pourrait confondre l'effet de l'axe avec celui des données disponibles. Cette décision exige un protocole explicite avant l'appel pipeline.",
        "",
        "## Limite et suite",
        "",
        "Le code `-200` est traité comme donnée manquante conformément à la documentation UCI. Les bornes et fréquences observées restent des constats; elles ne prouvent pas une panne ni une saturation instrumentale. Le plan de rotation complète est reporté jusqu'à ce qu'une représentation commune des flux puisse être justifiée sans imputation arbitraire.",
        "",
    ]
    REPORT.write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "raw_parsed_rows_including_empty": raw_parsed_rows,
        "blank_rows_excluded": blank_rows,
        "nonempty_records": report["nonempty_dated_source_records"],
        "numeric_flows": len(numeric_columns),
        "all_numeric_complete_rows": complete_rows,
        "complete_case_first_timestamp": report["complete_case_first_timestamp"],
        "complete_case_last_timestamp": report["complete_case_last_timestamp"],
        "timestamp_monotone": report["timestamp"]["monotone_in_file"],
        "duplicate_timestamps": report["timestamp"]["duplicate_timestamps"],
        "empty_time_bins": per_column_empty_bins,
        "sha256": report["source_csv_sha256"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

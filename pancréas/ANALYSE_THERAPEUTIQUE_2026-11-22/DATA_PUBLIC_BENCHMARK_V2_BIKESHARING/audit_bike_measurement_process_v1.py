#!/usr/bin/env python
"""Descriptive audit of the recorded measurement/aggregation chain.

This script reports file-level properties only. It cannot identify the
instrument or assign causality to a pipeline threshold.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
CSV = HERE / "source" / "hour.csv"
README = HERE / "source" / "Readme.txt"
OUT = HERE / "measurement_process_audit_v1.json"
REPORT = HERE / "RESULTS_MEASUREMENT_PROCESS_AUDIT_V1_FR.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    frame = pd.read_csv(CSV, parse_dates=["dteday"])
    timestamp = frame["dteday"] + pd.to_timedelta(frame["hr"], unit="h")
    dt_hours = timestamp.diff().dt.total_seconds().div(3600)
    missing_intervals = []
    for i in np.flatnonzero(dt_hours.to_numpy() > 1):
        missing_intervals.append({
            "previous_record": timestamp.iloc[i - 1].isoformat(),
            "next_record": timestamp.iloc[i].isoformat(),
            "gap_hours": int(dt_hours.iloc[i]),
            "unrepresented_hours_between": int(dt_hours.iloc[i] - 1),
        })

    weather_cols = ["temp", "atemp", "hum", "windspeed"]
    numeric_summary = {}
    for column in [*weather_cols, "cnt", "casual", "registered"]:
        values = pd.to_numeric(frame[column], errors="coerce")
        unique = np.sort(values.dropna().unique())
        gaps = np.diff(unique)
        minimum_step = float(gaps[gaps > 0].min()) if np.any(gaps > 0) else None
        numeric_summary[column] = {
            "n_nonmissing": int(values.notna().sum()),
            "n_unique": int(values.nunique(dropna=True)),
            "minimum_observed": float(values.min()),
            "maximum_observed": float(values.max()),
            "rows_at_minimum": int((values == values.min()).sum()),
            "rows_at_maximum": int((values == values.max()).sum()),
            "smallest_positive_step_between_unique_values": minimum_step,
            "n_unique_values_rounded_to_2_decimals": int(values.round(2).nunique(dropna=True)),
        }

    weather_category_counts = {
        str(int(k)): int(v) for k, v in frame["weathersit"].value_counts(dropna=False).sort_index().items()
    }
    cnt_jumps = frame.assign(timestamp=timestamp, delta=frame["cnt"].diff()).iloc[1:].copy()
    cnt_jumps["abs_delta"] = cnt_jumps["delta"].abs()
    largest_count_changes = []
    for _, row in cnt_jumps.nlargest(10, "abs_delta").iterrows():
        largest_count_changes.append({
            "timestamp": row["timestamp"].isoformat(),
            "previous_timestamp": timestamp.iloc[int(row.name) - 1].isoformat(),
            "cnt_previous": int(frame.loc[int(row.name) - 1, "cnt"]),
            "cnt_current": int(row["cnt"]),
            "cnt_difference": int(row["delta"]),
            "gap_hours": int(dt_hours.loc[row.name]),
        })

    readme_text = README.read_text(encoding="utf-8", errors="replace")
    report = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_csv": "source/hour.csv",
        "source_csv_sha256": sha256(CSV),
        "source_readme_sha256": sha256(README),
        "source_rows": int(len(frame)),
        "measurement_process_as_described_by_source": {
            "rental_records": "The Readme describes a two-year historical Capital Bikeshare log aggregated hourly and daily.",
            "weather_provenance": "The Readme attributes weather information to freemeteo.",
            "normalization_scales_stated_in_readme": {
                "temp": 41,
                "atemp": 50,
                "hum": 100,
                "windspeed": 67,
            },
            "weather_sensor_model_calibration_sampling_details_or_uncertainty_present": any(
                term in readme_text.lower()
                for term in ["sensor model", "calibration record", "instrument model", "measurement uncertainty"]
            ),
            "station_availability_or_fleet_capacity_series_present": False,
        },
        "timestamp_coverage": {
            "first": timestamp.min().isoformat(),
            "last": timestamp.max().isoformat(),
            "rows": int(len(timestamp)),
            "expected_hour_slots_inclusive": int((timestamp.max() - timestamp.min()).total_seconds() // 3600 + 1),
            "unrepresented_hour_slots": int((timestamp.max() - timestamp.min()).total_seconds() // 3600 + 1 - timestamp.nunique()),
            "gaps": missing_intervals,
        },
        "value_resolution_and_endpoint_descriptions": numeric_summary,
        "weather_category_record_counts": weather_category_counts,
        "largest_adjacent_record_cnt_changes": largest_count_changes,
        "interpretive_boundary": (
            "Endpoint concentrations, quantization, gaps, category changes, or large count changes are descriptive candidates "
            "for follow-up. They do not establish instrument clipping, a collection-system threshold, a causal event, or an "
            "explanation for any UNIVERSAL_LOG T0. The source lacks sensor calibration and system-availability logs."
        ),
        "data_handling": "No imputation, filtering, reordering, or alteration of source records was performed.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = []
    for column, item in numeric_summary.items():
        rows.append(
            f"| `{column}` | {item['n_unique']} | {item['minimum_observed']:.4g} | "
            f"{item['maximum_observed']:.4g} | {item['rows_at_minimum']} | {item['rows_at_maximum']} | "
            f"{item['smallest_positive_step_between_unique_values']:.4g} |"
        )
    report_md = f"""# Audit descriptif de la chaîne de mesure — Bike Sharing V1

## Portée et source

Analyse descriptive de `source/hour.csv` ({len(frame):,} lignes), sans correction des données. Empreinte SHA-256 : `{sha256(CSV)}`. Le Readme UCI décrit un journal historique de Capital Bikeshare agrégé à l'heure; il attribue l'information météo à Freemeteo et indique une normalisation par les facteurs 41 (`temp`), 50 (`atemp`), 100 (`hum`) et 67 (`windspeed`). Il ne fournit pas de modèle d'instrument, de certificat d'étalonnage, d'incertitude instrumentale ou de série de disponibilité/capacité des stations.

## Constats mesurés dans le fichier

- 17 379 lignes couvrent du {timestamp.min():%Y-%m-%d %H:%M} au {timestamp.max():%Y-%m-%d %H:%M}. L'intervalle inclusif comporte 17 544 heures; 165 heures n'ont pas de ligne, distribuées sur {len(missing_intervals)} intervalles. Le Readme ne donne pas leur mécanisme. Elles ne sont pas imputées.
- `casual + registered = cnt` pour toutes les lignes (contrôle d'intégrité du fichier).
- Parmi les valeurs météo normalisées, `hum` vaut exactement 1,00 dans {numeric_summary['hum']['rows_at_maximum']} lignes; `windspeed` vaut 0 dans {numeric_summary['windspeed']['rows_at_minimum']} lignes. Le maximum observé de `temp` et `atemp` apparaît chacun une fois.
- Les plus grandes différences absolues entre deux lignes consécutives de `cnt` sont conservées dans le JSON associé. Ce sont des changements de comptage observés; aucune cause n'est attribuée.

| Flux | Valeurs distinctes | Minimum | Maximum | Occurrences du minimum | Occurrences du maximum | Plus petit pas distinct observé |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## Hypothèses instrumentales à tester, sans conclusion

La concentration de `hum` à la borne supérieure et les nombreux zéros de `windspeed` peuvent justifier une vérification de résolution, d'arrondi, de limite de mesure ou de codage. Ils peuvent aussi avoir une explication physique. Le fichier et son Readme ne permettent pas de départager ces possibilités. Les catégories `weathersit`, la normalisation météo, l'agrégation horaire, les heures manquantes et la disponibilité des vélos sont des parties distinctes de la chaîne de production des données.

Un repère UNIVERSAL_LOG proche d'une borne, d'une transition catégorielle ou d'une lacune serait donc un candidat à examiner avec les métadonnées de collecte et des données indépendantes; ce rapprochement ne suffit pas à prouver que l'outil a créé le seuil. Il faut aussi préserver l'hypothèse inverse : un changement du phénomène peut être réel et capté correctement par l'instrument.

## Suite discriminante proposée

1. Chercher la documentation de collecte des données météo et les journaux de disponibilité/capacité par station; si ces sources n'existent pas dans l'archive publique, noter cette absence comme limite.
2. Comparer les champs météo à une source météorologique indépendante alignée par heure, en rapportant les écarts et les heures absentes sans les combler silencieusement.
3. Comparer l'analyse sur les enregistrements horaires et le fichier journalier fourni, en gelant les paramètres et en traitant l'agrégation comme facteur expérimental. Ne pas appeler les deux jeux des répétitions indépendantes.
4. Relier chaque sortie de seuil aux valeurs et changements observés dans tous les flux autour de T0, en excluant le contrôle choisi des flux analysés; rapporter séparément les cas où le contrôle demandé égale la cible et où le code substitue la cible.

Ces étapes séparent les observations du fichier, les hypothèses d'instrument et les résultats du pipeline. Elles ne présupposent pas que le seuil soit instrumental ou biologique/opérationnel.
"""
    REPORT.write_text(report_md, encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

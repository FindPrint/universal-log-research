"""Re-aggregate archived Ising estimator landscapes with v5.8 d_kind labels.

This script does not recompute the estimator trajectories or run the physical
simulators. It applies the v5.8 TLog aggregation and semantic metadata to the
archived df_feat.csv landscapes, preserving the original observation count and
control label for each case.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent
OUT = PROJECT / "tlog_d_kind_v58_results"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5.8.py"

spec = importlib.util.spec_from_file_location("universal_log_v58_reaggregation", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


def _read_d_vector(path: Path | None):
    if path is None or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("D_vector") or data.get("pipeline_D_vector")
    except Exception:
        return None


def _case(case_id, relative_path, n_samples, control, previous_path=None, previous_vector=None):
    source = PROJECT / relative_path
    landscape = pd.read_csv(source)
    state = ul.compute_holographic_tension_state(
        landscape,
        scores={},
        n_samples=n_samples,
        control_col=control,
    )
    previous = (
        previous_vector
        if previous_vector is not None
        else _read_d_vector(PROJECT / previous_path if previous_path else None)
    )
    new_vector = state.get("D_vector") or {}
    comparison = {}
    if previous is not None:
        for key, value in previous.items():
            new_value = new_vector.get(key)
            comparison[key] = {
                "previous": value,
                "v58_reaggregated": new_value,
                "difference": (
                    float(new_value) - float(value)
                    if value is not None and new_value is not None else None
                ),
            }

    record = {
        "case_id": case_id,
        "source_landscape": str(source.relative_to(PROJECT)),
        "source_landscape_note": "Paysage d'estimateurs archivé avant l'ajout de d_kind; seules les médianes TLog sont recalculées ici.",
        "pipeline_version_for_reaggregation": ul.VERSION_MASTER,
        "n_samples_for_tlog": n_samples,
        "control_col": control,
        "n_landscape_rows": len(landscape),
        "D_vector_v58": new_vector,
        "previous_D_vector_comparison": comparison or None,
        "legacy_class_semantics": {
            cls: {
                "d_kinds_present": axis.get("d_kinds_present", []),
                "semantic_type_homogeneous": axis.get("semantic_type_homogeneous"),
                "semantic_warning": axis.get("semantic_warning"),
            }
            for cls, axis in (state.get("geometric_layer", {}).get("axes") or {}).items()
        },
        "T_log_by_d_kind": state.get("geometric_layer", {}).get("T_log_by_d_kind", {}),
    }
    return record


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    chain_summary_path = (
        PROJECT / "ising_classique_test/finite_size/"
        "tlog_chain_comparison_controlled/tlog_chain_comparison_controlled.json"
    )
    chain_summary = json.loads(chain_summary_path.read_text(encoding="utf-8"))
    chain_vectors = {
        index: {
            f"d_{name}": values["per_chain_d"][index]
            for name, values in chain_summary["between_chain_anchor_summary"].items()
        }
        for index in range(3)
    }
    cases = [
        _case(
            "classical_temperature_sweep",
            Path("ising_classique_test/results_temperature/df_feat.csv"),
            105, "Temperature",
            Path("ising_classique_test/results_temperature/reading_synthesis.json"),
        ),
        _case(
            "classical_field_sweep",
            Path("ising_classique_test/results_field/df_feat.csv"),
            105, "Field",
            Path("ising_classique_test/results_field/reading_synthesis.json"),
        ),
        _case(
            "classical_tlog_profile_sweep",
            Path("ising_classique_test/results_tlog_profiles/df_feat.csv"),
            105, "Temperature",
            Path("ising_classique_test/results_tlog_profiles/reading_synthesis.json"),
        ),
    ]
    for index in range(3):
        cases.append(_case(
            f"classical_controlled_chain_{index}",
            Path(f"ising_classique_test/finite_size/tlog_chain_comparison_controlled/chain_{index}_df_feat.csv"),
            76, "Temperature",
            previous_vector=chain_vectors[index],
        ))
    for size in (8, 10, 12):
        cases.append(_case(
            f"quantum_transverse_ising_N{size}",
            Path(f"ising_quantique_test/results/N{size}/df_feat.csv"),
            81, "g",
            Path(f"ising_quantique_test/results/N{size}/tlog_result.json"),
        ))

    compared = [case for case in cases if case["previous_D_vector_comparison"]]
    comparison_differences = [
        abs(item["difference"])
        for case in compared
        for item in case["previous_D_vector_comparison"].values()
        if item["difference"] is not None
    ]
    comparison_summary = {
        "cases_compared": len(compared),
        "max_absolute_difference": max(comparison_differences) if comparison_differences else None,
        "exact_match": bool(comparison_differences and max(comparison_differences) == 0.0),
    }
    payload = {
        "purpose": "Apply v5.8 typed TLog aggregation to stored Ising estimator landscapes.",
        "interpretation_limit": "This is a re-aggregation of archived estimator outputs; it is not a fresh simulator run or a recalculation of all 29 estimator trajectories.",
        "pipeline_version": ul.VERSION_MASTER,
        "measurement_taxonomy_schema_version": "1.0",
        "legacy_D_vector_comparison": comparison_summary,
        "cases": cases,
    }
    (OUT / "ising_tlog_d_kind_v58.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rows = []
    for case in cases:
        for kind, profile in case["T_log_by_d_kind"].items():
            rows.append({
                "case_id": case["case_id"],
                "control_col": case["control_col"],
                "n_samples_for_tlog": case["n_samples_for_tlog"],
                "d_kind": kind,
                "label_fr": profile["label_fr"],
                "d_median": profile["d_median"],
                "T_log": profile["T_log"],
                "estimators_used": ", ".join(profile["estimators_used"]),
                "between_estimator_iqr": profile["between_estimator_iqr"],
                "status": profile["status"],
            })
    pd.DataFrame(rows).to_csv(OUT / "ising_tlog_d_kind_v58.csv", index=False)

    lines = [
        "# Relecture TLog typée des paysages Ising archivés (v5.8)",
        "",
        "Cette sortie regroupe les médianes déjà présentes dans les anciens fichiers df_feat.csv selon le nouveau d_kind. Les estimateurs ne sont pas recalculés. T_log_by_d_kind conserve (d−4) ln(n) et signale chaque regroupement comme exploratoire, à calibrer par domaine.",
        "",
        f"Comparaison aux vecteurs de classe archivés : {comparison_summary['cases_compared']} cas, écart absolu maximal {comparison_summary['max_absolute_difference']}, correspondance exacte = {comparison_summary['exact_match']}.",
        "",
        "## Vecteurs de classe historiques et comparaisons",
        "",
        "| Cas | Contrôle | n | d_sat | d_crit | d_div | d_null |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for case in cases:
        vector = case["D_vector_v58"]
        lines.append(
            f"| {case['case_id']} | {case['control_col']} | {case['n_samples_for_tlog']} | "
            f"{vector.get('d_sat')} | {vector.get('d_crit')} | {vector.get('d_div')} | {vector.get('d_null')} |"
        )
    lines.extend([
        "",
        "## Profils par type",
        "",
        "Voir le [CSV détaillé](ising_tlog_d_kind_v58.csv) et le [JSON complet](ising_tlog_d_kind_v58.json) pour les valeurs, les estimateurs utilisés, l'IQR (lorsqu'il est estimable) et les avertissements de classes hétérogènes.",
        "",
        "Les paysages sources sont des exports antérieurs; cette relecture ne recalcule pas les trajectoires des estimateurs.",
        "",
    ])
    (OUT / "RAPPORT_RELECTURE_ISING_V58.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote typed Ising re-aggregation to {OUT}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "candidate_Tiriac2018"
RUN_ROOT = HERE / "Tiriac2018_Gemcitabine_all_controls_PDACDomain"
RUN_MANIFEST = RUN_ROOT / "RUN_MATRIX_MANIFEST.json"
INPUT_MANIFEST = DATA_DIR / "PIPELINE_INPUT_MANIFEST.json"
OUT_JSON = RUN_ROOT / "PIPELINE_OUTPUT_SUMMARY.json"
OUT_CSV = RUN_ROOT / "PIPELINE_OUTPUT_SUMMARY.csv"
OUT_MD = RUN_ROOT / "PIPELINE_OUTPUT_SUMMARY.md"
OUT_PNG = RUN_ROOT / "GEMCITABINE_T0_BY_CONTROL.png"


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_.") or "column"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    run = load_json(RUN_MANIFEST)
    input_data = load_json(INPUT_MANIFEST)
    profiles = [*input_data["chemo_fluxes"], *input_data["targeted_fluxes"]]
    controls = [name for name in profiles if name != run["target"]]
    results = []
    for control in controls:
        item = {"target": run["target"], "control": control, "status": "missing"}
        path = RUN_ROOT / "by_control" / safe_name(control)
        status_file = path / "run_status.json"
        master_file = path / "pipeline_output" / "master_results.json"
        if status_file.exists():
            item.update(load_json(status_file))
        if master_file.exists():
            result = load_json(master_file)
            meta = result.get("metadata", {}) or {}
            cascade = result.get("five_threshold_cascade", {}) or {}
            units = (cascade.get("thresholds_in_control_units", {}) or {}).get("T_0_Monte_Carlo_Central", {}) or {}
            monotone = meta.get("control_monotonicity", {}) or {}
            item.update({
                "target_used": meta.get("target_used"),
                "control_used": meta.get("control"),
                "domain_used": meta.get("domain"),
                "n_samples": meta.get("n_samples"),
                "n_numeric_fluxes": len(meta.get("global_flux_stats", {}) or {}),
                "t0_pct": cascade.get("T_0_Monte_Carlo_Central"),
                "t0_ambiguous": units.get("ambiguous"),
                "control_monotone": monotone.get("monotone"),
                "control_monotonicity_direction": monotone.get("direction"),
                "control_spearman_order_r": monotone.get("spearman_order_vs_value_r"),
                "pipeline_harmonic_validation_enabled": meta.get("harmonic_validation_enabled"),
                "master_results_path": str(master_file),
            })
        results.append(item)

    columns = [
        "target", "control", "status", "exit_code", "elapsed_seconds", "domain_used",
        "target_used", "control_used", "n_samples", "n_numeric_fluxes", "t0_pct",
        "t0_ambiguous", "control_monotone", "control_monotonicity_direction",
        "control_spearman_order_r", "console_log_sha256", "console_log", "master_results_path",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    summary = {
        "target": run["target"],
        "domain_requested": run["domain"],
        "input_observations": run["input_observations"],
        "requested_controls": len(controls),
        "completed_exit_zero": sum(item.get("status") == "ok" and item.get("exit_code") == 0 for item in results),
        "errors_or_missing": sum(not (item.get("status") == "ok" and item.get("exit_code") == 0) for item in results),
        "t0_ambiguous_count": sum(item.get("t0_ambiguous") is True for item in results),
        "t0_nonambiguous_count": sum(item.get("t0_ambiguous") is False for item in results),
        "pipeline_sha256": run["pipeline_sha256"],
        "input_sha256": run["input_sha256"],
        "results": results,
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# UNIVERSAL_LOG — Tiriac 2018 PDAC PDO run summary",
        "",
        f"- Requested target: `{run['target']}`",
        f"- Domain: `{run['domain']}`",
        f"- Input observations: {run['input_observations']} PDOs",
        f"- Controls requested: {len(controls)}; completed successfully: {summary['completed_exit_zero']}; errors/missing: {summary['errors_or_missing']}",
        f"- Pipeline SHA-256: `{run['pipeline_sha256']}`",
        f"- Input CSV SHA-256: `{run['input_sha256']}`",
        "",
        "## Pipeline outputs (source order; no ranking)",
        "",
        "| Control column | Status | Domain | N | T0 (%) | T0 ambiguous | Control monotone |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for item in results:
        t0 = item.get("t0_pct")
        t0_text = f"{float(t0):.6g}" if isinstance(t0, (int, float)) else "—"
        lines.append(
            f"| {item['control']} | {item.get('status','missing')} | {item.get('domain_used','—')} | "
            f"{item.get('n_samples','—')} | {t0_text} | {item.get('t0_ambiguous','—')} | "
            f"{item.get('control_monotone','—')} |"
        )
    lines.extend([
        "",
        "## Reading limit",
        "",
        "This is a cross-sectional PDO response-profile dataset. The pipeline uses each selected AUC control as its configured axis; it does not create calendar time or a disease progression trajectory. `T0` and ambiguity flags below are raw pipeline outputs. This table contains no drug ranking, patient recommendation, or claim of efficacy.",
        "",
        "## Files",
        "",
        f"- Numeric summary: `{OUT_CSV.name}`",
        f"- Full machine-readable summary: `{OUT_JSON.name}`",
        f"- Figure: `{OUT_PNG.name}`",
        "- Per-control console logs and all pipeline JSON/CSV/TXT exports are retained under `by_control/`.",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        import matplotlib.pyplot as plt

        present = [item for item in results if isinstance(item.get("t0_pct"), (int, float))]
        if present:
            labels = [item["control"] for item in present]
            values = [float(item["t0_pct"]) for item in present]
            colors = ["#d88922" if item.get("t0_ambiguous") else "#3274a1" for item in present]
            height = max(7, len(present) * 0.31)
            fig, ax = plt.subplots(figsize=(12, height))
            y = list(range(len(present)))
            ax.barh(y, values, color=colors, alpha=0.9)
            ax.set_yticks(y, labels)
            ax.invert_yaxis()
            ax.set_xlim(0, 100)
            ax.set_xlabel("Pipeline T0 (% of configured control axis)")
            ax.set_title("UNIVERSAL_LOG v5.9.4 — raw T0 output by control column")
            ax.grid(axis="x", alpha=0.25)
            fig.text(0.01, 0.01, "Amber = pipeline marked T0 ambiguous. Cross-sectional PDO data; not a treatment ranking.", fontsize=9)
            fig.tight_layout(rect=(0, 0.03, 1, 1))
            fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
            plt.close(fig)
        else:
            print("No T0 values yet; figure not generated.")
    except Exception as exc:
        print(f"Figure generation skipped with error: {exc!r}")

    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    print(f"SUMMARY: {OUT_MD}")


if __name__ == "__main__":
    main()

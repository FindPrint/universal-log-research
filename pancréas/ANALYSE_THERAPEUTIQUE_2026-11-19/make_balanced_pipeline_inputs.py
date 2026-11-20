from __future__ import annotations

import csv
import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "pipeline_inputs"
OUTPUT = ROOT / "pipeline_inputs_balanced_50"
OUTPUT.mkdir(exist_ok=True)
SEED = 20261119
N_PER_GROUP = 50


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def sample_csv(model: str, output_dir: Path, n_per_group: int) -> dict:
    src = SOURCE / f"GSE271300_{model}_singlet_cells_multiflux.csv"
    with src.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    groups: dict[str, list[dict]] = defaultdict(list)
    key_name = "Animal_ID" if model in ("PC69", "PC106") else "Treatment"
    for row in rows:
        groups[row[key_name]].append(row)

    rng = np.random.default_rng(SEED)
    group_n = max(n_per_group, 45) if model == "GA60" else n_per_group
    selected = []
    counts = {}
    for group_name in sorted(groups):
        group = groups[group_name]
        n_take = min(group_n, len(group))
        indices = rng.choice(len(group), size=n_take, replace=False)
        chosen = [group[int(i)] for i in indices]
        selected.extend(chosen)
        counts[group_name] = {"available_cells": len(group), "selected_cells": len(chosen)}
    rng.shuffle(selected)

    out = output_dir / f"GSE271300_{model}_balanced{n_per_group}_multiflux.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)
    return {
        "model": model,
        "source_csv": str(src),
        "source_sha256": sha256(src),
        "balanced_csv": str(out),
        "balanced_sha256": sha256(out),
        "rows_selected": len(selected),
        "grouping_key": key_name,
        "groups": counts,
        "selection": f"Up to {group_n} rows without replacement per group; seeded numpy Generator; groups sorted by name; selected rows shuffled.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows-per-group", type=int, default=N_PER_GROUP)
    args = parser.parse_args()
    output_dir = ROOT / f"pipeline_inputs_balanced_{args.rows_per_group}"
    output_dir.mkdir(exist_ok=True)
    records = [sample_csv(model, output_dir, args.rows_per_group) for model in ("PC69", "PC106", "GA60")]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "rows_per_group_target": args.rows_per_group,
        "purpose": "Runtime-feasible pipeline execution across every numeric control; not a biological independent-replicate analysis.",
        "records": records,
        "run_history": [
            {
                "model": "PC69", "rows_per_mouse": 50, "target": "CellState_basal", "control_mode": "all",
                "elapsed_seconds_approx": 131, "status": "interrupted after MC threshold optimization, before a final pipeline export",
                "partial_console_output": "MC optimization terminated; best score 0.356; rule uniform; n_candidates 155; resolution 0.649%; chosen w_size 46; min_grp 6",
                "console_log": str(ROOT / "pipeline_runs_balanced50" / "PC69_target_basal" / "console.log"),
            },
            {
                "model": "PC69", "rows_per_mouse": None, "target": "CellState_basal", "control_mode": "all",
                "input_rows": 5083, "elapsed_seconds_approx": 894,
                "status": "interrupted before any final export; no biological result retained",
                "observed_warning": "RuntimeWarning invalid value encountered in sqrt at UNIVERSAL_LOG_v5.9.4.py:1726",
                "console_log": str(ROOT / "pipeline_runs" / "PC69_target_basal" / "console.log"),
            },
        ],
    }
    out = output_dir / f"BALANCED{args.rows_per_group}_PIPELINE_INPUT_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"manifest": str(out), "models": [{"model": r["model"], "rows": r["rows_selected"], "groups": r["groups"]} for r in records]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

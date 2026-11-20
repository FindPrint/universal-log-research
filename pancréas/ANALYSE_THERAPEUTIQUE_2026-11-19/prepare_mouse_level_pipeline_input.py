from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ANALYSIS = Path(__file__).resolve().parent
SOURCE = ANALYSIS / "results_mouse_level" / "GSE271300_mouse_level_summaries.csv"
OUT_DIR = ANALYSIS / "mouse_level_pipeline_trial"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUT_DIR / "GSE271300_PC69_PC106_mouse_level_multiflux.csv"
MANIFEST = OUT_DIR / "MOUSE_LEVEL_INPUT_MANIFEST.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    source = pd.read_csv(SOURCE)
    required = {
        "model", "animal", "treatment", "basal_fraction",
        "mean_scBasalScore", "mean_scClassicalScore", "mean_S_score", "mean_G2M_score",
    }
    missing = sorted(required - set(source.columns))
    if missing:
        raise ValueError(f"Missing source columns: {missing}")
    if source["animal"].duplicated().any():
        raise ValueError("Animal IDs must be unique; refusing pseudoreplication.")

    data = source.loc[source["model"].isin(["PC69", "PC106"])].copy()
    if len(data) != 13 or data["animal"].nunique() != 13:
        raise ValueError(f"Expected 13 unique PC69/PC106 mice, found {len(data)} rows.")
    if data[list(required - {"model", "animal", "treatment"})].isna().any().any():
        raise ValueError("Missing values in target/common numeric fluxes; no imputation is allowed here.")
    if not set(data["treatment"]) <= {"veh", "mrtx"}:
        raise ValueError(f"Unexpected treatment values: {sorted(set(data['treatment']))}")

    # Explicit indicator encodings; source row order is preserved without sorting or shuffling.
    data["Treatment_code"] = data["treatment"].map({"veh": 0, "mrtx": 1}).astype("int64")
    data["PDX_model_code"] = data["model"].map({"PC69": 0, "PC106": 1}).astype("int64")
    columns = [
        "basal_fraction", "Treatment_code", "PDX_model_code", "mean_scBasalScore",
        "mean_scClassicalScore", "mean_S_score", "mean_G2M_score",
    ]
    output = data[columns].copy()
    output.to_csv(OUTPUT, index=False, float_format="%.12g")

    manifest = {
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "output": str(OUTPUT),
        "output_sha256": sha256(OUTPUT),
        "rows": int(len(output)),
        "unique_animals": int(data["animal"].nunique()),
        "source_rows_preserved_in_order": True,
        "target": "basal_fraction",
        "numeric_controls": columns[1:],
        "categorical_code_mappings": {
            "Treatment_code": {"veh": 0, "mrtx": 1},
            "PDX_model_code": {"PC69": 0, "PC106": 1},
        },
        "excluded_fields": ["animal", "model", "treatment", "n_cells_assigned", "n_cells_in_analysis", "basal_cells", "state_labeled_cells"],
        "construction": "One source row per mouse; common complete mouse-level target/fluxes only; no aggregation, imputation, sorting, or shuffling in this step.",
        "critical_axis_note": "This is cross-sectional. Row order is not time or disease progression; pipeline T0/axis outputs must not be read as temporal or therapeutic thresholds.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(output), "columns": columns, "input_sha256": manifest["output_sha256"], "manifest": str(MANIFEST)}, indent=2))


if __name__ == "__main__":
    main()

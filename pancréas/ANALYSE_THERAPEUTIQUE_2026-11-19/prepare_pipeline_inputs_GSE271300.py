from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import h5py
import numpy as np
from scipy.sparse import csr_matrix


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_GSE271300"
OUT = ROOT / "pipeline_inputs"
OUT.mkdir(exist_ok=True)
ANALYSIS_SCRIPT = ROOT / "analyze_GSE271300_mouse_level.py"
PANEL = ("KRAS", "EGFR", "ERBB2", "ERBB3", "STAT3", "GATA6", "KRT19", "CEACAM5", "TP63")


def load_audit_module():
    spec = importlib.util.spec_from_file_location("gse271300_audit", ANALYSIS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import the mouse-level audit helpers.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_expression(audit, model: str, records: list[dict]) -> dict[str, list[float]]:
    path = DATA / f"GSE271300_PDX_{model}_QC.h5ad"
    with h5py.File(path, "r") as h5:
        obs = h5["obs"]
        ids = audit.read_obs_column(obs, "_index")
        lookup = {value: i for i, value in enumerate(ids)}
        vars_ = [audit.decode(value) for value in np.asarray(h5["var"]["_index"])]
        var_lookup = {name: i for i, name in enumerate(vars_)}
        genes = [gene for gene in PANEL if gene in var_lookup]
        x = h5["X"]
        shape = tuple(int(v) for v in np.asarray(x.attrs["shape"]).ravel())
        matrix = csr_matrix((np.asarray(x["data"], dtype=np.float32),
                             np.asarray(x["indices"], dtype=np.int32),
                             np.asarray(x["indptr"], dtype=np.int64)), shape=shape)
        row_indices = np.asarray([lookup[row["cell_id"]] for row in records], dtype=int)
        expr = matrix[row_indices, :][:, [var_lookup[g] for g in genes]].toarray()
        return {gene: expr[:, j].astype(float).tolist() for j, gene in enumerate(genes)}


def numeric_fields(records: list[dict], expression: dict[str, list[float]]) -> list[str]:
    fields = [
        "Treatment_code", "CellState_basal", "CellState_classical",
        "scBasalScore", "scClassicalScore", "EMTScore",
        "S_score", "G2M_score", "G1Score", "G2MScore",
        *expression.keys(),
    ]
    return [name for name in fields if (
        name in expression or
        name in {"Treatment_code", "CellState_basal", "CellState_classical"} or
        any(row.get(name) is not None for row in records)
    )]


def write_pipeline_csv(model: str, records: list[dict], expression: dict[str, list[float]]) -> Path:
    fields = numeric_fields(records, expression)
    path = OUT / f"GSE271300_{model}_singlet_cells_multiflux.csv"
    columns = ["Cell_ID", "Animal_ID", "Treatment", *fields]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for i, row in enumerate(records):
            result = {
                "Cell_ID": row["cell_id"],
                "Animal_ID": row.get("animal", "POOLED_NO_ANIMAL"),
                "Treatment": row["treatment"],
                "Treatment_code": 1 if row["treatment"] == "mrtx" else 0,
                "CellState_basal": 1 if row.get("cellState") == "basal" else 0,
                "CellState_classical": 1 if row.get("cellState") == "classical" else 0,
            }
            for name in fields:
                if name in expression:
                    result[name] = expression[name][i]
                elif name not in result:
                    result[name] = row.get(name)
            writer.writerow(result)
    return path


def main() -> None:
    audit = load_audit_module()
    reports = []
    for model in ("PC69", "PC106"):
        animals, diag = audit.load_model(model)
        records = [row for cells in animals.values() for row in cells]
        expression = add_expression(audit, model, records)
        path = write_pipeline_csv(model, records, expression)
        reports.append({
            "model": model,
            "input_csv": str(path),
            "rows_cells": len(records),
            "animal_replicates": len(animals),
            "numeric_controls_and_fluxes": numeric_fields(records, expression),
            "mouse_assignment_diagnostics": diag,
        })

    # GA60 is included as a pooled, treatment-labelled exploration because its
    # inspected analyzed H5AD has no individual mouse labels.
    model = "GA60"
    analyzed_path = DATA / f"GSE271300_PDX_{model}_analyzed.h5ad"
    with h5py.File(analyzed_path, "r") as h5:
        obs = h5["obs"]
        ids = audit.read_obs_column(obs, "_index")
        treatment = audit.read_obs_column(obs, "treatment")
        state = audit.read_obs_column(obs, "cellState")
        score_fields = {
            name: audit.read_numeric_column(obs, name)
            for name in ("scBasalScore", "scClassicalScore", "S_score", "G2M_score", "EMTScore")
            if name in obs
        }
        records = []
        for i, cell_id in enumerate(ids):
            if state[i] not in ("basal", "classical"):
                continue
            record = {
                "cell_id": str(cell_id), "animal": "POOLED_NO_ANIMAL",
                "treatment": str(treatment[i]),
                "cellState": str(state[i]),
            }
            for name, values in score_fields.items():
                value = values[i]
                record[name] = float(value) if np.isfinite(value) else None
            records.append(record)
    expression = add_expression(audit, model, records)
    path = write_pipeline_csv(model, records, expression)
    reports.append({
        "model": model,
        "input_csv": str(path),
        "rows_cells": len(records),
        "animal_replicates": None,
        "numeric_controls_and_fluxes": numeric_fields(records, expression),
        "warning": "Pooled treatment comparison; no animal IDs available in inspected analyzed H5AD.",
    })

    report_path = OUT / "GSE271300_PIPELINE_INPUTS.json"
    report_path.write_text(__import__("json").dumps({
        "source": "NCBI GEO GSE271300",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300",
        "intended_pipeline": "UNIVERSAL_LOG_v5.9.4.py",
        "numeric treatment encoding": "vehicle=0, MRTX1133=1",
        "usage": "All numeric columns are made available as candidate controls/fluxes. Cell/animal IDs remain text metadata and are not numeric controls.",
        "records": reports,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    for item in reports:
        print(item["model"], item["input_csv"], item["rows_cells"], "rows; numeric columns:", item["numeric_controls_and_fluxes"])
    print("Input manifest:", report_path)


if __name__ == "__main__":
    main()

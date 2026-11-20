from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = HERE / "candidate_Tiriac2018"
RUN = HERE / "Tiriac2018_Gemcitabine_all_controls_PDACDomain"
ABORTED = HERE / "Tiriac2018_cross_class_pipeline_runs"
PIPELINE = ROOT / "UNIVERSAL_LOG_v5.9.4.py"
OUTPUT = ROOT / "output" / "pdac_pipeline_audit_2026-11-19"
ZIP_PATH = OUTPUT / "TIRIAC2018_GEMCITABINE_ALL_CONTROLS_PDAC_AUDIT_BUNDLE.zip"
SHA_PATH = OUTPUT / "TIRIAC2018_GEMCITABINE_ALL_CONTROLS_PDAC_AUDIT_BUNDLE_SHA256.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_file(files: list[tuple[Path, str]], path: Path, arcname: str) -> None:
    if path.is_file():
        files.append((path, arcname))


def main() -> None:
    status_path = RUN / "RUN_MATRIX_STATUS.json"
    run_manifest_path = RUN / "RUN_MATRIX_MANIFEST.json"
    input_manifest_path = DATA / "PIPELINE_INPUT_MANIFEST.json"
    if not (status_path.is_file() and run_manifest_path.is_file() and input_manifest_path.is_file()):
        raise FileNotFoundError("Pipeline matrix is incomplete; wait for RUN_MATRIX_STATUS.json")
    run_status = json.loads(status_path.read_text(encoding="utf-8"))
    input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    if run_status.get("n_controls_requested") != 25 or run_status.get("n_completed") != 25 or run_status.get("n_error") != 0:
        raise ValueError(
            "Refusing to freeze a partial or failed matrix: "
            f"requested={run_status.get('n_controls_requested')} completed={run_status.get('n_completed')} errors={run_status.get('n_error')}"
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    files: list[tuple[Path, str]] = []
    for name in (
        "prepare_Tiriac2018_pipeline_data.py",
        "run_Tiriac2018_gemcitabine_all_controls.py",
        "summarize_Tiriac2018_pipeline_run.py",
        "create_Tiriac2018_pipeline_audit_pdf.py",
        "package_Tiriac2018_dataset.py",
        "package_Tiriac2018_pipeline_audit.py",
    ):
        add_file(files, HERE / name, f"scripts/{name}")
    for name in (
        "DATASET_AUDIT.md",
        "PIPELINE_INPUT_MANIFEST.json",
        "ENVIRONMENT_PIP_FREEZE.txt",
        "supplement_4775186.xlsx",
        "supplement_4775187.xlsx",
        "Tiriac2018_60PDO_completecase_drug_AUC.csv",
        "Tiriac2018_60PDO_PIPELINE_INPUT_AUDIT.zip",
        "Tiriac2018_60PDO_PIPELINE_INPUT_AUDIT_SHA256.txt",
    ):
        add_file(files, DATA / name, f"dataset/{name}")
    add_file(files, PIPELINE, "pipeline/UNIVERSAL_LOG_v5.9.4.py")
    for path in sorted(RUN.rglob("*")):
        if path.is_file():
            relative = path.relative_to(RUN)
            files.append((path, str(Path("run") / relative)))
    for path in sorted(ABORTED.rglob("*")):
        if path.is_file():
            relative = path.relative_to(ABORTED)
            files.append((path, str(Path("aborted_generic_attempt") / relative)))
    file_manifest = [
        {"archive_path": arcname.replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path, arcname in files
    ]
    readme = f"""# Tiriac 2018 PDAC PDO audit bundle

This is the reproducibility package for the completed UNIVERSAL_LOG v5.9.4 all-control-column run.

## Actual run

- Input: {input_manifest['observations']} complete matched PDO models; {input_manifest['n_fluxes']} AUC fluxes.
- Target: {run_manifest['target']} AUC, fixed across controls.
- Controls: {run_status['n_completed']} of {run_status['n_controls_requested']} non-target numeric columns, each run individually.
- Domain: {run_manifest['domain']}; mode: {run_manifest['mode']}; seed: {run_manifest['seed']}.
- Pipeline SHA-256: {run_manifest['pipeline_sha256']}.
- Input SHA-256: {run_manifest['input_sha256']}.

Each run has a console log, status, command, and original numerical exports under `run/by_control/`. The PDF companion summarizes the runs and carries this ZIP as an embedded attachment.

## Reproduction

The package includes the exact pipeline source, prepared CSV, source workbooks, preparation script, and frozen `.venv` package list. From the project root, rerun the preparation script, then the matrix runner; the input manifest documents identifier matching and complete-case exclusions.

## Scope and caution

The profiles are cross-sectional organoid AUCs, not a longitudinal patient record. The configured control is an AUC axis; `T0` is not a calendar-time transition, validated therapy threshold, or patient recommendation. The table contains no clinical outcome target. No efficacy or cure conclusion is made.

The earlier `generic`-domain attempt is retained separately under `aborted_generic_attempt/`; its four outputs are explicitly not treated as PDAC results.

## Source attribution and rights

Source: https://doi.org/10.1158/2159-8290.CD-18-0349. Third-party source files retain their original attribution and terms; this bundle does not relicense them.
"""

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5, allowZip64=True) as archive:
        archive.writestr("README.md", readme)
        for path, arcname in files:
            archive.write(path, arcname=arcname.replace("\\", "/"))
        archive.writestr("PACKAGE_FILE_SHA256.json", json.dumps(file_manifest, indent=2, ensure_ascii=False) + "\n")
    package_hash = sha256(ZIP_PATH)
    SHA_PATH.write_text(f"{package_hash}  {ZIP_PATH.name}\n", encoding="ascii")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP member integrity failed: {bad}")
    print(f"ZIP: {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes; SHA-256 {package_hash})")
    print(f"SHA: {SHA_PATH}")
    print(f"Members: {len(file_manifest)+2}; testzip=None")


if __name__ == "__main__":
    main()

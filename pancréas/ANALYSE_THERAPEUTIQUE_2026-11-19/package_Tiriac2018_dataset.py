from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
DATA = HERE / "candidate_Tiriac2018"
MANIFEST = DATA / "PIPELINE_INPUT_MANIFEST.json"
ZIP_PATH = DATA / "Tiriac2018_60PDO_PIPELINE_INPUT_AUDIT.zip"
SHA_PATH = DATA / "Tiriac2018_60PDO_PIPELINE_INPUT_AUDIT_SHA256.txt"
FILES = [
    (HERE / "prepare_Tiriac2018_pipeline_data.py", "scripts/prepare_Tiriac2018_pipeline_data.py"),
    (DATA / "DATASET_AUDIT.md", "audit/DATASET_AUDIT.md"),
    (DATA / "PIPELINE_INPUT_MANIFEST.json", "audit/PIPELINE_INPUT_MANIFEST.json"),
    (DATA / "supplement_4775186.xlsx", "source/supplement_4775186.xlsx"),
    (DATA / "supplement_4775187.xlsx", "source/supplement_4775187.xlsx"),
    (DATA / "Tiriac2018_60PDO_completecase_drug_AUC.csv", "input/Tiriac2018_60PDO_completecase_drug_AUC.csv"),
    (DATA / "ENVIRONMENT_PIP_FREEZE.txt", "environment/ENVIRONMENT_PIP_FREEZE.txt"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(DATA / manifest["input_csv"]) != manifest["input_sha256"]:
        raise ValueError("Prepared CSV SHA-256 does not match the input manifest")
    for source in manifest["source_files"]:
        if sha256(DATA / source["path"]) != source["sha256"]:
            raise ValueError(f"Source SHA-256 mismatch: {source['path']}")

    package_items = [
        {"archive_path": archive_path, "source_path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path, archive_path in FILES
    ]
    readme = f"""# Tiriac 2018 PDAC organoid pipeline input package

This package contains the exact source spreadsheets, the auditable 60-PDO complete-case input, its preparation script and data-provenance notes.

- Study: https://doi.org/10.1158/2159-8290.CD-18-0349
- Matched PDOs: {manifest['observations']}
- Numeric drug-AUC profiles: {manifest['n_fluxes']} ({len(manifest['chemo_fluxes'])} chemotherapy, {len(manifest['targeted_fluxes'])} targeted-agent profiles)
- Source workbook rows: 66 in each pharmacotyping table; unmatched source IDs and incomplete profiles are documented in the manifest.
- No values were imputed; no drug response rank or medical recommendation is supplied by this package.

Rebuild from the project root with `.venv\\Scripts\\python.exe pancréas\\ANALYSE_THERAPEUTIQUE_2026-11-19\\prepare_Tiriac2018_pipeline_data.py`.

The source files retain their original attribution and rights. This package does not apply the project's license to third-party materials.
"""
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        archive.writestr("README.md", readme)
        for path, archive_path in FILES:
            archive.write(path, arcname=archive_path)
        archive.writestr("PACKAGE_FILE_SHA256.json", json.dumps(package_items, indent=2, ensure_ascii=False) + "\n")
    package_hash = sha256(ZIP_PATH)
    SHA_PATH.write_text(f"{package_hash}  {ZIP_PATH.name}\n", encoding="ascii")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP integrity check failed at {bad}")
    print(f"ZIP: {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes; SHA-256 {package_hash})")
    print(f"SHA: {SHA_PATH}")


if __name__ == "__main__":
    main()

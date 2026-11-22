#!/usr/bin/env python
"""Reconstruct a scoped project tree from a full snapshot and a delta ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_target(root: Path, member: str) -> Path:
    normalized = member.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe member path: {member!r}")
    if path.parts[0].endswith(":"):
        raise ValueError(f"Drive-qualified member path: {member!r}")
    target = root.joinpath(*path.parts).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Member escapes destination: {member!r}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("delta", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-base-sha256", help="Optional explicit baseline hash; otherwise read from the delta manifest.")
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    delta = args.delta.resolve()
    destination = args.destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("Destination must be absent or empty; refusing to overwrite existing files.")
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(delta, "r") as delta_zip:
        manifest = json.loads(delta_zip.read("DELTA_MANIFEST.json").decode("utf-8"))
        if manifest.get("format") != "universal-log-project-delta-v1":
            raise ValueError("Unsupported or missing delta format.")
    expected = (args.expected_base_sha256 or manifest["baseline_snapshot_sha256"]).lower()
    if sha256_file(baseline) != expected:
        raise ValueError("Baseline SHA-256 does not match the delta manifest.")

    # Extract the baseline with explicit path traversal protection.
    with zipfile.ZipFile(baseline, "r") as base_zip:
        seen = set()
        for info in base_zip.infolist():
            if info.is_dir():
                continue
            relative = info.filename.replace("\\", "/")
            target = safe_target(destination, relative)
            if relative in seen:
                raise ValueError(f"Duplicate path in baseline archive: {relative}")
            seen.add(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            with base_zip.open(info, "r") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)

    # Apply replacements/additions and verify each SHA-256 before moving on.
    with zipfile.ZipFile(delta, "r") as delta_zip:
        for item in manifest["updated_files"]:
            relative = item["path"]
            target = safe_target(destination, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".delta-writing")
            h = hashlib.sha256()
            with delta_zip.open(relative, "r") as src, temporary.open("wb") as dst:
                for block in iter(lambda: src.read(8 * 1024 * 1024), b""):
                    h.update(block)
                    dst.write(block)
            if h.hexdigest() != item["sha256"]:
                temporary.unlink(missing_ok=True)
                raise ValueError(f"Delta file SHA-256 mismatch: {relative}")
            temporary.replace(target)
        for item in manifest.get("appended_files", []):
            source = safe_target(destination, item["base_path"])
            if not source.is_file() or source.stat().st_size != item["base_size_bytes"] or sha256_file(source) != item["base_sha256"]:
                raise ValueError(f"Append base file does not match: {item['base_path']}")
            target = safe_target(destination, item["path"])
            if target.exists():
                raise FileExistsError(f"Append target already exists: {item['path']}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            with delta_zip.open(item["patch_member"], "r") as patch, target.open("ab") as output:
                shutil.copyfileobj(patch, output, length=8 * 1024 * 1024)
            if target.stat().st_size != item["result_size_bytes"] or sha256_file(target) != item["result_sha256"]:
                raise ValueError(f"Appended output failed integrity check: {item['path']}")

    for item in manifest.get("moved_files", []):
        source = safe_target(destination, item["from"])
        target = safe_target(destination, item["to"])
        if not source.is_file():
            raise FileNotFoundError(f"Move source is missing: {item['from']}")
        if target.exists():
            raise FileExistsError(f"Move destination already exists: {item['to']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)

    with zipfile.ZipFile(delta, "r") as delta_zip:
        for relative in manifest["deleted_paths"]:
            target = safe_target(destination, relative)
            if target.is_file():
                target.unlink()

    result = {
        "status": "reconstructed",
        "version": manifest["version"],
        "baseline": baseline.name,
        "baseline_sha256_verified": expected,
        "updated_files": manifest["update_count"],
        "appended_files": manifest.get("append_count", 0),
        "moved_files": manifest.get("move_count", 0),
        "deleted_files": manifest["delete_count"],
        "destination": str(destination),
        "scope_note": manifest["reconstruction_note"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

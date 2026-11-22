#!/usr/bin/env python
"""Build an integrity-checked delta ZIP against an immutable full snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE_ACTIVE = ROOT / "output" / "master_whitepaper_v11" / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip"
DEFAULT_BASE_ARCHIVED = ROOT / "archive_sources" / "master_whitepaper_v11" / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V11_2026-11-22.zip"
DEFAULT_BASE = DEFAULT_BASE_ARCHIVED if DEFAULT_BASE_ARCHIVED.is_file() else DEFAULT_BASE_ACTIVE
DEFAULT_OUTPUT = ROOT / "output" / "deltas" / "DELTA_V12_2026-11-22.zip"
SNAPSHOT_PREFIX = "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def crc_size(path: Path) -> tuple[int, int]:
    size = 0
    crc = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            size += len(block)
            crc = zlib.crc32(block, crc)
    return size, crc & 0xFFFFFFFF


def safe_member(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe archive path: {name!r}")
    if path.parts[0].endswith(":"):
        raise ValueError(f"Drive-qualified archive path: {name!r}")
    return path.as_posix()


def excluded(relative: str, output_relative: str) -> bool:
    p = PurePosixPath(relative)
    parts_lower = [part.lower() for part in p.parts]
    if relative == output_relative or relative.startswith("output/deltas/"):
        return True
    if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in parts_lower):
        return True
    if p.suffix.lower() == ".pyc" or p.name.endswith(".building"):
        return True
    if p.suffix.lower() == ".zip" and p.name.startswith(SNAPSHOT_PREFIX):
        return True
    return False


def current_files(root: Path, output_path: Path) -> dict[str, Path]:
    try:
        output_relative = output_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        output_relative = "__external_output__"
    result: dict[str, Path] = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        dirs[:] = sorted(
            name for name in dirs
            if not (directory_path / name).is_symlink()
            and not excluded((directory_path / name).relative_to(root).as_posix() + "/x", output_relative)
        )
        for name in files:
            path = directory_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or excluded(relative, output_relative):
                continue
            result[safe_member(relative)] = path
    return result


def read_base_index(base: Path) -> dict[str, tuple[int, int]]:
    with zipfile.ZipFile(base, "r") as archive:
        return {
            safe_member(info.filename): (info.file_size, info.CRC)
            for info in archive.infolist() if not info.is_dir()
        }


def sha256_zip_member(archive: zipfile.ZipFile, name: str) -> str:
    digest = hashlib.sha256()
    with archive.open(name, "r") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_prefix(path: Path, byte_count: int) -> str:
    digest = hashlib.sha256()
    remaining = byte_count
    with path.open("rb") as stream:
        while remaining:
            block = stream.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise EOFError(f"File ended before {byte_count} bytes: {path.name}")
            digest.update(block)
            remaining -= len(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--version", default="V12")
    parser.add_argument("--base-sha256", help="Expected SHA-256; defaults to the adjacent .sha256 sidecar.")
    args = parser.parse_args()
    root = args.root.resolve()
    base = args.base.resolve()
    output = args.output.resolve()
    if not base.is_file():
        raise FileNotFoundError(base)
    if output == base:
        raise ValueError("Output path cannot overwrite the baseline snapshot.")
    sidecar = base.with_suffix(base.suffix + ".sha256")
    expected_base_sha = args.base_sha256
    if not expected_base_sha and sidecar.is_file():
        expected_base_sha = sidecar.read_text(encoding="ascii").split()[0].lower()
    if not expected_base_sha:
        raise ValueError("Provide --base-sha256 or an adjacent baseline .sha256 sidecar.")
    if len(expected_base_sha) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected_base_sha):
        raise ValueError("Expected base SHA-256 must be 64 hexadecimal characters.")
    output.parent.mkdir(parents=True, exist_ok=True)
    building = output.with_name(output.name + ".building")
    if output.exists() or building.exists():
        raise FileExistsError(f"Refusing to overwrite {output} or {building}.")

    started = time.perf_counter()
    baseline = read_base_index(base)
    files = current_files(root, output)
    current_meta: dict[str, tuple[int, int]] = {}
    print(f"Comparing {len(files):,} scoped files with {len(baseline):,} baseline members...", flush=True)
    for index, (relative, path) in enumerate(sorted(files.items()), 1):
        size, crc = crc_size(path)
        current_meta[relative] = (size, crc)
        if index % 1000 == 0:
            print(f"Compared {index:,}/{len(files):,} scoped files...", flush=True)

    added_paths = set(current_meta) - set(baseline)
    removed_paths = set(baseline) - set(current_meta)
    appends = []
    append_targets: set[str] = set()
    # Detect a PDF that is an incremental PyMuPDF append of a full PDF in the base.
    # Store only the appended suffix, never another complete copy of the old PDF.
    with zipfile.ZipFile(base, "r") as base_zip:
        for target_rel in sorted(added_paths):
            target_name = PurePosixPath(target_rel).name
            if not (target_name.startswith("UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_") and target_name.lower().endswith(".pdf")):
                continue
            target_path = files[target_rel]
            target_size = current_meta[target_rel][0]
            candidates = [
                name for name, (base_size, _crc) in baseline.items()
                if PurePosixPath(name).name.startswith("UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_")
                and name.lower().endswith(".pdf") and target_size > base_size
            ]
            for base_rel in sorted(candidates):
                base_size = baseline[base_rel][0]
                base_sha = sha256_zip_member(base_zip, base_rel)
                if sha256_prefix(target_path, base_size) != base_sha:
                    continue
                with target_path.open("rb") as stream:
                    stream.seek(base_size)
                    patch_data = stream.read()
                patch_sha = hashlib.sha256(patch_data).hexdigest()
                appends.append({
                    "path": target_rel,
                    "base_path": base_rel,
                    "base_size_bytes": base_size,
                    "base_sha256": base_sha,
                    "result_size_bytes": target_size,
                    "result_sha256": sha256_file(target_path),
                    "patch_member": f"delta_patches/pdf_append_{patch_sha}.bin",
                    "patch_size_bytes": len(patch_data),
                    "patch_sha256": patch_sha,
                    "_patch_data": patch_data,
                })
                append_targets.add(target_rel)
                break

    # Pair removed and added files with identical size/CRC as moves. This preserves
    # archive relocation without storing the moved bytes a second time.
    moves = []
    move_sources: set[str] = set()
    move_targets: set[str] = set()
    removed_by_meta: dict[tuple[int, int], list[str]] = {}
    for source_rel in sorted(removed_paths):
        removed_by_meta.setdefault(baseline[source_rel], []).append(source_rel)
    for target_rel in sorted(added_paths - append_targets):
        meta = current_meta[target_rel]
        candidates = removed_by_meta.get(meta, [])
        source_rel = next((candidate for candidate in candidates if candidate not in move_sources), None)
        if source_rel is None:
            continue
        moves.append({"from": source_rel, "to": target_rel, "size_bytes": meta[0], "crc32": f"{meta[1]:08x}"})
        move_sources.add(source_rel)
        move_targets.add(target_rel)

    updates = []
    for relative, path in sorted(files.items()):
        size, crc = current_meta[relative]
        old = baseline.get(relative)
        if relative in append_targets or relative in move_targets:
            continue
        if old != (size, crc):
            updates.append({
                "path": relative,
                "operation": "add" if old is None else "replace",
                "size_bytes": size,
                "sha256": sha256_file(path),
                "source": path,
            })
    deletions = sorted(removed_paths - move_sources)
    public_appends = [{key: value for key, value in item.items() if key != "_patch_data"} for item in appends]

    manifest = {
        "format": "universal-log-project-delta-v1",
        "version": args.version,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_snapshot_filename": base.name,
        "baseline_snapshot_sha256": expected_base_sha.lower(),
        "baseline_member_count": len(baseline),
        "scoped_current_file_count": len(files),
        "update_count": len(updates),
        "append_count": len(appends),
        "move_count": len(moves),
        "delete_count": len(deletions),
        "updated_files": [
            {key: value for key, value in item.items() if key != "source"}
            for item in updates
        ],
        "appended_files": public_appends,
        "moved_files": moves,
        "deleted_paths": deletions,
        "scope_exclusions": [
            ".git/", ".venv/", "__pycache__/", ".pytest_cache/", "*.pyc",
            "output/deltas/", "archive_sources/**/UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_*.zip",
        ],
        "reconstruction_note": "Extract baseline; apply updated_files; create appended_files by copying a verified base member and appending its suffix; apply moved_files; then remove deleted_paths. Historical snapshot ZIPs and runtime environments are separate archival dependencies, not part of this reconstructed project tree.",
        "integrity_note": "Updates, append suffixes and complete appended outputs carry SHA-256. Move discovery uses matching path content size/CRC. The reconstruction utility verifies the full baseline SHA-256 before extraction.",
    }
    try:
        with zipfile.ZipFile(building, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            for item in updates:
                source = item["source"]
                method = zipfile.ZIP_STORED if source.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".zip"} else zipfile.ZIP_DEFLATED
                archive.write(source, arcname=item["path"], compress_type=method)
            for item in appends:
                archive.writestr(item["patch_member"], item["_patch_data"], compress_type=zipfile.ZIP_STORED)
            archive.writestr("DELTA_MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
            archive.writestr("DELTA_RECONSTRUCTION_README.txt", (
                "This is an incremental update, not a standalone project archive.\n"
                f"Required baseline: {base.name}\n"
                f"Required baseline SHA-256: {expected_base_sha.lower()}\n"
                "Rebuild with reconstruct_project_from_delta.py BASE.zip DELTA.zip DESTINATION\n"
            ))
        with zipfile.ZipFile(building, "r") as archive:
            for item in updates:
                digest = hashlib.sha256()
                with archive.open(item["path"]) as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != item["sha256"]:
                    raise RuntimeError(f"Delta content verification failed: {item['path']}")
            for item in appends:
                digest = hashlib.sha256()
                with archive.open(item["patch_member"]) as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != item["patch_sha256"]:
                    raise RuntimeError(f"Append patch verification failed: {item['path']}")
        building.replace(output)
    except BaseException:
        building.unlink(missing_ok=True)
        raise
    print(json.dumps({
        "status": "complete",
        "baseline_members": len(baseline),
        "scoped_current_files": len(files),
        "updated_files": len(updates),
        "appended_files": len(appends),
        "moved_files": len(moves),
        "deleted_files": len(deletions),
        "delta_bytes": output.stat().st_size,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "output": output.name,
        "manifest": manifest,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

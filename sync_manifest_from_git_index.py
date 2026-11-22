#!/usr/bin/env python
"""Rewrite a CSV manifest's SHA-256 values to match exact Git index file bytes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
from pathlib import Path


def run_git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="Git worktree containing the staged publication files")
    parser.add_argument("--manifest", type=Path, required=True, help="Manifest CSV inside the worktree")
    args = parser.parse_args()
    repo = args.repo.resolve()
    manifest = args.manifest if args.manifest.is_absolute() else repo / args.manifest
    rows = list(csv.DictReader(manifest.open(encoding="utf-8-sig", newline="")))
    paths = [row["path"] for row in rows]
    listing = run_git(repo, "ls-files", "--stage", "-z", "--", *paths)
    path_to_oid: dict[str, str] = {}
    for item in listing.split(b"\0"):
        if not item:
            continue
        metadata, raw_path = item.split(b"\t", 1)
        mode, oid, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise RuntimeError(f"Unmerged index entry for {raw_path!r}")
        path_to_oid[raw_path.decode("utf-8")] = oid
    missing = [path for path in paths if path not in path_to_oid]
    if missing:
        raise FileNotFoundError("Paths are not staged in Git index:\n" + "\n".join(missing))
    oids = [path_to_oid[path] for path in paths]
    batch = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=repo,
        input=("\n".join(oids) + "\n").encode("ascii"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout
    cursor = 0
    updated = 0
    for row, oid in zip(rows, oids):
        newline = batch.find(b"\n", cursor)
        header = batch[cursor:newline].decode("ascii").split()
        if len(header) != 3 or header[0] != oid or header[1] != "blob":
            raise RuntimeError(f"Unexpected cat-file response for {row['path']}")
        size = int(header[2])
        start = newline + 1
        content = batch[start:start + size]
        if len(content) != size or batch[start + size:start + size + 1] != b"\n":
            raise RuntimeError(f"Truncated cat-file response for {row['path']}")
        cursor = start + size + 1
        new_hash = hashlib.sha256(content).hexdigest()
        updated += row["sha256"] != new_hash
        row["bytes"] = str(size)
        row["sha256"] = new_hash
    with manifest.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "group", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated {updated} SHA/size entries from {len(rows)} staged blobs in {manifest.name}.")


if __name__ == "__main__":
    main()

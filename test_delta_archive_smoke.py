#!/usr/bin/env python
"""Small end-to-end smoke check for the delta builder and reconstructor."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pymupdf as fitz


ROOT = Path(__file__).resolve().parent
BUILDER = ROOT / "build_project_delta.py"
RECONSTRUCTOR = ROOT / "reconstruct_project_from_delta.py"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="universal_log_delta_smoke_") as temp_name:
        temp = Path(temp_name)
        worktree = temp / "worktree"
        worktree.mkdir()
        (worktree / "keep.txt").write_text("keep\n", encoding="utf-8")
        (worktree / "replace.txt").write_text("new value\n", encoding="utf-8")
        (worktree / "added.txt").write_text("added\n", encoding="utf-8")
        (worktree / "archive_sources" / "historical").mkdir(parents=True)
        (worktree / "archive_sources" / "historical" / "moved.txt").write_text("same bytes moved\n", encoding="utf-8")
        v12_pdf_path = worktree / "output" / "master_whitepaper_v12" / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V12_smoke.pdf"
        v12_pdf_path.parent.mkdir(parents=True)
        base_pdf_path = temp / "base_whitepaper.pdf"
        base_pdf = fitz.open()
        base_pdf.new_page().insert_text((72, 72), "V11 base")
        base_pdf.save(base_pdf_path)
        base_pdf.close()
        appendix_pdf = fitz.open()
        appendix_pdf.new_page().insert_text((72, 72), "V12 appendix")
        appendix_pdf.save(temp / "appendix.pdf")
        appendix_pdf.close()
        import shutil
        shutil.copyfile(base_pdf_path, v12_pdf_path)
        v12_pdf = fitz.open(v12_pdf_path)
        appendix = fitz.open(temp / "appendix.pdf")
        v12_pdf.insert_pdf(appendix)
        appendix.close()
        v12_pdf.saveIncr()
        v12_pdf.close()
        (worktree / "archive_sources" / "historical" / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V4.zip").write_bytes(b"external archive")
        base = temp / "baseline.zip"
        with zipfile.ZipFile(base, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("keep.txt", "keep\n")
            archive.writestr("replace.txt", "old value\n")
            archive.writestr("delete.txt", "delete me\n")
            archive.writestr("old/moved.txt", "same bytes moved\n")
            archive.write(base_pdf_path, arcname="output/master_whitepaper_v11/UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V11_smoke.pdf")
        base_sha = hashlib.sha256(base.read_bytes()).hexdigest()
        base.with_suffix(base.suffix + ".sha256").write_text(f"{base_sha}  baseline.zip\n", encoding="ascii")
        delta = worktree / "output" / "deltas" / "SMOKE_DELTA.zip"
        subprocess.run([
            sys.executable, str(BUILDER), "--root", str(worktree), "--base", str(base),
            "--output", str(delta), "--version", "SMOKE", "--base-sha256", base_sha,
        ], check=True, capture_output=True, text=True)
        destination = temp / "reconstructed"
        subprocess.run([
            sys.executable, str(RECONSTRUCTOR), str(base), str(delta), str(destination),
        ], check=True, capture_output=True, text=True)
        assert (destination / "keep.txt").read_text(encoding="utf-8") == "keep\n"
        assert (destination / "replace.txt").read_text(encoding="utf-8") == "new value\n"
        assert (destination / "added.txt").read_text(encoding="utf-8") == "added\n"
        assert not (destination / "delete.txt").exists()
        assert not (destination / "old" / "moved.txt").exists()
        assert (destination / "archive_sources" / "historical" / "moved.txt").read_text(encoding="utf-8") == "same bytes moved\n"
        rebuilt_pdf = destination / "output" / "master_whitepaper_v12" / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V12_smoke.pdf"
        assert rebuilt_pdf.read_bytes() == v12_pdf_path.read_bytes()
        assert fitz.open(rebuilt_pdf).page_count == 2
        assert not (destination / "archive_sources" / "historical" / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_V4.zip").exists()
        print("PASS: add/replace/delete/move reconstructed; incremental PDF suffix reused the base; historical ZIP excluded.")


if __name__ == "__main__":
    main()

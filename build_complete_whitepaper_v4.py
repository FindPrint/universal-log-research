#!/usr/bin/env python3
"""Build a consolidated, self-contained Universal Log project whitepaper.

The PDF keeps the prior V3 audit intact, appends the later Ising and PDAC
reports, and embeds a ZIP snapshot of project files as a streamed attachment.
The snapshot intentionally excludes Git internals, the machine-specific venv,
and transient caches/render files; the scope is documented in the PDF and ZIP.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import shutil
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    StreamObject,
    TextStringObject,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "master_whitepaper_v4"
OUT.mkdir(parents=True, exist_ok=True)
ARCHIVE = OUT / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_2026-11-19.zip"
ARCHIVE_TEMP = OUT / "snapshot_build.tmp.zip"
PDF = OUT / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V4_2026-11-19.pdf"
CATALOG = OUT / "PROJECT_FILE_CATALOG_MASTER_2026-11-19.csv"
HASHES = OUT / "SHA256SUMS_MASTER_2026-11-19.txt"
EXCLUSIONS = OUT / "SCOPE_AND_EXCLUSIONS_2026-11-19.txt"
MANIFEST = OUT / "MASTER_WHITEPAPER_V4_MANIFEST.json"
PDF_SHA = OUT / "UNIVERSAL_LOG_LIVRE_BLANC_COMPLET_V4_2026-11-19.pdf.sha256"
ARCHIVE_SHA = OUT / "UNIVERSAL_LOG_FULL_PROJECT_SNAPSHOT_2026-11-19.zip.sha256"
FRONT = OUT / "front_matter.pdf"
PDF_TEMP = OUT / "master_build.tmp.pdf"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "tmp",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDED_TOP_REL = {"output/master_whitepaper_v4"}
PRECOMPRESSED = {
    ".7z", ".avi", ".bz2", ".docx", ".gif", ".gz", ".heic", ".jpeg",
    ".jpg", ".mp3", ".mp4", ".npy", ".npz", ".parquet", ".pdf", ".png",
    ".pptx", ".rar", ".sqlite", ".sqlite3", ".tif", ".tiff", ".webp",
    ".xlsx", ".xz", ".zip", ".zst",
}
CHUNK = 8 * 1024 * 1024


@dataclass(frozen=True)
class Appendix:
    path: Path
    title: str


APPENDICES = [
    Appendix(ROOT / "AUDIT_COMPLET_PIPELINE_V6_ISING_2026-11-15.pdf", "Ising classique - audit complet v6"),
    Appendix(ROOT / "pancréas" / "livre-blanc-pdac-v6.pdf", "PDAC - livre blanc v6 (version historique)"),
    Appendix(ROOT / "pancréas" / "livre-blanc-pdac-v6.1-2026-11-15.pdf", "PDAC - livre blanc v6.1"),
    Appendix(ROOT / "pancréas" / "Livre_Blanc_UNIVERSAL_LOG_PDAC_v1.0.pdf", "PDAC - livre blanc v1.0 (version historique)"),
    Appendix(ROOT / "pancréas" / "Rapport_Final_UNIVERSAL_LOG_PDAC_v1.0.pdf", "PDAC - rapport final v1.0 (version historique)"),
    Appendix(ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-16" / "AUDIT_PRISM_PDACS_v1_COMPLET.pdf", "PDAC - audit PRISM complet du 16 novembre"),
    Appendix(ROOT / "pancréas" / "ANALYSE_THERAPEUTIQUE_2026-11-16" / "daraxonrasib_resistance_2026" / "reanalyzed" / "AUDIT_ADDENDUM_RESISTANCE_DARAXONRASIB_PDACS_v1.pdf", "PDAC - reanalyse de la resistance au daraxonrasib"),
    Appendix(ROOT / "output" / "pdf" / "ADDENDUM_AUDIT_PDAC_MULTIFLUX_2026-11-17.pdf", "PDAC - audit multiflux du 17 novembre, version initiale"),
    Appendix(ROOT / "output" / "pdf" / "ADDENDUM_AUDIT_PDAC_MULTIFLUX_2026-11-17_v2_EXTERNAL_G12C.pdf", "PDAC - audit externe G12C, version 2"),
    Appendix(ROOT / "output" / "pdf" / "ADDENDUM_AUDIT_PDAC_MULTIFLUX_2026-11-17_v3_G12D_PARPi.pdf", "PDAC - analyse G12D et PARP, version 3"),
    Appendix(ROOT / "output" / "pdf" / "ADDENDUM_AUDIT_PDAC_MULTIFLUX_2026-11-17_v4_MAPPING_QA.pdf", "PDAC - controle du mapping multiflux, version 4"),
    Appendix(ROOT / "output" / "pdf" / "ADDENDUM_AUDIT_THERAPEUTIQUE_PDAC_2026-11-17.pdf", "PDAC - reanalyse therapeutique des donnees animales, 17 novembre"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def iter_payload_files() -> list[Path]:
    files: list[Path] = []
    for current, dirs, names in os.walk(ROOT, topdown=True, followlinks=False):
        current_path = Path(current)
        rel_current = current_path.relative_to(ROOT).as_posix()
        kept_dirs = []
        for d in dirs:
            child = current_path / d
            child_rel = child.relative_to(ROOT).as_posix()
            if d in EXCLUDED_DIR_NAMES or child.is_symlink():
                continue
            if any(child_rel == prefix or child_rel.startswith(prefix + "/") for prefix in EXCLUDED_TOP_REL):
                continue
            kept_dirs.append(d)
        dirs[:] = kept_dirs
        for name in names:
            path = current_path / name
            rel = path.relative_to(ROOT).as_posix()
            if any(rel == prefix or rel.startswith(prefix + "/") for prefix in EXCLUDED_TOP_REL):
                continue
            if path.is_symlink() or path.suffix.lower() == ".pyc":
                continue
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix().casefold())


def write_scope_file(file_count: int, input_bytes: int, payload_count: int, payload_bytes: int) -> None:
    gib = 1024 ** 3
    text = f"""UNIVERSAL_LOG project snapshot - scope statement
Snapshot date: 2026-11-19

The full project directory scan found {file_count:,} files and {input_bytes:,} bytes ({input_bytes / gib:.3f} GiB), including machine-specific and generated files.
The reproducible snapshot contains {payload_count:,} project files totaling {payload_bytes:,} bytes ({payload_bytes / gib:.3f} GiB) before ZIP compression.

Included: source code, theory notes, the 29-estimator/TLog materials, run configurations, raw and processed data present in the project, figures, result tables, audit reports, historical release artifacts, licenses, and reproducibility scripts.

Excluded: .git (repository internals and object database), .venv (machine-specific Python environment), tmp (temporary or render outputs), Python bytecode, and cache directories. These are not needed to interpret or rerun the analyses. The working Git tree had untracked project additions at snapshot time; therefore Git history is not represented by the ZIP. The full working files listed in the catalog are represented.

The archive includes a file catalog and SHA-256 manifest. Existing third-party datasets and publications retain their original terms; the project's MIT and CC BY 4.0 notices do not override source licenses or access conditions.

The ZIP itself and this final PDF are not included inside the snapshot to avoid recursion. The ZIP is embedded as an attachment in the PDF. External SHA-256 sidecars are delivered beside the PDF and ZIP.
"""
    EXCLUSIONS.write_text(text, encoding="utf-8")


def make_catalog_and_hashes(files: list[Path]) -> tuple[list[dict[str, object]], int]:
    records: list[dict[str, object]] = []
    total = 0
    with CATALOG.open("w", newline="", encoding="utf-8-sig") as csvfile, HASHES.open("w", encoding="utf-8") as hashfile:
        writer = csv.writer(csvfile)
        writer.writerow(["path", "bytes", "sha256"])
        for idx, path in enumerate(files, 1):
            before = path.stat()
            digest = sha256_file(path)
            after = path.stat()
            if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                raise RuntimeError(f"File changed while hashing: {path}")
            rel = path.relative_to(ROOT).as_posix()
            writer.writerow([rel, before.st_size, digest])
            hashfile.write(f"{digest}  {rel}\n")
            records.append({"path": rel, "bytes": before.st_size, "sha256": digest})
            total += before.st_size
            if idx % 250 == 0 or idx == len(files):
                print(f"SHA-256 {idx}/{len(files)} files; {total:,} bytes scanned", flush=True)
    return records, total


def make_archive(files: list[Path], total: int) -> dict[str, object]:
    with zipfile.ZipFile(ARCHIVE_TEMP, "w", allowZip64=True) as zf:
        zf.comment = b"Universal Log full project snapshot, 2026-11-19. See embedded catalog and SHA-256 manifest."
        for idx, path in enumerate(files, 1):
            rel = path.relative_to(ROOT).as_posix()
            compress_type = zipfile.ZIP_STORED if path.suffix.lower() in PRECOMPRESSED else zipfile.ZIP_DEFLATED
            level = None if compress_type == zipfile.ZIP_STORED else 1
            zf.write(path, arcname=rel, compress_type=compress_type, compresslevel=level)
            if idx % 250 == 0 or idx == len(files):
                print(f"ZIP {idx}/{len(files)} files", flush=True)
        zf.write(CATALOG, arcname="PROJECT_FILE_CATALOG_MASTER_2026-11-19.csv", compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
        zf.write(HASHES, arcname="SHA256SUMS_MASTER_2026-11-19.txt", compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
        zf.write(EXCLUSIONS, arcname="SCOPE_AND_EXCLUSIONS_2026-11-19.txt", compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
    with zipfile.ZipFile(ARCHIVE_TEMP, "r") as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        if len(zf.namelist()) != len(files) + 3:
            raise RuntimeError("ZIP entry count does not match catalog + scope files")
    ARCHIVE_TEMP.replace(ARCHIVE)
    archive_hash = sha256_file(ARCHIVE)
    ARCHIVE_SHA.write_text(f"{archive_hash}  {ARCHIVE.name}\n", encoding="ascii")
    print(f"ZIP complete: {ARCHIVE.stat().st_size:,} bytes; SHA-256 {archive_hash}", flush=True)
    return {"path": str(ARCHIVE), "bytes": ARCHIVE.stat().st_size, "sha256": archive_hash, "entries": len(files) + 3}


def repair_existing_archive() -> tuple[dict[str, object], list[dict[str, object]], int, int, int]:
    """Deduplicate the just-built ZIP and refresh hashes for the current builder."""
    with CATALOG.open("r", newline="", encoding="utf-8-sig") as stream:
        records = list(csv.DictReader(stream))
    if not records:
        raise RuntimeError("Existing project catalog is empty")
    replacements = {
        "build_complete_whitepaper_v4.py": ROOT / "build_complete_whitepaper_v4.py",
        "COMPLETE_WHITEPAPER_V4_README.md": ROOT / "COMPLETE_WHITEPAPER_V4_README.md",
        "REQUIREMENTS_WHITEPAPER_V4.txt": ROOT / "REQUIREMENTS_WHITEPAPER_V4.txt",
    }
    by_path = {str(row["path"]): row for row in records}
    for rel, source in replacements.items():
        if rel not in by_path or not source.is_file():
            raise RuntimeError(f"Cannot refresh snapshot entry: {rel}")
        by_path[rel]["bytes"] = source.stat().st_size
        by_path[rel]["sha256"] = sha256_file(source)
    file_paths = [ROOT / str(row["path"]) for row in records]
    if any(not path.is_file() for path in file_paths):
        missing = [str(path) for path in file_paths if not path.is_file()]
        raise RuntimeError(f"Snapshot files disappeared; full rebuild required: {missing[:5]}")
    for row, path in zip(records, file_paths):
        if row["path"] not in replacements and path.stat().st_size != int(row["bytes"]):
            raise RuntimeError(f"A project file changed after the snapshot; full rebuild required: {row['path']}")
    total = sum(int(row["bytes"]) for row in records)
    with CATALOG.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["path", "bytes", "sha256"])
        for row in records:
            writer.writerow([row["path"], row["bytes"], row["sha256"]])
    with HASHES.open("w", encoding="utf-8") as stream:
        for row in records:
            stream.write(f"{row['sha256']}  {row['path']}\n")
    full_files = [p for p in ROOT.rglob("*") if p.is_file() and OUT not in p.parents]
    full_bytes = sum(path.stat().st_size for path in full_files)
    write_scope_file(len(full_files), full_bytes, len(records), total)
    replace_content = {rel: path.read_bytes() for rel, path in replacements.items()}
    skipped_names = {
        "PROJECT_FILE_CATALOG_MASTER_2026-11-19.csv",
        "SHA256SUMS_MASTER_2026-11-19.txt",
        "SCOPE_AND_EXCLUSIONS_2026-11-19.txt",
        "output/master_whitepaper_v4/PROJECT_FILE_CATALOG_MASTER_2026-11-19.csv",
        "output/master_whitepaper_v4/SHA256SUMS_MASTER_2026-11-19.txt",
        "output/master_whitepaper_v4/SCOPE_AND_EXCLUSIONS_2026-11-19.txt",
    }
    seen: set[str] = set()
    with zipfile.ZipFile(ARCHIVE, "r") as old, zipfile.ZipFile(ARCHIVE_TEMP, "w", allowZip64=True) as new:
        for info in old.infolist():
            if info.filename in seen or info.filename in skipped_names:
                continue
            seen.add(info.filename)
            if info.filename in replace_content:
                new.writestr(info.filename, replace_content[info.filename], compress_type=info.compress_type, compresslevel=1 if info.compress_type == zipfile.ZIP_DEFLATED else None)
                continue
            with old.open(info, "r") as source, new.open(info, "w", force_zip64=True) as target:
                shutil.copyfileobj(source, target, length=CHUNK)
        for path in (CATALOG, HASHES, EXCLUSIONS):
            new.write(path, arcname=path.name, compress_type=zipfile.ZIP_DEFLATED, compresslevel=1)
    with zipfile.ZipFile(ARCHIVE_TEMP, "r") as check:
        names = check.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("Duplicate paths remain after ZIP repair")
        bad = check.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failure after repair: {bad}")
    ARCHIVE_TEMP.replace(ARCHIVE)
    archive_hash = sha256_file(ARCHIVE)
    ARCHIVE_SHA.write_text(f"{archive_hash}  {ARCHIVE.name}\n", encoding="ascii")
    archive_meta = {"path": str(ARCHIVE), "bytes": ARCHIVE.stat().st_size, "sha256": archive_hash, "entries": len(names)}
    return archive_meta, records, total, len(full_files), full_bytes


def draw_para(c: canvas.Canvas, text: str, x: float, y_top: float, width: float, style, gap: float = 7.0) -> float:
    from reportlab.platypus import Paragraph
    p = Paragraph(text, style)
    _, height = p.wrap(width, 700)
    p.drawOn(c, x, y_top - height)
    return y_top - height - gap


def build_front_matter(archive_meta: dict[str, object], records: list[dict[str, object]], total_payload_bytes: int) -> list[dict[str, object]]:
    from reportlab.lib.styles import ParagraphStyle

    pagesize = A4
    width, height = pagesize
    navy = colors.HexColor("#12233F")
    teal = colors.HexColor("#167D88")
    pale = colors.HexColor("#EAF1F4")
    text = colors.HexColor("#1F2937")
    small = ParagraphStyle("small", fontName="Helvetica", fontSize=9, leading=12, textColor=text)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14, textColor=text)
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=navy, spaceAfter=8)
    h3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=teal, spaceAfter=4)
    foot = "UNIVERSAL_LOG - Livre blanc integral V4 | 19 novembre 2026"
    c = canvas.Canvas(str(FRONT), pagesize=pagesize, pageCompression=1)
    c.setTitle("UNIVERSAL_LOG - Livre blanc integral du projet - V4")
    c.setAuthor("Projet UNIVERSAL_LOG")
    c.setSubject("Code, theorie, resultats, audits Ising et PDAC, provenance et reproduction")
    c.setKeywords("UNIVERSAL_LOG, TLog, audit, Ising, PDAC, reproduction, snapshot")

    # Page 1 - cover
    c.setFillColor(navy)
    c.rect(0, height - 210, width, 210, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(48, height - 86, "UNIVERSAL_LOG")
    c.setFont("Helvetica", 18)
    c.drawString(48, height - 121, "Livre blanc integral du projet")
    c.setFont("Helvetica", 12)
    c.drawString(48, height - 151, "Edition maitre V4 - dossier consolide jusqu'au 19 novembre 2026")
    c.setFillColor(teal)
    c.roundRect(48, height - 196, 110, 22, 7, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(103, height - 189, "AUDIT REPRODUCTIBLE")
    y = height - 246
    y = draw_para(c, "<b>Ce volume rassemble le livre blanc d'audit V3, l'audit Ising v6, les dossiers PDAC et les analyses therapeutiques produites jusqu'au 17 novembre.</b> Il conserve les versions anterieures comme traces historiques et ajoute une archive ZIP complete du contenu de travail reproductible.", 48, y, width - 96, body, 16)
    y = draw_para(c, f"Le ZIP attache contient {len(records):,} fichiers de projet, soit {total_payload_bytes:,} octets avant compression ({total_payload_bytes / (1024**3):.2f} GiB). Taille ZIP: {int(archive_meta['bytes']):,} octets. SHA-256 ZIP: <font name='Courier'>{archive_meta['sha256']}</font>.", 48, y, width - 96, small, 12)
    c.setFillColor(pale)
    c.roundRect(48, 115, width - 96, 108, 10, stroke=0, fill=1)
    y = 206
    y = draw_para(c, "<b>Licence du projet:</b> code MIT; documentation et resultats CC BY 4.0, selon les fichiers de licence du projet. Les donnees, articles et pieces provenant de tiers conservent leurs conditions d'origine.", 64, y, width - 128, small, 8)
    draw_para(c, "<b>Portee scientifique:</b> le dossier documente un outil multi-flux et ses usages. Les resultats inclus ne demontrent ni l'universalite du pipeline, ni un remede contre le cancer du pancreas, ni l'efficacite clinique d'une combinaison.", 64, y, width - 128, small, 4)
    c.setFillColor(colors.HexColor("#6B7280")); c.setFont("Helvetica", 8); c.drawString(48, 48, foot); c.drawRightString(width - 48, 48, "1")
    c.showPage()

    # Page 2 - executive reading guide and evidence boundaries
    c.setFillColor(navy); c.setFont("Helvetica-Bold", 22); c.drawString(48, height - 58, "Lire le dossier: faits, limites et decisions")
    y = height - 92
    y = draw_para(c, "<b>Le projet.</b> Le pipeline, ses 29 estimateurs, TLog, les configurations de flux et de controle, et les audits font partie de la theorie de travail. Ce livre blanc les documente comme un ensemble evolutif; il ne reduit pas la theorie a la formule finale de TLog.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>Ising.</b> Les configurations, executions et controles du protocole v6 sont ajoutes apres l'audit general V3. Les resultats restent circonscrits aux essais documentes; le lecteur doit distinguer un seuil interne du pipeline d'une mesure physique de Tc.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>PDAC - donnees cellulaires.</b> Le scan GSE309596 porte sur 115 664 cellules provenant de 12 echantillons, avec trois echantillons par bras. Parmi 328 comparaisons estimables, aucune ne passe q BH &lt; 0,05. Les cellules ne sont pas traitees comme des replicats biologiques; les plus grands effets bruts demeurent exploratoires.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>PDAC - donnees animales publiees.</b> La reanalyse du fichier source observe une croissance tumorale plus faible sous combinaison KRAS G12D + olaparib que sous monotherapies ou vehicule dans cinq modeles du meme article, avec six animaux par bras. C'est un signal preclinique a reproduire independamment; ce n'est ni une preuve clinique, ni une preuve de guerison, ni une demonstration generale de synergie.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>Statut des propositions.</b> Les resultats observes sont rapportes comme tels; les explications biologiques sont marquees comme interpretations; les experiences futures sont des hypotheses. Les analyses d'une meme publication ne sont pas comptees comme des validations independantes.", 48, y, width - 96, body, 12)
    c.setFillColor(pale); c.roundRect(48, 70, width - 96, 70, 8, stroke=0, fill=1)
    draw_para(c, "<b>Lecture recommandee:</b> commencer par l'audit V3, poursuivre avec l'audit Ising v6, puis lire les rapports PDAC selon leur date. Le catalogue et les empreintes SHA-256 se trouvent dans le ZIP attache.", 62, 124, width - 124, small, 0)
    c.setFillColor(colors.HexColor("#6B7280")); c.setFont("Helvetica", 8); c.drawString(48, 48, foot); c.drawRightString(width - 48, 48, "2")
    c.showPage()

    # Page 3 - dynamically paginated contents
    c.setFillColor(navy); c.setFont("Helvetica-Bold", 22); c.drawString(48, height - 58, "Sommaire et pagination")
    y = height - 92
    intro = "Les pages des documents ajoutes sont reproduites integralement. Le dernier appendice est aussi present dans l'archive ZIP, avec ses donnees, scripts et pieces justificatives."
    y = draw_para(c, intro, 48, y, width - 96, small, 13)
    toc_items = [
        ("Ouverture: couverture, lecture scientifique, sommaire et reproduction", 1, 4),
        ("Livre blanc UNIVERSAL_LOG V3 - code, TLog, experiences et audit historique", 5, 2006),
    ]
    page = 2011
    appendix_page_rows: list[dict[str, object]] = []
    for appendix in APPENDICES:
        reader = PdfReader(str(appendix.path), strict=False)
        count = len(reader.pages)
        appendix_page_rows.append({"title": appendix.title, "start_page": page, "end_page": page + count - 1, "pages": count, "path": str(appendix.path)})
        toc_items.append((appendix.title, page, count))
        page += count
    for title, start_page, count in toc_items:
        c.setFillColor(teal); c.rect(48, y - 1, 4, 12, stroke=0, fill=1)
        c.setFillColor(text); c.setFont("Helvetica-Bold", 9)
        display_title = title
        max_width = width - 148
        while stringWidth(display_title, "Helvetica-Bold", 9) > max_width and len(display_title) > 24:
            display_title = display_title[:-4] + "..."
        c.drawString(61, y, display_title)
        c.setFont("Helvetica", 9); c.drawRightString(width - 78, y, f"p. {start_page:,}")
        c.setFillColor(colors.HexColor("#6B7280")); c.setFont("Helvetica", 8); c.drawRightString(width - 48, y, f"{count} p.")
        y -= 21
    c.setFillColor(pale); c.roundRect(48, 70, width - 96, 65, 8, stroke=0, fill=1)
    draw_para(c, f"Pagination totale estimee: {page - 1:,} pages. Les references vers les jeux de donnees, versions historiques et scripts complets sont conservees dans l'archive jointe.", 62, 119, width - 124, small, 0)
    c.setFillColor(colors.HexColor("#6B7280")); c.setFont("Helvetica", 8); c.drawString(48, 48, foot); c.drawRightString(width - 48, 48, "3")
    c.showPage()

    # Page 4 - extraction, reproduction, and scope
    c.setFillColor(navy); c.setFont("Helvetica-Bold", 22); c.drawString(48, height - 58, "Reproduire et extraire l'archive")
    y = height - 92
    y = draw_para(c, "<b>Archive incluse.</b> Le PDF joint un seul ZIP qui reproduit les fichiers de projet presents a la date de l'audit: scripts, versions du pipeline, donnees, configurations, journaux, graphiques, rapports, licences et archives historiques. Le catalogue donne les chemins et tailles; le fichier SHA-256 permet de verifier les fichiers apres extraction.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>Extraction.</b> Ouvrir les pieces jointes du PDF avec un lecteur qui prend en charge les fichiers incorpores, ou utiliser pypdf. Le ZIP externe livre a cote du PDF est identique a la piece jointe et facilite l'extraction de plusieurs gigaoctets.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>Reproduction.</b> Depuis la racine extraite, consulter README_AUDIT_REPRODUCTION_V3.md et les README propres aux audits Ising et PDAC. Les commandes exactes, entrees, options et limites sont dans ces guides. L'environnement .venv n'est pas copie car il est lie a la machine; creer un environnement Python et installer les dependances indiquees dans les requirements fournis.", 48, y, width - 96, body, 12)
    y = draw_para(c, "<b>Exclusions explicites.</b> Le snapshot exclut .git (base d'objets et historique Git), .venv, tmp, caches et bytecode. Il contient le contenu de travail, pas une image disque exacte. Les modifications non commitees du depot sont presentes comme fichiers du snapshot; l'historique Git, lui, n'y est pas inclus.", 48, y, width - 96, body, 12)
    y = draw_para(c, f"<b>Empreinte du ZIP:</b> <font name='Courier'>{archive_meta['sha256']}</font><br/><b>Fichiers de travail inclus:</b> {len(records):,}<br/><b>Donnees non compressees:</b> {total_payload_bytes:,} octets ({total_payload_bytes / (1024**3):.2f} GiB)<br/><b>Version et date:</b> V4, 19 novembre 2026", 48, y, width - 96, small, 8)
    c.setFillColor(colors.HexColor("#6B7280")); c.setFont("Helvetica", 8); c.drawString(48, 48, foot); c.drawRightString(width - 48, 48, "4")
    c.showPage()
    c.save()
    return appendix_page_rows


class FileBackedEmbeddedStream(StreamObject):
    """PDF stream object that copies a large attachment in bounded memory."""

    def __init__(self, path: Path):
        super().__init__()
        self.path = path
        self.payload_length = path.stat().st_size
        self.payload_offset: int | None = None
        self.written_sha256: str | None = None
        self.update({
            NameObject("/Type"): NameObject("/EmbeddedFile"),
            NameObject("/Subtype"): NameObject("/application#2Fzip"),
            NameObject("/Length"): NumberObject(self.payload_length),
            NameObject("/Params"): DictionaryObject({NameObject("/Size"): NumberObject(self.payload_length)}),
        })

    def write_to_stream(self, stream) -> None:  # pypdf calls this with its output stream
        DictionaryObject.write_to_stream(self, stream)
        stream.write(b"\nstream\n")
        self.payload_offset = stream.tell()
        digest = hashlib.sha256()
        with self.path.open("rb") as source:
            while True:
                chunk = source.read(CHUNK)
                if not chunk:
                    break
                stream.write(chunk)
                digest.update(chunk)
        stream.write(b"\nendstream")
        self.written_sha256 = digest.hexdigest()


def add_large_attachment(writer: PdfWriter, path: Path, description: str) -> FileBackedEmbeddedStream:
    stream = FileBackedEmbeddedStream(path)
    stream_ref = writer._add_object(stream)
    file_spec = DictionaryObject({
        NameObject("/Type"): NameObject("/Filespec"),
        NameObject("/F"): TextStringObject(path.name),
        NameObject("/UF"): TextStringObject(path.name),
        NameObject("/Desc"): TextStringObject(description),
        NameObject("/AFRelationship"): NameObject("/Data"),
        NameObject("/EF"): DictionaryObject({NameObject("/F"): stream_ref, NameObject("/UF"): stream_ref}),
    })
    file_spec_ref = writer._add_object(file_spec)
    root = writer.root_object
    names = root.get(NameObject("/Names"))
    if names is None:
        names_dict = DictionaryObject()
        root[NameObject("/Names")] = writer._add_object(names_dict)
    else:
        names_dict = names.get_object()
    embedded = names_dict.get(NameObject("/EmbeddedFiles"))
    if embedded is None:
        embedded_dict = DictionaryObject()
        names_dict[NameObject("/EmbeddedFiles")] = writer._add_object(embedded_dict)
    else:
        embedded_dict = embedded.get_object()
    pairs = list(embedded_dict.get(NameObject("/Names"), ArrayObject()))
    for i in range(0, len(pairs), 2):
        try:
            if str(pairs[i].get_object()) == path.name:
                raise RuntimeError(f"Attachment name already exists: {path.name}")
        except AttributeError:
            if str(pairs[i]) == path.name:
                raise RuntimeError(f"Attachment name already exists: {path.name}")
    pairs.extend([TextStringObject(path.name), file_spec_ref])
    paired = [(str(pairs[i].get_object()), pairs[i], pairs[i + 1]) for i in range(0, len(pairs), 2)]
    paired.sort(key=lambda row: row[0].casefold())
    name_array = ArrayObject()
    for _, key, value in paired:
        name_array.extend([key, value])
    embedded_dict[NameObject("/Names")] = name_array
    af = root.get(NameObject("/AF"))
    af_array = af.get_object() if af is not None else ArrayObject()
    af_array.append(file_spec_ref)
    root[NameObject("/AF")] = af_array
    return stream


def hash_pdf_region(path: Path, start: int, size: int) -> str:
    digest = hashlib.sha256()
    remaining = size
    with path.open("rb") as stream:
        stream.seek(start)
        while remaining:
            chunk = stream.read(min(CHUNK, remaining))
            if not chunk:
                raise RuntimeError("PDF ended before the embedded ZIP stream was complete")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def build_master_pdf(appendix_rows: list[dict[str, object]], archive_meta: dict[str, object]) -> dict[str, object]:
    base_reader = PdfReader(str(ROOT / "AUDIT_UNIVERSAL_LOG_WHITEPAPER_V3.pdf"), strict=False)
    front_reader = PdfReader(str(FRONT), strict=False)
    writer = PdfWriter()
    writer.clone_document_from_reader(base_reader)
    for index, page in enumerate(front_reader.pages):
        writer.insert_page(page, index)
    writer.add_outline_item(title="Ouverture et guide de reproduction", page_number=0)
    writer.add_outline_item(title="Livre blanc UNIVERSAL_LOG V3 - audit historique", page_number=4)
    for row in appendix_rows:
        src = PdfReader(str(row["path"]), strict=False)
        writer.append(src, import_outline=False)
        writer.add_outline_item(title=str(row["title"]), page_number=int(row["start_page"]) - 1)
    stream = add_large_attachment(writer, ARCHIVE, "Snapshot reproductible complet des fichiers de projet au 19 novembre 2026; voir le catalogue et les empreintes SHA-256 inclus.")
    writer.add_metadata({
        "/Title": "UNIVERSAL_LOG - Livre blanc integral du projet - edition V4",
        "/Author": "Projet UNIVERSAL_LOG",
        "/Subject": "Audit reproductible du pipeline, de la theorie TLog, des essais Ising et des analyses PDAC",
        "/Keywords": "UNIVERSAL_LOG, TLog, Ising, PDAC, audit, reproduction",
        "/CreationDate": datetime.now().astimezone().strftime("D:%Y%m%d%H%M%S%z"),
        "/ModDate": datetime.now().astimezone().strftime("D:%Y%m%d%H%M%S%z"),
    })
    names_dict = writer.root_object.get(NameObject("/Names")).get_object()
    embedded_dict = names_dict.get(NameObject("/EmbeddedFiles")).get_object()
    name_array = embedded_dict.get(NameObject("/Names"))
    attachment_names = [str(name_array[i].get_object()) for i in range(0, len(name_array), 2)]
    if ARCHIVE.name not in attachment_names:
        raise RuntimeError("Project snapshot missing from PDF attachment name tree before write")
    with PDF_TEMP.open("wb") as out_stream:
        writer.write(out_stream)
    if stream.payload_offset is None or stream.written_sha256 is None:
        raise RuntimeError("PDF writer did not serialize the streamed ZIP attachment")
    if stream.written_sha256 != archive_meta["sha256"]:
        raise RuntimeError("Hash of ZIP payload written to the PDF differs from the archive")
    embedded_hash = hash_pdf_region(PDF_TEMP, stream.payload_offset, stream.payload_length)
    if embedded_hash != archive_meta["sha256"]:
        raise RuntimeError("Embedded ZIP bytes read back from the PDF do not match the external ZIP")
    PDF_TEMP.replace(PDF)
    pdf_hash = sha256_file(PDF)
    PDF_SHA.write_text(f"{pdf_hash}  {PDF.name}\n", encoding="ascii")
    expected_pages = 4 + 2006 + sum(int(row["pages"]) for row in appendix_rows)
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        info = subprocess.run([pdfinfo, str(PDF)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
        if not match or int(match.group(1)) != expected_pages:
            raise RuntimeError(f"Poppler page count mismatch: expected {expected_pages}; output was {info[:2000]}")
        actual_pages = int(match.group(1))
    else:
        print("WARNING: pdfinfo unavailable; expected page count is based on input documents.", flush=True)
        actual_pages = expected_pages
    return {"path": str(PDF), "bytes": PDF.stat().st_size, "sha256": pdf_hash, "pages": actual_pages, "attachments": len(attachment_names), "embedded_zip_sha256": embedded_hash, "embedded_zip_bytes": stream.payload_length, "payload_offset": stream.payload_offset}


def main() -> None:
    started = time.time()
    for appendix in APPENDICES:
        if not appendix.path.is_file():
            raise FileNotFoundError(f"Required source PDF missing: {appendix.path}")
    if "--repair-existing-archive" in sys.argv:
        archive_meta, records, total, full_count, full_bytes = repair_existing_archive()
        print(f"Repaired existing ZIP: {archive_meta['entries']} unique entries", flush=True)
    else:
        files = iter_payload_files()
        if not files:
            raise RuntimeError("No project payload files found")
        print(f"Project files to catalogue and archive: {len(files)}", flush=True)
        records, total = make_catalog_and_hashes(files)
        full_files = [p for p in ROOT.rglob("*") if p.is_file() and OUT not in p.parents]
        full_bytes = sum(p.stat().st_size for p in full_files)
        write_scope_file(len(full_files), full_bytes, len(records), total)
        archive_meta = make_archive(files, total)
        full_count = len(full_files)
    appendix_rows = build_front_matter(archive_meta, records, total)
    # Add the four-page front section to the expected final page offsets.
    pdf_meta = build_master_pdf(appendix_rows, archive_meta)
    manifest = {
        "edition": "V4 complete master whitepaper",
        "snapshot_date": "2026-11-19",
        "root": str(ROOT),
        "input_tree_files_including_exclusions": full_count,
        "input_tree_bytes_including_exclusions": full_bytes,
        "payload_files": len(records),
        "payload_bytes_before_zip": total,
        "archive": archive_meta,
        "pdf": pdf_meta,
        "excluded_directories": sorted(EXCLUDED_DIR_NAMES | {"output/master_whitepaper_v4"}),
        "appendices": appendix_rows,
        "build_seconds": round(time.time() - started, 2),
        "python": sys.version,
        "pypdf": __import__("pypdf").__version__,
        "reportlab": __import__("reportlab").Version,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"archive": archive_meta, "pdf": pdf_meta, "manifest": str(MANIFEST), "seconds": manifest["build_seconds"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()

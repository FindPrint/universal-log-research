from __future__ import annotations

import hashlib
from pathlib import Path

from pypdf import PdfReader
from pypdf._configuration import apply_configuration


HERE = Path(__file__).resolve().parent
PDF = HERE / "UNIVERSAL_LOG_TIRIAC2018_PDCAUDIT_ADDENDUM_2026-11-19.pdf"
EXPECTED = HERE / "TIRIAC2018_GEMCITABINE_ALL_CONTROLS_PDAC_AUDIT_BUNDLE.zip"
EMBEDDED_NAME = EXPECTED.name


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    expected_hash = sha256(EXPECTED.read_bytes())
    with apply_configuration(maximum_declared_stream_length=200_000_000):
        reader = PdfReader(str(PDF), strict=False)
        attachments = reader.attachments
        names = list(attachments.keys())
        if EMBEDDED_NAME not in names:
            raise SystemExit(f"Expected attachment missing; found: {names}")
        contents = attachments[EMBEDDED_NAME]
    if len(contents) != 1:
        raise SystemExit(f"Expected one embedded file, found {len(contents)}")
    embedded_hash = sha256(contents[0])
    print(f"pages={len(reader.pages)}")
    print(f"attachment={EMBEDDED_NAME}")
    print(f"embedded_bytes={len(contents[0])}")
    print(f"embedded_sha256={embedded_hash}")
    print(f"external_sha256={expected_hash}")
    print(f"match={embedded_hash == expected_hash}")
    if embedded_hash != expected_hash:
        raise SystemExit("Embedded audit ZIP differs from external ZIP")


if __name__ == "__main__":
    main()

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


OUT = Path(__file__).resolve().parent / "candidate_GSE194249_sources"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "GSE194249_PDPCOs_FPKM.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE194nnn/GSE194249/suppl/GSE194249_PDPCOs_FPKM.txt.gz",
    **{
        f"41467_2022_29857_MOESM{i}_ESM.xlsx": f"https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-29857-6/MediaObjects/41467_2022_29857_MOESM{i}_ESM.xlsx"
        for i in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]
    },
    "41467_2022_29857_MOESM1_ESM.pdf": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-29857-6/MediaObjects/41467_2022_29857_MOESM1_ESM.pdf",
    "41467_2022_29857_MOESM2_ESM.pdf": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-29857-6/MediaObjects/41467_2022_29857_MOESM2_ESM.pdf",
    "41467_2022_29857_MOESM3_ESM.pdf": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-29857-6/MediaObjects/41467_2022_29857_MOESM3_ESM.pdf",
    "41467_2022_29857_MOESM15_ESM.pdf": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-29857-6/MediaObjects/41467_2022_29857_MOESM15_ESM.pdf",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    records = []
    for name, url in SOURCES.items():
        dest = OUT / name
        request = urllib.request.Request(url, headers={"User-Agent": "UNIVERSAL_LOG-reproducibility/1.0"})
        with urllib.request.urlopen(request, timeout=90) as response, dest.open("wb") as output:
            expected = response.headers.get("Content-Length")
            while block := response.read(1024 * 1024):
                output.write(block)
        size = dest.stat().st_size
        if expected and size != int(expected):
            dest.unlink(missing_ok=True)
            raise IOError(f"Incomplete download {name}: expected {expected}, got {size}")
        records.append({"file": name, "url": url, "bytes": size, "sha256": sha256(dest)})
        print(f"DOWNLOADED {name} {size} {records[-1]['sha256']}")
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "accessions": ["GSE194249", "doi:10.1038/s41467-022-29857-6"],
        "source_files": records,
        "scope": "Source-data acquisition only. No pipeline run or biological inference is recorded by this script.",
    }
    (OUT / "SOURCE_ACQUISITION_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

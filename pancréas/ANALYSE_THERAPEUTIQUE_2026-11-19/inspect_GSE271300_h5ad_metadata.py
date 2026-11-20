from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_GSE271300"
OUT = ROOT / "GSE271300_H5AD_METADATA_AUDIT.json"


def text(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def values_for(obj) -> list[str]:
    if isinstance(obj, h5py.Group):
        if "codes" in obj and "categories" in obj:
            codes = np.asarray(obj["codes"])
            cats = [text(x) for x in np.asarray(obj["categories"])]
            return ["__NA__" if int(code) < 0 else cats[int(code)] for code in codes]
        return []
    return [text(x) for x in np.asarray(obj)]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(path: Path) -> dict:
    result = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
    with h5py.File(path, "r") as h5:
        result["root_keys"] = list(h5.keys())
        result["root_attrs"] = {str(k): text(v) for k, v in h5.attrs.items()}
        x = h5.get("X")
        if isinstance(x, h5py.Dataset):
            result["X"] = {"kind": "dense", "shape": list(x.shape), "dtype": str(x.dtype)}
        elif isinstance(x, h5py.Group):
            result["X"] = {
                "kind": "group",
                "keys": list(x.keys()),
                "attrs": {str(k): text(v) for k, v in x.attrs.items()},
            }
        else:
            result["X"] = None
        obs = h5.get("obs")
        if isinstance(obs, h5py.Group):
            columns = {}
            for name in obs.keys():
                vals = values_for(obs[name])
                if vals:
                    counts = Counter(vals)
                    columns[name] = {
                        "n": len(vals),
                        "n_unique": len(counts),
                        "top_counts": counts.most_common(30),
                    }
                elif isinstance(obs[name], h5py.Group):
                    columns[name] = {"kind": "group", "keys": list(obs[name].keys())}
            result["obs"] = {"n_obs": len(next(iter(obs.values()))) if len(obs) else 0, "columns": columns}
        var = h5.get("var")
        if isinstance(var, h5py.Group):
            result["var_keys"] = list(var.keys())
            if "_index" in var:
                result["n_var"] = len(var["_index"])
                result["var_index_examples"] = [text(v) for v in np.asarray(var["_index"][:10])]
    return result


def main() -> None:
    files = sorted(DATA.glob("*.h5ad"))
    if not files:
        raise SystemExit(f"No H5AD sources found in {DATA}")
    report = {
        "source": "NCBI GEO GSE271300",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE271300",
        "scope": "Structural metadata audit only; no per-cell hypothesis tests are performed.",
        "files": [inspect(path) for path in files],
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    for item in report["files"]:
        print(f"\n{item['file']} bytes={item['bytes']} SHA256={item['sha256']}")
        print("X:", item.get("X"))
        for name, column in item.get("obs", {}).get("columns", {}).items():
            lowered = name.lower()
            if any(token in lowered for token in ("hash", "sample", "condition", "treat", "model", "patient", "mouse", "orig", "batch", "mrtx", "vehicle", "veh", "ans", "b025")):
                print("OBS", name, column)
        print("n_var:", item.get("n_var"), "var examples:", item.get("var_index_examples"))
    print(f"\nMetadata audit: {OUT}")


if __name__ == "__main__":
    main()

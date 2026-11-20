from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALL_DIR = ROOT / "pipeline_runs_balanced15" / "PC69_target_basal" / "Treatment_code"
SINGLE_DIR = ROOT / "pipeline_runs_single15" / "PC69_target_basal" / "Treatment_code"
OUT = ROOT / "pipeline_runs_balanced15" / "comparison_all_vs_single_Treatment_code.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def first_differences(a, b, path="$", limit=25):
    diffs = []
    def walk(x, y, p):
        if len(diffs) >= limit:
            return
        if type(x) is not type(y):
            diffs.append({"path": p, "all_type": type(x).__name__, "single_type": type(y).__name__})
        elif isinstance(x, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x or k not in y:
                    diffs.append({"path": f"{p}.{k}", "difference": "key_missing"})
                else:
                    walk(x[k], y[k], f"{p}.{k}")
                if len(diffs) >= limit:
                    break
        elif isinstance(x, list):
            if len(x) != len(y):
                diffs.append({"path": p, "all_length": len(x), "single_length": len(y)})
            for i, (u, v) in enumerate(zip(x, y)):
                walk(u, v, f"{p}[{i}]")
                if len(diffs) >= limit:
                    break
        elif x != y:
            diffs.append({"path": p, "all_value": x, "single_value": y})
    walk(a, b, path)
    return diffs


def main():
    all_files = {p.name: p for p in ALL_DIR.iterdir() if p.is_file() and p.name != "console.log"}
    single_files = {p.name: p for p in SINGLE_DIR.iterdir() if p.is_file() and p.name != "console.log"}
    records = []
    for name in sorted(set(all_files) | set(single_files)):
        a, b = all_files.get(name), single_files.get(name)
        record = {"file": name, "present_in_all": a is not None, "present_in_single": b is not None}
        if a and b:
            record["bytes_all"] = a.stat().st_size
            record["bytes_single"] = b.stat().st_size
            record["sha256_all"] = digest(a)
            record["sha256_single"] = digest(b)
            record["byte_identical"] = record["sha256_all"] == record["sha256_single"]
            if name.endswith(".json") and not record["byte_identical"]:
                try:
                    x = json.loads(a.read_text(encoding="utf-8"))
                    y = json.loads(b.read_text(encoding="utf-8"))
                    record["json_structurally_equal"] = x == y
                    record["first_differences"] = first_differences(x, y)
                except Exception as exc:
                    record["json_compare_error"] = str(exc)
        records.append(record)
    report = {
        "comparison": "same input, same target, same seed/options; control-mode all subrun vs independent control-mode single run",
        "all_dir": str(ALL_DIR),
        "single_dir": str(SINGLE_DIR),
        "files": records,
        "identical_payload_count": sum(r.get("byte_identical", False) for r in records),
        "payload_count": sum(r["present_in_all"] and r["present_in_single"] for r in records),
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "comparison_report": str(OUT),
        "identical_payload_count": report["identical_payload_count"],
        "payload_count": report["payload_count"],
        "files": [{"file": r["file"], "byte_identical": r.get("byte_identical"), "json_structurally_equal": r.get("json_structurally_equal")} for r in records],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

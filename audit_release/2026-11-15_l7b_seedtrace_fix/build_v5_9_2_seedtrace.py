"""Build a traceable seed-reporting patch from the archived v5.9.1 audit copy.

This patch changes reporting metadata only. It does not alter estimator values,
L7b thresholds, or the scientific interpretation of any existing run.
"""
from __future__ import annotations

from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parent
SOURCE = RELEASE / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"
TARGET = HERE / "UNIVERSAL_LOG_v5_9_2_AUDITFIX_SEEDTRACE.py"
RECORD = HERE / "build_record.json"
DIFF = HERE / "v5_9_1_to_v5_9_2.diff"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    newline = "\r\n" if b"\r\n" in source_bytes else "\n"
    source_text = source_bytes.decode("utf-8").replace("\r\n", "\n")
    result = source_text

    result = replace_once(
        result,
        'VERSION_MASTER = "v5.9.1-L7aL7b-DKind-AuditFix"',
        'VERSION_MASTER = "v5.9.2-L7aL7b-DKind-AuditFix-SeedTrace"',
        "version label",
    )
    result = replace_once(
        result,
        "def _l7b_extract_summary(result):\n"
        '    """Extrait le minimum necessaire d un run pour L7b, sans dependre du detail interne."""',
        "def _l7b_extract_summary(result, seed=None):\n"
        '    """Extrait le resume L7b et conserve la graine connue par l appelant."""',
        "summary signature",
    )
    result = replace_once(
        result,
        '        return {\n'
        '            "T0_pct": t0,\n'
        '            "consensus_direction": (l7.get("consensus_direction") if isinstance(l7, dict) else None),\n'
        '            "global_confidence": _l7b_safe_float(l7.get("global_confidence")) if isinstance(l7, dict) else None,\n'
        '            "Delta": delta,\n'
        '            "dominant_regime": holo.get("dominant_regime") if isinstance(holo, dict) else None,\n'
        '            "L7_status": (l7.get("status") if isinstance(l7, dict) else None),\n'
        '        }',
        '        summary = {\n'
        '            "T0_pct": t0,\n'
        '            "consensus_direction": (l7.get("consensus_direction") if isinstance(l7, dict) else None),\n'
        '            "global_confidence": _l7b_safe_float(l7.get("global_confidence")) if isinstance(l7, dict) else None,\n'
        '            "Delta": delta,\n'
        '            "dominant_regime": holo.get("dominant_regime") if isinstance(holo, dict) else None,\n'
        '            "L7_status": (l7.get("status") if isinstance(l7, dict) else None),\n'
        '        }\n'
        '        if seed is not None:\n'
        '            summary["seed"] = int(seed)\n'
        '        return summary',
        "seed propagation",
    )
    result = replace_once(
        result,
        "                return _l7b_extract_summary(res)\n",
        "                return _l7b_extract_summary(res, seed=seed_v)\n",
        "known rerun seed",
    )

    diff_text = "".join(difflib.unified_diff(
        source_text.splitlines(keepends=True), result.splitlines(keepends=True),
        fromfile=SOURCE.name, tofile=TARGET.name, n=4,
    ))
    with DIFF.open("w", encoding="utf-8", newline="\n") as diff_file:
        diff_file.write(diff_text)

    target_bytes = result.replace("\n", newline).encode("utf-8")
    TARGET.write_bytes(target_bytes)
    record = {
        "artifact": TARGET.name,
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE.name,
        "source_sha256": sha256_bytes(source_bytes),
        "output_sha256": sha256_bytes(target_bytes),
        "diff_file": DIFF.name,
        "diff_sha256": sha256_bytes(diff_text.encode("utf-8")),
        "python": platform.python_version(),
        "patch_intent": "Carry the caller-known seed into each L7b rerun summary so the seed check exports its actual seed.",
        "changes": [
            "Version label changed to v5.9.2-L7aL7b-DKind-AuditFix-SeedTrace.",
            "_l7b_extract_summary accepts optional seed and exports it when provided.",
            "L7b rerun helper passes the seed value used for that rerun.",
        ],
        "expected_scope": "Traceability metadata only; no estimator, threshold, score, or verdict formula changed.",
    }
    RECORD.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Build Cohen-d-only copies of current and archived pipeline versions.

Original version files are never modified. Cliff's-delta remains as a legacy
callable for imported-code compatibility, but all shipped pipeline modes and
diagnostics use Cohen's d; custom requests for Cliff's delta are rejected.
"""
from __future__ import annotations

from datetime import datetime, timezone
import ast
import difflib
import hashlib
import json
from pathlib import Path
import platform
import re

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
VARIANTS = [
    {
        "name": "v5.3",
        "source": ROOT / "UNIVERSAL_LOG_v5_3.py",
        "target": ROOT / "UNIVERSAL_LOG_v5.3_COHEND_ONLY.py",
        "version": "v5.3-ControleRelatifNullCadre-CohenDOnly",
    },
    {
        "name": "v5.8",
        "source": ROOT / "UNIVERSAL_LOG_v5.8.py",
        "target": ROOT / "UNIVERSAL_LOG_v5.8_COHEND_ONLY.py",
        "version": "v5.8.0-MultiHorizon-L3L5L6-SemanticSplitL7-CohenDOnly",
    },
    {
        "name": "v5.9.0",
        "source": ROOT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py",
        "target": ROOT / "UNIVERSAL_LOG_v5.9.0_COHEND_ONLY.py",
        "version": "v5.9.0-L7aL7b-CoherenceRobustesse-CohenDOnly",
    },
    {
        "name": "v5.9.2-current-audit-candidate",
        "source": HERE / "UNIVERSAL_LOG_v5_9_2_AUDITFIX_SEEDTRACE.py",
        "target": ROOT / "UNIVERSAL_LOG_v5.9.2.py",
        "version": "v5.9.2-L7aL7b-DKind-AuditFix-SeedTrace-CohenDOnly",
    },
]
PREVIOUS_RECORD = HERE / "cohend_only_variant_build_record.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_once_in_function(text: str, function_name: str, old: str, new: str) -> str:
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    node = next((item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == function_name), None)
    if node is None:
        raise RuntimeError(f"Missing function {function_name}")
    segment = "".join(lines[node.lineno - 1:node.end_lineno])
    count = segment.count(old)
    if count != 1:
        raise RuntimeError(f"{function_name}: expected one denominator site, found {count}")
    segment = segment.replace(old, new, 1)
    lines[node.lineno - 1:node.end_lineno] = [segment]
    return "".join(lines)


def patch_source(text: str, version: str) -> str:
    version_pattern = re.compile(r'^VERSION_MASTER\s*=\s*"[^"]+"$', re.MULTILINE)
    text, version_count = version_pattern.subn(f'VERSION_MASTER = "{version}"', text, count=1)
    if version_count != 1:
        raise RuntimeError(f"version label: expected exactly one match, found {version_count}")

    stat_line = re.compile(r"^STATISTICAL_TEST\s*=.*$", re.MULTILINE)
    text, stat_count = stat_line.subn(
        "STATISTICAL_TEST = 'cohen_d'  # Cohen-d-only variant; Cliff helper is legacy only.",
        text, count=1,
    )
    if stat_count != 1:
        raise RuntimeError(f"STATISTICAL_TEST: expected exactly one match, found {stat_count}")

    text = replace_once_in_function(
        text, "cohen_d",
        "    pooled_std = np.sqrt((v1 + v2) / 2.0)\n",
        "    # Conventional pooled SD: weight sample variances by degrees of freedom.\n"
        "    pooled_var = ((len(g1) - 1) * v1 + (len(g2) - 1) * v2) / (len(g1) + len(g2) - 2)\n"
        "    pooled_std = np.sqrt(pooled_var)\n",
    )
    text = replace_once_in_function(
        text, "_scan_critical_threshold_fast",
        "                    pooled_std = np.sqrt((v1 + v2) / 2.0)\n",
        "                    pooled_var = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)\n"
        "                    pooled_std = np.sqrt(pooled_var)\n",
    )

    # The three historical mode presets that selected Cliff now use Cohen d.
    text = text.replace("'cliff_delta'", "'cohen_d'")
    text = text.replace('"cliff_delta"', '"cohen_d"')
    text = text.replace("test: cliff_delta", "test: cohen_d")

    text = replace_once(
        text,
        "    d = cohen_d(g1, g2) if stat_test == 'cohen_d' else cliff_delta(g1, g2, min_grp)\n",
        '    if stat_test != "cohen_d":\n'
        '        raise ValueError("This CohenDOnly pipeline accepts only stat_test=cohen_d")\n'
        "    d = cohen_d(g1, g2)\n",
        "separation score metric guard",
    )
    legacy_router = (
        "    if mode_cfg.get('test', 'cohen_d') != 'cohen_d':\n"
        "        return _scan_critical_threshold_legacy(\n"
        "            fluxes, control_series, mode_cfg, n_candidates, resolution,\n"
        "            w_size, min_grp)\n"
    )
    text = replace_once(
        text, legacy_router,
        '    if mode_cfg.get("test", "cohen_d") != "cohen_d":\n'
        '        raise ValueError("This CohenDOnly pipeline accepts only test=cohen_d")\n',
        "scan metric guard",
    )
    text = replace_once(
        text,
        "                cd = float(cliff_delta(ga, gb, min_grp=2))\n",
        "                cd = float(cohen_d(ga, gb))\n",
        "cross-class effect calculation",
    )

    # Rename the emitted field; retaining the old Cliff key would mislabel a
    # Cohen-d calculation and make downstream readers infer the wrong scale.
    text = text.replace("cliff_pairs", "cohen_d_pairs")
    text = text.replace("cliff_between_classes", "cohen_d_between_classes")
    text = text.replace("plus_cliff_delta", "plus_cohen_d")
    text = text.replace("Cliff's delta", "Cohen's d")
    text = text.replace("+ Cliff", "+ Cohen d")
    text = text.replace("+ Cliff's", "+ Cohen's")
    text = text.replace("cliff-delta", "Cohen-d")
    text = text.replace("Cliff-delta", "Cohen-d")

    # Mark the low-level function as retained compatibility code, not a path
    # used by this variant.
    text = replace_once(
        text,
        "def cliff_delta(g1, g2, min_grp=3):\n",
        "# Legacy compatibility helper. CohenDOnly pipeline paths never call this.\n"
        "def cliff_delta(g1, g2, min_grp=3):\n",
        "legacy helper annotation",
    )

    tree = ast.parse(text)
    active_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "cliff_delta"]
    if active_calls:
        raise RuntimeError(f"CohenDOnly source still has {len(active_calls)} active Cliff-delta call(s)")
    mode_tests = re.findall(r"'test':\s*'([^']+)'", text)
    if not mode_tests or any(value != "cohen_d" for value in mode_tests):
        raise RuntimeError(f"Not all mode presets use Cohen d: {mode_tests}")
    if '"cohen_d_between_classes"' not in text:
        raise RuntimeError("Cohen-d class diagnostic key was not written")
    return text


def main() -> None:
    previous_targets = {}
    if PREVIOUS_RECORD.is_file():
        previous = json.loads(PREVIOUS_RECORD.read_text(encoding="utf-8"))
        previous_targets = {item["target"]: item["target_sha256"] for item in previous.get("variants", [])}
    records = []
    for variant in VARIANTS:
        source_path: Path = variant["source"]
        target_path: Path = variant["target"]
        source_bytes = source_path.read_bytes()
        newline = "\r\n" if b"\r\n" in source_bytes else "\n"
        source = source_bytes.decode("utf-8").replace("\r\n", "\n")
        patched = patch_source(source, variant["version"])
        diff = "".join(difflib.unified_diff(
            source.splitlines(keepends=True), patched.splitlines(keepends=True),
            fromfile=source_path.name, tofile=target_path.name, n=3,
        ))
        diff_name = f"{variant['name'].replace('.', '_')}_cohend_only.diff"
        diff_path = HERE / diff_name
        with diff_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(diff)
        target_bytes = patched.replace("\n", newline).encode("utf-8")
        if target_path.exists():
            current_hash = sha256(target_path.read_bytes())
            known_hash = previous_targets.get(str(target_path.relative_to(ROOT)))
            if current_hash != known_hash:
                raise FileExistsError(f"Refusing to overwrite an unrecognized or modified variant: {target_path}")
        target_path.write_bytes(target_bytes)
        records.append({
            "name": variant["name"],
            "source": str(source_path.relative_to(ROOT)),
            "source_sha256": sha256(source_bytes),
            "target": str(target_path.relative_to(ROOT)),
            "target_sha256": sha256(target_bytes),
            "diff": str(diff_path.relative_to(ROOT)),
            "diff_sha256": sha256(diff.encode("utf-8")),
            "mode_presets_cohen_d_only": True,
            "active_cliff_delta_calls": 0,
        })
    report = {
        "status": "built",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "builder": Path(__file__).name,
        "selection_note": "A user-requested Cohen-d-only branch. Original files are unchanged; derived older versions inherit their source versions' other behavior and have not received full integration revalidation.",
        "metric_semantics": {
            "cohen_d": "Signed standardized mean difference; mathematically unbounded. CohenDOnly variants use the conventional pooled SD weighted by degrees of freedom.",
            "cliff_delta": "Signed pairwise dominance difference in [-1, 1]. Retained as an unused compatibility helper; it is not calculated by the shipped variants.",
            "equivalence": "Different estimands. Raw values, threshold choices, and outcomes are not guaranteed equal.",
            "compatibility": "Class diagnostic output key is renamed from cliff_between_classes to cohen_d_between_classes to avoid mislabeling values.",
            "formula_change": "Derived variants replace the archived equal-weight variance denominator with the conventional degrees-of-freedom weighted pooled standard deviation in cohen_d.",
        },
        "variants": records,
    }
    record_path = HERE / "cohend_only_variant_build_record.json"
    record_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

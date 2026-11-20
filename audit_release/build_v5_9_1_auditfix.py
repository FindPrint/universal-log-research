"""Build a traceable v5.9.1 audit copy without modifying supplied sources."""
from __future__ import annotations

import ast
import difflib
import hashlib
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
SOURCE_59 = PROJECT / "universal_x5f_log_x5f_L7a_x5f_L7b_x5f_v5.9.0f_0_n0z8.py"
SOURCE_58 = PROJECT / "UNIVERSAL_LOG_v5.8.py"
TARGET = OUT / "UNIVERSAL_LOG_v5_9_1_AUDITFIX.py"


def extract_function(source: str, name: str) -> str:
    lines = source.splitlines()
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return "\n".join(lines[node.lineno - 1:node.end_lineno])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Patch {label}: expected one target, found {count}")
    return source.replace(old, new, 1)


def fixed_l7b_function() -> str:
    return '''def level_robustness_L7b_from_summaries(ref, seed_alt, window_80, shuffled, log_run):
    """L7b-FULL summaries. Missing evidence is INDETERMINE; never votes UP/DOWN."""
    def _number(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value if np.isfinite(value) else None

    def _direction(value):
        return value in ("up", "down", "flat")

    def _ready(summary, require_delta=False):
        if not isinstance(summary, dict) or summary.get("L7_status") != "ok":
            return False
        if _number(summary.get("T0_pct")) is None or not _direction(summary.get("consensus_direction")):
            return False
        return not require_delta or _number(summary.get("Delta")) is not None

    try:
        if not isinstance(ref, dict):
            return {"version": "L7b-ROBUSTESSE", "mode": "full", "status": "error",
                    "verdict": "INDETERMINE", "lecture": "Resume de reference manquant, audit impossible.", "checks": {}}

        t0_ref = _number(ref.get("T0_pct"))
        dir_ref = ref.get("consensus_direction")
        delta_ref = _number(ref.get("Delta"))
        ref_ready = _ready(ref)

        # 1. Seed sensitivity: unavailable measurements are not scientific failures.
        if not ref_ready or not _ready(seed_alt):
            chk_seed = {"statut": "INDETERMINE", "detail": "Reference ou re-run graine incomplet; comparaison impossible."}
        else:
            t0_alt = _number(seed_alt.get("T0_pct"))
            distance = abs(t0_ref - t0_alt)
            same_direction = seed_alt.get("consensus_direction") == dir_ref
            if distance <= 5.0 and same_direction:
                chk_seed = {"statut": "PASS", "T0_ref": t0_ref, "T0_graine_alt": t0_alt,
                            "ecart_T0": round(distance, 3), "graine_alternative": seed_alt.get("seed"),
                            "direction_ref": dir_ref, "direction_graine_alt": seed_alt.get("consensus_direction"),
                            "detail": "T0 stable a 5 points et direction identique entre graines."}
            else:
                chk_seed = {"statut": "FAIL", "T0_ref": t0_ref, "T0_graine_alt": t0_alt,
                            "ecart_T0": round(distance, 3), "graine_alternative": seed_alt.get("seed"),
                            "direction_ref": dir_ref, "direction_graine_alt": seed_alt.get("consensus_direction"),
                            "detail": "La graine change T0 au-dela de 5 points ou change la direction."}

        # 2. Window sensitivity.
        if not ref_ready or not _ready(window_80):
            chk_window = {"statut": "INDETERMINE", "detail": "Reference ou re-run fenetre 80% incomplet; comparaison impossible."}
        else:
            t0_window = _number(window_80.get("T0_pct"))
            distance = abs(t0_ref - t0_window)
            same_direction = window_80.get("consensus_direction") == dir_ref
            if distance <= 10.0 and same_direction:
                chk_window = {"statut": "PASS", "T0_ref": t0_ref, "T0_fenetre_80": t0_window,
                              "ecart_T0": round(distance, 3), "direction_ref": dir_ref,
                              "direction_fenetre_80": window_80.get("consensus_direction"),
                              "detail": "T0 stable a 10 points et direction identique a 80% de la fenetre."}
            else:
                chk_window = {"statut": "FAIL", "T0_ref": t0_ref, "T0_fenetre_80": t0_window,
                              "ecart_T0": round(distance, 3), "direction_ref": dir_ref,
                              "direction_fenetre_80": window_80.get("consensus_direction"),
                              "detail": "La fenetre 80% change T0 au-dela de 10 points ou change la direction."}

        # 3. Order shuffle. Compare magnitudes because Delta=d_div-d_sat is signed.
        if not ref_ready or delta_ref is None or not _ready(shuffled, require_delta=True):
            chk_shuffle = {"statut": "INDETERMINE", "T0_ref": t0_ref,
                           "Delta_ref": delta_ref,
                           "detail": "Reference ou re-run melange sans T0/direction/Delta valide; effet de l'ordre non identifiable."}
        else:
            t0_shuffle = _number(shuffled.get("T0_pct"))
            delta_shuffle = _number(shuffled.get("Delta"))
            ref_magnitude = abs(delta_ref)
            shuffle_magnitude = abs(delta_shuffle)
            same_delta_sign = (delta_ref == 0.0 or delta_shuffle == 0.0 or np.sign(delta_ref) == np.sign(delta_shuffle))
            if ref_magnitude <= 1e-12:
                chk_shuffle = {"statut": "INDETERMINE", "T0_ref": t0_ref, "T0_melange": t0_shuffle,
                               "Delta_ref": delta_ref, "Delta_melange": delta_shuffle,
                               "detail": "Delta de reference nul ou quasi nul; une attenuation relative n'est pas definie."}
            elif not same_delta_sign:
                chk_shuffle = {"statut": "INDETERMINE", "T0_ref": t0_ref, "T0_melange": t0_shuffle,
                               "Delta_ref": delta_ref, "Delta_melange": delta_shuffle,
                               "rapport_magnitudes": shuffle_magnitude / ref_magnitude,
                               "detail": "Le signe de Delta change apres melange; la regle d'attenuation seule ne classe pas ce cas."}
            else:
                ratio = shuffle_magnitude / ref_magnitude
                shared = {"T0_ref": t0_ref, "T0_melange": t0_shuffle,
                          "Delta_ref": delta_ref, "Delta_melange": delta_shuffle,
                          "Delta_ref_magnitude": ref_magnitude,
                          "Delta_melange_magnitude": shuffle_magnitude,
                          "rapport_magnitudes": ratio,
                          "direction_ref": dir_ref,
                          "direction_melange": shuffled.get("consensus_direction")}
                if ratio < 0.5:
                    chk_shuffle = {"statut": "PASS", **shared,
                                   "detail": "La magnitude de Delta diminue d'au moins 50% apres melange; signal sensible a l'ordre selon le seuil implemente."}
                elif ratio < 0.8:
                    chk_shuffle = {"statut": "PASS", **shared,
                                   "detail": "La magnitude de Delta diminue entre 20% et 50% apres melange; attenuation selon le seuil implemente."}
                elif shuffled.get("consensus_direction") == dir_ref:
                    chk_shuffle = {"statut": "FAIL", **shared,
                                   "detail": "Magnitude de Delta et direction persistent sans ordre temporel; le signal peut venir de la distribution."}
                else:
                    chk_shuffle = {"statut": "INDETERMINE", **shared,
                                   "detail": "La magnitude de Delta persiste mais la direction change; attribution a l'ordre non resolue."}

        # 4. Log scaling is informative only and cannot make the overall verdict fail.
        if not ref_ready or not _ready(log_run):
            chk_scale = {"statut": "INDETERMINE", "sensibilite": "INCONNUE",
                         "detail": "Reference ou re-run logarithmique incomplet; sensibilite d'echelle non mesurable."}
        else:
            t0_log = _number(log_run.get("T0_pct"))
            distance = abs(t0_ref - t0_log)
            same_direction = log_run.get("consensus_direction") == dir_ref
            sensitive = distance > 20.0 or not same_direction
            chk_scale = {"statut": "INFORMATIF", "sensibilite": "SENSIBLE" if sensitive else "INVARIANT",
                         "T0_ref": t0_ref, "T0_log": t0_log, "ecart_T0": round(distance, 3),
                         "direction_ref": dir_ref, "direction_log": log_run.get("consensus_direction"),
                         "detail": "Le changement d'echelle modifie T0/direction." if sensitive else "Le changement d'echelle ne modifie pas T0/direction dans ce cas."}

        checks = {"graine": chk_seed, "fenetre": chk_window, "melange": chk_shuffle, "echelle": chk_scale}
        decisive = [chk_seed, chk_window, chk_shuffle]
        if any(check.get("statut") == "FAIL" for check in decisive):
            verdict = "FRAGILE"
            lecture = "Au moins un stress decisif echoue; ne pas utiliser L7a seul pour decider."
        elif any(check.get("statut") == "INDETERMINE" for check in decisive):
            verdict = "INDETERMINE"
            lecture = "Un stress decisif manque de mesures comparables; ne pas trancher."
        else:
            verdict = "ROBUSTE"
            lecture = "Les stress graine, fenetre et melange passent les regles implementees; cela ne prouve pas la validite de L7a."
        return {"version": "L7b-ROBUSTESSE", "mode": "full", "status": "ok", "verdict": verdict,
                "lecture": lecture,
                "ne_pas_confondre": "L7a-COHERENCE = vote interne UP/DOWN/FLAT. L7b-ROBUSTESSE = audit ROBUSTE/FRAGILE/INDETERMINE. Ne jamais moyenner les deux.",
                "reference": ref, "checks": checks}
    except Exception as exc:
        return {"version": "L7b-ROBUSTESSE", "mode": "full", "status": "error", "verdict": "INDETERMINE",
                "lecture": "L7b-full en erreur, ne pas interpreter L7a seul.", "detail": f"{type(exc).__name__}: {exc}", "checks": {}}
'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_59 = SOURCE_59.read_text(encoding="utf-8")
    source_58 = SOURCE_58.read_text(encoding="utf-8")
    patched = source_59

    # Restore v5.8's reviewed d_kind registry and consistency/export helpers.
    registry_start = source_58.index("D_KIND_REGISTRY = {")
    registry_end = source_58.index("def _check_dimension_for_tlog_partition():", registry_start)
    registry = source_58[registry_start:registry_end].rstrip()
    insertion = "def _check_dimension_for_tlog_partition():"
    if patched.count(insertion) != 1:
        raise RuntimeError("Cannot find unique taxonomy insertion point in v5.9")
    patched = patched.replace(insertion, registry + "\n\n" + insertion, 1)

    # Restore only the taxonomy-bearing state functions; their v5.8/v5.9 AST diff
    # was inspected and consists of the d_kind fields/aggregation being removed.
    for function_name in ("_empty_holographic", "compute_holographic_tension_state"):
        old_func = extract_function(patched, function_name)
        restored_func = extract_function(source_58, function_name)
        patched = replace_once(patched, old_func, restored_func, f"restore {function_name}")

    patched = replace_once(patched, "VERSION_MASTER = \"v5.9.0-L7aL7b-CoherenceRobustesse\"",
                           "VERSION_MASTER = \"v5.9.1-L7aL7b-DKind-AuditFix\"", "version master")
    patched = replace_once(patched, 'VERSION = VERSION_MASTER.split("-")[0]  # -> "v5.8.0"',
                           'VERSION = VERSION_MASTER.split("-")[0]  # -> "v5.9.1"', "version comment")
    # argparse interpolates percent signs in help strings using %-formatting.
    patched = replace_once(
        patched,
        'help="L7b-ROBUSTESSE FULL : audit complet graine + fenetre 80% + melange + log (~3-4x un run). Sans ce flag, L7b-LIGHT sans re-run."',
        'help="L7b-ROBUSTESSE FULL : audit complet graine + fenetre 80 pour cent + melange + log (environ 3 a 4 fois le cout d’un run). Sans ce flag, L7b-LIGHT sans re-run."',
        "argparse help percent formatting",
    )
    old_l7b = extract_function(patched, "level_robustness_L7b_from_summaries")
    patched = replace_once(patched, old_l7b, fixed_l7b_function(), "L7b summary semantics")

    # Make the alternate seed explicit and keep its generated folder label truthful.
    old_seed = "seed_alt = int(seed) + 81 if int(seed) != 123 else 42"
    new_seed = "seed_alt = 123 if int(seed) != 123 else 42"
    patched = replace_once(patched, old_seed, new_seed, "alternate seed selection")
    patched = replace_once(patched, '_one(str(csv_path), seed_alt, "seed123")',
                           '_one(str(csv_path), seed_alt, f"seed_{seed_alt}")', "alternate seed output folder")
    patched = replace_once(patched, '"seed_alt": _one(str(csv_path), seed_alt, f"seed_{seed_alt}"),',
                           '"seed_alt": _one(str(csv_path), seed_alt, f"seed_{seed_alt}"),\n                "seed_alt_seed": seed_alt,',
                           "alternate seed provenance")

    # Restore native machine-readable exports and typed fields in four-test CSV.
    export_anchor = "        df_feat.to_csv(out_path / 'df_feat.csv', index=False)\n    except Exception as _e:\n        _log_failure('df_feat_csv', _e)"
    export_replacement = "        df_feat.to_csv(out_path / 'df_feat.csv', index=False)\n    except Exception as _e:\n        _log_failure('df_feat_csv', _e)\n    try:\n        _write_estimator_measurement_type_exports(out_path)\n    except Exception as _e:\n        _log_failure('estimator_measurement_taxonomy_export', _e)"
    patched = replace_once(patched, export_anchor, export_replacement, "taxonomy CSV/JSON export")
    row_anchor = "                            'estimator_class': _entry.get('estimator_class'),\n                            'trajectory': _trajectory"
    row_replacement = "                            'estimator_class': _entry.get('estimator_class'),\n                            'd_kind': _entry.get('d_kind', ESTIMATOR_D_KIND.get(_estimator)),\n                            'quantity_type': _entry.get('quantity_type', ESTIMATOR_MEASUREMENT_TYPES.get(_estimator, {}).get('quantity_type')),\n                            'trajectory': _trajectory"
    patched = replace_once(patched, row_anchor, row_replacement, "typed estimator four-test export")

    # Restore the typed section in the human-readable report.
    report_anchor = "        f.write(f\"  T_log class median : {_geo.get('T_log_class_median')}\\n\")\n        f.write(f\"  Falsification : {_sig_txt}\\n\")"
    report_replacement = "        f.write(f\"  T_log class median : {_geo.get('T_log_class_median')}\\n\")\n        f.write(\"  T_log par d_kind: medians exploratoires, chaque type garde ses estimateurs\\n\")\n        for _kind, _entry in (_geo.get('T_log_by_d_kind') or {}).items():\n            f.write(f\"    {_kind}: d={_fmt_opt(_entry.get('d_median'))} T_log={_fmt_opt(_entry.get('T_log'))} estimateurs={_entry.get('estimators_used')} IQR={_fmt_opt(_entry.get('between_estimator_iqr'))}\\n\")\n        f.write(\"  La reference 4 reste a calibrer selon d_kind.\\n\")\n        f.write(f\"  Falsification : {_sig_txt}\\n\")"
    patched = replace_once(patched, report_anchor, report_replacement, "typed human-readable report")

    TARGET.write_text(patched + "\n", encoding="utf-8")
    # Store a plain, exact, reviewable change ledger and a unified diff.
    diff = "\n".join(difflib.unified_diff(
        source_59.splitlines(), patched.splitlines(),
        fromfile=str(SOURCE_59), tofile=str(TARGET), lineterm="",
    )) + "\n"
    (OUT / "v5.9.0_to_v5.9.1_auditfix.diff").write_text(diff, encoding="utf-8")
    import json
    provenance = {
        "source_v5_9": str(SOURCE_59), "source_v5_9_sha256": sha256(SOURCE_59),
        "taxonomy_source_v5_8": str(SOURCE_58), "taxonomy_source_v5_8_sha256": sha256(SOURCE_58),
        "derived_v5_9_1": str(TARGET), "derived_v5_9_1_sha256": sha256(TARGET),
        "changes": [
            "Restore v5.8 d_kind registry, validation helpers, per-estimator metadata, and T_log_by_d_kind while retaining legacy class medians.",
            "Restore estimator_measurement_types CSV/JSON export and typed estimator_four_tests columns.",
            "Correct missing-data handling in L7b full checks: missing reference/T0/direction/Delta becomes INDETERMINE.",
            "Compare signed Delta attenuation using magnitudes; sign reversals are INDETERMINE rather than silently classified.",
            "Make the alternate seed explicitly 123 (or 42 when the base seed is 123) and label its output folder truthfully.",
            "Fix argparse --help crash caused by an unescaped percent sign in the L7b FULL help text.",
            "Correct stale VERSION comment and identify derived module as v5.9.1.",
        ],
        "unchanged": [
            "Original user-provided v5.9 source file remains unmodified.",
            "29 estimator calculations and L7a implementation are not edited by this patcher.",
            "L7b implementation thresholds 5, 10, 20, 0.50, 0.80 and the 0.5 scale diagnostic remain uncalibrated implementation choices.",
        ],
    }
    (OUT / "v5.9.1_patch_provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(provenance, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

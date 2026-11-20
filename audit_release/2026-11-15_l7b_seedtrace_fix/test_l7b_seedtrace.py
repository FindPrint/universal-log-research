"""Focused regression checks for the v5.9.2 L7b seed traceability patch."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PIPELINE = Path(__file__).with_name("UNIVERSAL_LOG_v5_9_2_AUDITFIX_SEEDTRACE.py")
SPEC = importlib.util.spec_from_file_location("universal_log_seedtrace_test", PIPELINE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load pipeline module: {PIPELINE}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fake_run(t0: float, seed: int | None = None) -> dict:
    result = {
        "five_threshold_cascade": {"T_0_Monte_Carlo_Central": t0},
        "holographic_tension_state": {"Delta_tension": 1.25, "dominant_regime": "criticality"},
        "prediction_levels": {
            "L7_consensus": {
                "consensus_direction": "up",
                "global_confidence": 0.5,
                "status": "ok",
            }
        },
    }
    return MODULE._l7b_extract_summary(result, seed=seed)


class SeedTraceabilityTests(unittest.TestCase):
    def test_known_seed_is_preserved(self):
        self.assertEqual(fake_run(88.5, seed=123)["seed"], 123)

    def test_zero_seed_is_not_dropped(self):
        self.assertEqual(fake_run(88.5, seed=0)["seed"], 0)

    def test_omitted_seed_remains_optional(self):
        self.assertNotIn("seed", fake_run(88.5))

    def test_seed_check_exports_the_alternate_seed(self):
        reference = fake_run(89.0)
        alternate = fake_run(88.5, seed=123)
        result = MODULE.level_robustness_L7b_from_summaries(
            reference, alternate, reference, reference, reference
        )
        self.assertEqual(result["checks"]["graine"]["statut"], "PASS")
        self.assertEqual(result["checks"]["graine"]["graine_alternative"], 123)

    def test_full_check_runner_passes_seed_into_summary(self):
        with tempfile.TemporaryDirectory(prefix="l7b_seedtrace_") as temp:
            root = Path(temp)
            csv_path = root / "synthetic.csv"
            csv_path.write_text(
                "Control,Target\n" + "".join(f"{i},{2.0 + i / 100:.3f}\n" for i in range(60)),
                encoding="utf-8",
            )
            seen_seeds = []

            def fake_pipeline(**kwargs):
                seen_seeds.append(kwargs["seed"])
                return {
                    "five_threshold_cascade": {"T_0_Monte_Carlo_Central": 89.0},
                    "holographic_tension_state": {"Delta_tension": 1.25, "dominant_regime": "criticality"},
                    "prediction_levels": {
                        "L7_consensus": {
                            "consensus_direction": "up",
                            "global_confidence": 0.5,
                            "status": "ok",
                        }
                    },
                }

            with patch.object(MODULE, "_run_full_unified_pipeline_single", fake_pipeline):
                extra = MODULE._run_l7b_full_checks(
                    csv_path=str(csv_path), target_col="Target", control_col="Control",
                    domain="generic", risk=0.2, horizon=1, horizons=[1], seed=77,
                    mode="fast", base_out_path=str(root / "out"),
                    target_policy=None, target_resolution=None,
                    control_selection_info=None, max_workers=1,
                )

            self.assertEqual(extra["seed_alt_seed"], 123)
            self.assertEqual(extra["seed_alt"]["seed"], 123)
            self.assertEqual(seen_seeds, [123, 77, 77, 77])


if __name__ == "__main__":
    unittest.main(verbosity=2)

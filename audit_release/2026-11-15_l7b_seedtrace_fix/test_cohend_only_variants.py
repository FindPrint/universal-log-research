"""Checks for the requested Cohen-d-only version family."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
VARIANT_PATHS = [
    ROOT / "UNIVERSAL_LOG_v5.3_COHEND_ONLY.py",
    ROOT / "UNIVERSAL_LOG_v5.8_COHEND_ONLY.py",
    ROOT / "UNIVERSAL_LOG_v5.9.0_COHEND_ONLY.py",
    ROOT / "UNIVERSAL_LOG_v5.9.2.py",
]
LATEST_PATH = VARIANT_PATHS[-1]
BENCH_PATH = HERE / "cliff_vs_cohen_scan_benchmark.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CohenOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = [load_module(p, f"cohend_only_variant_{i}") for i, p in enumerate(VARIANT_PATHS)]
        cls.latest = cls.modules[-1]

    def test_all_derived_versions_import_and_configure_only_cohen_d(self):
        for module in self.modules:
            modes = module.PARAMETERS["modes"]
            self.assertTrue(modes)
            self.assertEqual({value.get("test", "cohen_d") for value in modes.values()}, {"cohen_d"})

    def test_no_active_cliff_calls_and_output_key_renamed(self):
        for path in VARIANT_PATHS:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "cliff_delta"]
            self.assertEqual(calls, [], path.name)
            self.assertIn('"cohen_d_between_classes"', source)
            self.assertNotIn('"cliff_between_classes"', source)

    def test_explicit_cliff_request_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "only stat_test=cohen_d"):
            self.latest.separation_score([1.0, 2.0], [0.0, 1.0], stat_test="cliff_delta")
        with self.assertRaisesRegex(ValueError, "only test=cohen_d"):
            self.latest.scan_critical_threshold(
                {"x": np.array([0., 1., 2., 3., 4., 5.])},
                np.linspace(0, 100, 6), {"test": "cliff_delta", "w_size": 2, "min_grp": 1},
                n_candidates=5, w_size=2, min_grp=1,
            )

    def test_cohen_d_uses_degrees_of_freedom_weighted_pooled_sd(self):
        actual = self.latest.cohen_d([1.0, 2.0, 3.0], [4.0, 5.0, 6.0, 7.0, 8.0])
        expected = (2.0 - 6.0) / np.sqrt(2.0)
        self.assertAlmostEqual(actual, expected, places=12)

    def test_latest_preserves_seed_trace_fix(self):
        self.assertIn("seed", self.latest._l7b_extract_summary(
            {
                "five_threshold_cascade": {"T_0_Monte_Carlo_Central": 90.0},
                "holographic_tension_state": {"Delta_tension": 0.5},
                "prediction_levels": {"L7_consensus": {"status": "ok", "consensus_direction": "up"}},
            }, seed=123,
        ))

    def test_latest_scan_matches_cohen_branch_on_archived_inputs(self):
        benchmark = json.loads(BENCH_PATH.read_text(encoding="utf-8"))
        for case in benchmark["results"]:
            csv_path = ROOT / Path(case["input_path"])
            df = pd.read_csv(csv_path)
            fluxes = {name: df[name].to_numpy(dtype=float) for name in case["fluxes"]}
            control = df["MC_Update"].to_numpy(dtype=float)
            axis_cfg = dict(self.latest.PARAMETERS["modes"]["fast"], random_seed=20261108)
            progress = self.latest._build_mc_progress_axis(control, fluxes, axis_cfg)["progress_pct"]
            cfg = dict(self.latest.PARAMETERS["modes"][case["mode_parameters_from_v5_9_1"]])
            threshold, _ = self.latest.scan_critical_threshold(
                fluxes, progress, cfg, n_candidates=case["n_candidates"],
                w_size=case["window_size"], min_grp=case["min_group_count"],
            )
            self.assertAlmostEqual(float(threshold), case["cohen_threshold"], places=10)

    def test_archived_comparison_records_non_equivalent_threshold_case(self):
        benchmark = json.loads(BENCH_PATH.read_text(encoding="utf-8"))
        small = [r for r in benchmark["results"] if r["input"] == "archived_80_row_slice"]
        self.assertTrue(small)
        self.assertTrue(all(r["threshold_equal"] is False for r in small))
        self.assertTrue(all(r["cliff_over_cohen_speed_ratio"] > 1.0 for r in benchmark["results"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

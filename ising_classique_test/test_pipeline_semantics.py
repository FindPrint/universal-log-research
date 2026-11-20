import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "UNIVERSAL_LOG_v5_3.py"
spec = importlib.util.spec_from_file_location("universal_log", SCRIPT)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)

class ControlAndFluxSelectionBenchmarks(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            "Temperature": np.linspace(1.5, 4.0, 80),
            "Energy": np.linspace(-2.0, -0.5, 80),
            "Magnetization": np.sin(np.linspace(0, 8, 80)),
            "Label": ["sample"] * 80,
        })

    def test_safe_defaults_are_single_control_and_harmonic_validation_off(self):
        self.assertEqual(ul.CONTROL_MODE, "single")
        self.assertFalse(ul.HARMONIC_VALIDATION_ENABLED)

    def test_single_control_fallback_chooses_first_numeric_axis(self):
        controls, info = ul.resolve_control_columns(
            self.frame, control_mode="single", default_column="Time"
        )
        self.assertEqual(controls, ["Temperature"])
        self.assertTrue(info["fallback_used"])

    def test_all_mode_remains_available_when_requested(self):
        controls, _ = ul.resolve_control_columns(self.frame, control_mode="all")
        self.assertEqual(controls, ["Temperature", "Energy", "Magnetization"])

    def test_default_fluxes_exclude_control_and_keep_other_numeric_columns(self):
        fluxes, info = ul.resolve_flux_columns(self.frame, "Temperature")
        self.assertEqual(fluxes, ["Energy", "Magnetization"])
        self.assertEqual(info["mode"], "all_numeric_except_control")

    def test_explicit_fluxes_keep_only_requested_observables(self):
        fluxes, info = ul.resolve_flux_columns(
            self.frame, "Temperature", ["Magnetization", "Energy"]
        )
        self.assertEqual(fluxes, ["Magnetization", "Energy"])
        self.assertEqual(info["mode"], "explicit")

    def test_explicit_fluxes_reject_missing_nonnumeric_and_control_columns(self):
        for requested, expected in [
            (["Missing"], "absentes"),
            (["Label"], "non numériques"),
            (["Temperature"], "contrôle"),
        ]:
            with self.subTest(requested=requested):
                with self.assertRaisesRegex(ValueError, expected):
                    ul.resolve_flux_columns(self.frame, "Temperature", requested)

class ModeOverrideBenchmarks(unittest.TestCase):
    def test_fixed_window_override_is_applied_and_auditable(self):
        base = {"w_size": 80, "min_grp": 2}
        updated, applied = ul._apply_experimental_mode_overrides(
            base, {"w_size": 600}
        )
        self.assertEqual(base["w_size"], 80)
        self.assertEqual(updated["w_size"], 600)
        self.assertEqual(applied, {"w_size": 600})

    def test_fixed_window_override_rejects_invalid_values(self):
        for value, error in [(1, ValueError), (2.5, TypeError), (True, TypeError)]:
            with self.subTest(value=value):
                with self.assertRaises(error):
                    ul._apply_experimental_mode_overrides({"w_size": 80}, {"w_size": value})
        with self.assertRaises(ValueError):
            ul._apply_experimental_mode_overrides({"w_size": 80}, {"min_grp": 4})

class ClassificationBenchmarks(unittest.TestCase):
    @staticmethod
    def landscape(d_sat, d_crit, d_div):
        values = {name: 1.0 for name in ul.ESTIMATOR_NAMES}
        for name in ul.DIMENSION_FOR_TLOG["saturation"]:
            values[name] = d_sat
        for name in ul.DIMENSION_FOR_TLOG["criticality"]:
            values[name] = d_crit
        for name in ul.DIMENSION_FOR_TLOG["divergence"]:
            values[name] = d_div
        values["SpectralDimension"] = 2.0
        return pd.DataFrame({f"flux_{name}_mean": [value]
                             for name, value in values.items()})

    def test_synthetic_regime_rules_are_labeled_heuristic_not_physical(self):
        cases = [
            ((2.0, 4.0, 3.7), "criticality"),
            ((2.0, 4.0, 6.0), "divergence"),
            ((2.0, 2.5, 3.0), "saturation"),
        ]
        for values, expected in cases:
            with self.subTest(expected=expected):
                result = ul.compute_holographic_tension_state(
                    self.landscape(*values), n_samples=100, control_col="Temperature"
                )
                self.assertEqual(result["dominant_regime"], expected)
                self.assertTrue(result["regime_is_heuristic"])
                self.assertFalse(result["regime_is_physical_call"])
                self.assertEqual(result["regime_classification_method"],
                                 "dimension_threshold_heuristic")

    def test_insufficient_dimensions_do_not_claim_a_regime(self):
        result = ul.compute_holographic_tension_state(
            pd.DataFrame({"unrelated": [1.0]}), n_samples=100, control_col="Temperature"
        )
        self.assertEqual(result["dominant_regime"], "indeterminate")
        self.assertFalse(result["regime_is_heuristic"])
        self.assertFalse(result["regime_is_physical_call"])

class TLogProfileBenchmarks(unittest.TestCase):
    def test_default_tlog_scale_is_labeled_row_count(self):
        self.assertEqual(
            ul.normalize_tlog_scales(None, default_n=105),
            [{"kind": "row_count", "value": 105}],
        )

    def test_custom_scales_are_preserved_as_separate_views(self):
        scales = ul.normalize_tlog_scales([
            {"kind": "observations", "value": 100},
            {"kind": "system_size", "value": 10000},
        ], default_n=12)
        self.assertEqual(scales, [
            {"kind": "observations", "value": 100},
            {"kind": "system_size", "value": 10000},
        ])

    def test_tlog_profiles_label_d_method_scale_and_missing_uncertainty(self):
        state = {
            "per_estimator": {
                "Higuchi": {"enters_geometric_D": True, "raw_median": 2.0,
                            "estimator_class": "saturation"},
                "Katz": {"enters_geometric_D": True, "raw_median": 2.4,
                         "estimator_class": "saturation"},
                "PermutationEntropy": {"enters_geometric_D": False,
                                        "raw_median": 0.5,
                                        "estimator_class": "saturation"},
            },
            "geometric_layer": {"axes": {
                "saturation": {"dimension_median": 2.0,
                               "estimators_used": ["Higuchi", "Katz"],
                               "n_dimension_estimators_used": 2},
            }},
        }
        d_uncertainty = {
            "status": "estimated", "method": "moving_block_bootstrap_over_progress_positions",
            "block_length_positions": 5,
            "interpretation": "block interval",
            "estimators": {"Higuchi": {"n_valid": 50, "se": 0.1,
                                         "ci95_low": 1.8, "ci95_high": 2.2}},
            "anchors": {"saturation": {"n_valid": 50, "se": 0.12,
                                        "ci95_low": 1.75, "ci95_high": 2.25}},
        }
        profiles = ul.build_tlog_profiles(state, [
            {"kind": "observations", "value": 100},
            {"kind": "system_size", "value": 10000},
        ], d_uncertainty=d_uncertainty)
        self.assertEqual(len(profiles), 2)
        self.assertEqual(profiles[0]["n_scale"]["kind"], "observations")
        self.assertAlmostEqual(profiles[0]["estimator_readings"]["Higuchi"]["T_log"],
                               -2.0 * np.log(100), places=5)
        self.assertAlmostEqual(profiles[1]["anchor_readings"]["saturation"]["T_log"],
                               -2.0 * np.log(10000), places=5)
        self.assertNotIn("PermutationEntropy", profiles[0]["estimator_readings"])
        self.assertEqual(profiles[0]["estimator_readings"]["Higuchi"]["uncertainty"]["status"],
                         "estimated")
        self.assertAlmostEqual(
            profiles[0]["estimator_readings"]["Higuchi"]["uncertainty"]["T_log_se"],
            0.1 * np.log(100), places=5
        )
        self.assertIn("n est traité comme une valeur fixe",
                      profiles[0]["estimator_readings"]["Higuchi"]["uncertainty"]["n_scale_uncertainty"])
        self.assertIsNotNone(
            profiles[0]["anchor_readings"]["saturation"]["between_estimator_spread"]
        )
        self.assertEqual(profiles[0]["global_tension"]["status"], "not_defined")

    def test_moving_block_bootstrap_estimates_d_uncertainty_without_claiming_row_independence(self):
        n = 80
        progress = np.arange(n, dtype=float)
        frame = pd.DataFrame({
            "Progress": progress,
            "Energy_Higuchi_mean": 1.4 + 0.2 * np.sin(progress / 7.0),
            "Magnetization_Higuchi_mean": 1.6 + 0.15 * np.cos(progress / 9.0),
        })
        uncertainty = ul.estimate_tlog_d_uncertainty(
            frame, n_input_rows=40, window_size=10, n_bootstrap=50, seed=4
        )
        self.assertEqual(uncertainty["status"], "estimated")
        self.assertEqual(uncertainty["block_length_positions"], 20)
        self.assertEqual(uncertainty["estimators"]["Higuchi"]["n_valid"], 50)
        self.assertIn("pas une incertitude universelle", uncertainty["interpretation"])
        sensitivity = ul.estimate_tlog_d_uncertainty(
            frame, n_input_rows=40, window_size=10, n_bootstrap=30, seed=4,
            block_length_positions=8
        )
        self.assertEqual(sensitivity["block_length_positions"], 8)
        self.assertEqual(sensitivity["block_length_source"], "explicit_sensitivity_override")

    def test_uncertainty_is_unavailable_when_window_covers_landscape(self):
        frame = pd.DataFrame({
            "Progress": np.arange(20, dtype=float),
            "Energy_Higuchi_mean": np.linspace(1.0, 2.0, 20),
        })
        uncertainty = ul.estimate_tlog_d_uncertainty(
            frame, n_input_rows=20, window_size=20, n_bootstrap=50
        )
        self.assertEqual(uncertainty["status"], "not_estimated")

    def test_tlog_scale_requires_kind_and_finite_value_greater_than_one(self):
        for item in [
            {"kind": "", "value": 10},
            {"kind": "rows", "value": 1},
            {"kind": "rows", "value": float("nan")},
            {"kind": "rows", "value": "invalid"},
        ]:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    ul.normalize_tlog_scales([item], default_n=10)

    def test_cli_scale_syntax(self):
        self.assertEqual(ul.parse_tlog_scale_args(["rows=105", "system=4096"]), [
            {"kind": "rows", "value": "105"},
            {"kind": "system", "value": "4096"},
        ])
        with self.assertRaises(ValueError):
            ul.parse_tlog_scale_args(["missing_separator"])

    def test_window_size_resolves_from_pipeline_metadata_shapes(self):
        self.assertEqual(ul.resolve_tlog_window_size({"metadata": {"w_size": 21}}), 21)
        self.assertEqual(ul.resolve_tlog_window_size({
            "metadata": {"threshold_optimization": {"best_config": {"w_size": 17}}}
        }), 17)
        self.assertEqual(ul.resolve_tlog_window_size({
            "metadata": {"threshold_metadata": {"w_size": 13}}
        }), 13)
        self.assertIsNone(ul.resolve_tlog_window_size({"metadata": {}}))

if __name__ == "__main__":
    unittest.main(verbosity=2)

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "UNIVERSAL_LOG_v5.8.py"
spec = importlib.util.spec_from_file_location("universal_log_v58_taxonomy_test", SCRIPT)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


class MeasurementTaxonomyV58Tests(unittest.TestCase):
    def test_all_29_estimators_have_one_consistent_measurement_type(self):
        self.assertEqual(len(ul.ESTIMATOR_NAMES), 29)
        self.assertEqual(set(ul.ESTIMATOR_D_KIND), set(ul.ESTIMATOR_NAMES))
        self.assertEqual(set(ul.ESTIMATOR_MEASUREMENT_TYPES), set(ul.ESTIMATOR_NAMES))
        self.assertEqual(len(ul.ESTIMATOR_D_KIND), len(set(ul.ESTIMATOR_D_KIND)))

        tlog_names = {
            name for members in ul.DIMENSION_FOR_TLOG.values() for name in members
        }
        typed_dimension_names = {
            name for name, kind in ul.ESTIMATOR_D_KIND.items()
            if ul.D_KIND_REGISTRY[kind]["quantity_type"] == "dimension_proxy"
        }
        self.assertEqual(len(tlog_names), 21)
        self.assertEqual(typed_dimension_names, tlog_names)
        self.assertEqual(len(set(ul.ESTIMATOR_NAMES) - tlog_names), 8)

    def test_registry_exports_include_all_29_estimators(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = ul._write_estimator_measurement_type_exports(directory)
            csv = pd.read_csv(paths["csv"])
            data = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
        self.assertEqual(len(csv), 29)
        self.assertEqual(set(csv["estimator"]), set(ul.ESTIMATOR_NAMES))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(set(data["estimators"]), set(ul.ESTIMATOR_NAMES))

    def test_tlog_state_exposes_types_and_does_not_mix_typed_profiles(self):
        landscape = pd.DataFrame({
            f"flux_{name}_mean": np.array([2.0, 3.0, 4.0])
            for name in ul.ESTIMATOR_NAMES
        })
        state = ul.compute_holographic_tension_state(
            landscape, scores={}, n_samples=128, control_col="temperature"
        )

        self.assertEqual(state["measurement_taxonomy_schema_version"], "1.0")
        self.assertEqual(set(state["estimator_measurement_types"]), set(ul.ESTIMATOR_NAMES))
        self.assertEqual(set(state["per_estimator"]), set(ul.ESTIMATOR_NAMES))
        for name in ul.ESTIMATOR_NAMES:
            row = state["per_estimator"][name]
            self.assertEqual(row["d_kind"], ul.ESTIMATOR_D_KIND[name])
            self.assertEqual(row["quantity_type"], ul.D_KIND_REGISTRY[row["d_kind"]]["quantity_type"])

        geometric = state["geometric_layer"]
        self.assertIn("T_log_by_d_kind", geometric)
        self.assertEqual(set(geometric["T_log_by_estimator"]), tlog_names_from_code(ul))
        for name, profile in geometric["T_log_by_estimator"].items():
            self.assertEqual(profile["d_kind"], ul.ESTIMATOR_D_KIND[name])
        expected_kinds = {
            ul.ESTIMATOR_D_KIND[name] for name in tlog_names_from_code(ul)
        }
        self.assertEqual(set(geometric["T_log_by_d_kind"]), expected_kinds)
        for kind, profile in geometric["T_log_by_d_kind"].items():
            self.assertTrue(profile["estimators_used"])
            self.assertTrue(all(ul.ESTIMATOR_D_KIND[name] == kind for name in profile["estimators_used"]))
            self.assertEqual(profile["formula"], "(d-4)*log(n)")
            self.assertEqual(profile["status"], "exploratory_requires_domain_calibration")
            if len(profile["estimators_used"]) == 1:
                self.assertIsNone(profile["between_estimator_iqr"])
                self.assertEqual(profile["between_estimator_iqr_status"], "not_estimable_single_estimator")

        for axis in geometric["axes"].values():
            if not axis["semantic_type_homogeneous"]:
                self.assertIsNotNone(axis["semantic_warning"])


def tlog_names_from_code(module):
    return {
        name for members in module.DIMENSION_FOR_TLOG.values() for name in members
    }


if __name__ == "__main__":
    unittest.main()

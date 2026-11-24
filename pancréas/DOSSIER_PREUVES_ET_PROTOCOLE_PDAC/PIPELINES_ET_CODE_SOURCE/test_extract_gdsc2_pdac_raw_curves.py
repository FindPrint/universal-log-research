from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import extract_gdsc2_pdac_raw_curves as gdsc_extractor
from extract_gdsc2_pdac_raw_curves import normalize_scan


def _row(
    position: int,
    tag: str,
    intensity: float,
    drug_id: str = "NA",
    concentration: float | str = "NA",
) -> dict[str, str]:
    return {
        "SCAN_ID": "scan-1",
        "BARCODE": "plate-1",
        "RESEARCH_PROJECT": "GDSC_SA",
        "DATE_CREATED": "2015-02-13",
        "SCAN_DATE": "2015-02-17",
        "COSMIC_ID": "753624",
        "CELL_ID": "4712",
        "MASTER_CELL_ID": "198",
        "SANGER_MODEL_ID": "SIDM00934",
        "CELL_LINE_NAME": "CAPAN-1",
        "ASSAY": "Glo",
        "DURATION": "4",
        "SEEDING_DENSITY": "250",
        "DRUGSET_ID": "drugset-1",
        "POSITION": str(position),
        "TAG": tag,
        "DRUG_ID": drug_id,
        "CONC": str(concentration),
        "INTENSITY": str(intensity),
    }


class NormalizeScanTests(unittest.TestCase):
    def test_uses_sanger_controls_and_trims_to_zero_one(self) -> None:
        rows = [
            _row(1, "NC-1", 1000),
            _row(2, "NC-1", 1200),
            _row(3, "B", 100),
            _row(4, "B", 200),
            _row(5, "L1-D1-S", 50, "1017", 10),
            _row(6, "L1-D2-S", 650, "1017", 1),
            _row(7, "L1-D3-S", 1300, "1017", 0.1),
            _row(8, "L1-D4-S", 700, "1017", 1),
        ]

        wells, audit, points = normalize_scan("scan-1", rows)

        self.assertEqual(audit["status"], "OK")
        self.assertEqual(audit["nc1_mean_intensity"], 1100)
        self.assertEqual(audit["blank_mean_intensity"], 150)
        expected = [0, 100 * 500 / 950, 100, 100 * 550 / 950]
        for well, expected_value in zip(wells, [value / 100 for value in expected]):
            self.assertAlmostEqual(well["viability_fraction"], expected_value)
        self.assertEqual(len(points), 3)

    def test_removes_failed_and_unassigned_drug_positions(self) -> None:
        rows = [
            _row(1, "NC-1", 1000),
            _row(2, "B", 100),
            _row(3, "FAIL", 900),
            _row(3, "L1-D1-S", 800, "1017", 10),
            _row(4, "L2-D1-S", 800, "NA", 10),
            _row(5, "L3-D1-S", 800, "1017", 10),
        ]

        wells, audit, _ = normalize_scan("scan-1", rows)

        self.assertEqual([well["position"] for well in wells], ["5"])
        self.assertEqual(audit["n_failed_positions"], 1)
        self.assertEqual(audit["n_missing_drug_positions"], 1)

    def test_excludes_combinations_and_abstains_without_controls(self) -> None:
        rows = [
            _row(1, "NC-1", 1000),
            _row(2, "B", 100),
            _row(3, "L1-D1-C", 500, "1017", 10),
        ]
        wells, audit, points = normalize_scan("scan-1", rows)
        self.assertEqual(wells, [])
        self.assertEqual(points, [])
        self.assertEqual(audit["status"], "OK")
        self.assertIn("excluded_non_single_agent_rows=1", audit["issues"])

        no_controls = [_row(1, "L1-D1-S", 500, "1017", 10)]
        wells, audit, points = normalize_scan("scan-1", no_controls)
        self.assertEqual((wells, points), ([], []))
        self.assertEqual(audit["status"], "EXCLUDED")
        self.assertIn("missing_NC-1_control", audit["issues"])
        self.assertIn("missing_B_blank", audit["issues"])

    def test_excludes_scan_with_invalid_control_dynamic_range(self) -> None:
        rows = [
            _row(1, "NC-1", 100),
            _row(2, "B", 200),
            _row(3, "L1-D1-S", 150, "1017", 10),
        ]

        wells, audit, points = normalize_scan("scan-1", rows)

        self.assertEqual((wells, points), ([], []))
        self.assertEqual(audit["status"], "EXCLUDED")
        self.assertIn("nonpositive_control_dynamic_range", audit["issues"])


class ExtractFileTests(unittest.TestCase):
    def test_extracts_only_configured_lines_and_writes_provenance(self) -> None:
        rows = [
            _row(1, "NC-1", 1000),
            _row(2, "B", 100),
            _row(3, "L1-D1-S", 500, "1017", 10),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / gdsc_extractor.RAW_FILENAME
            output = root / "out"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

            with patch.object(
                gdsc_extractor, "EXPECTED_SIZE_BYTES", source.stat().st_size
            ):
                manifest = gdsc_extractor.extract(source, output)

            self.assertEqual(manifest["source_rows_read"], 3)
            self.assertEqual(manifest["normalized_well_count"], 1)
            self.assertEqual(
                manifest["cell_line_coverage"]["CAPAN-1"]["single_agent_wells"], 1
            )
            with (output / "gdsc2_pdac_normalized_wells.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                extracted = list(csv.DictReader(handle))
            self.assertEqual(len(extracted), 1)
            self.assertEqual(float(extracted[0]["viability_fraction"]), 4 / 9)
            self.assertTrue((output / "gdsc2_pdac_raw_manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()

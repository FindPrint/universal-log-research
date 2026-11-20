<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Protocol clarification

The predeclared protocol says the 80-row slice was chosen to retain "two 40-row windows." That wording describes the slice length relative to the historical matched replay's 40-row setting; it does **not** mean this integration run used two fixed 40-row windows.

The production API kept automatic window optimization enabled. The live log shows an effective `w_size=16` for the reference run and `w_size=22` for the alternate-seed rerun. We preserve the original pre-run protocol unchanged and report the observed effective windows here. The 80-row choice remains an engineering bound for a software integration run, not a scientific sampling argument.

The full result reports `graine_alternative: null` even though the code chose seed `123` (`seed_alt = 123 if seed != 123 else 42`). `_l7b_extract_summary` omits the seed field, while the result formatter reads it. The numerical comparison completed and returned PASS, but the selected alternate seed is therefore not exported in that check object. This is a traceability defect in the tested v5.9.1 source, not a failed seed-stability calculation.

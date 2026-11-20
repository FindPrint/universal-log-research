"""Block-length sensitivity of UNIVERSAL_LOG T_log uncertainty on the Ising sweep."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parents[1]
FINITE_SIZE = PROJECT / "ising_classique_test" / "finite_size"
INTEGRATION = PROJECT / "ising_classique_test" / "results_tlog_uncertainty_verified"
PIPELINE = PROJECT / "UNIVERSAL_LOG_v5_3.py"

spec = importlib.util.spec_from_file_location("universal_log", PIPELINE)
ul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ul)


def main(n_bootstrap=500, seed=861109):
    data = json.loads((INTEGRATION / "master_results.json").read_text(encoding="utf-8"))
    landscape = pd.read_csv(INTEGRATION / "df_feat.csv")
    n_input = int(data["metadata"]["n_samples"])
    window = ul.resolve_tlog_window_size(data["run_pipeline"])
    if window is None:
        raise ValueError("The integration output does not contain an estimator window size.")
    default_block = int(np.ceil(window * len(landscape) / n_input))
    block_lengths = sorted(set(max(2, int(round(default_block * f)))
                               for f in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)))
    block_lengths = [b for b in block_lengths if b < len(landscape)]
    scales = data["metadata"].get("tlog_scales") or [{"kind": "row_count", "value": n_input}]
    state = data["holographic_tension_state"]
    records = []
    summaries = []
    profiles_by_block = {}

    for index, block_length in enumerate(block_lengths):
        uncertainty = ul.estimate_tlog_d_uncertainty(
            landscape, n_input_rows=n_input, window_size=window,
            n_bootstrap=n_bootstrap, seed=seed + index,
            block_length_positions=block_length,
        )
        if uncertainty.get("status") != "estimated":
            raise RuntimeError(f"Block {block_length}: {uncertainty.get('reason')}")
        profiles = ul.build_tlog_profiles(state, scales, d_uncertainty=uncertainty)
        profiles_by_block[str(block_length)] = profiles
        summaries.append({
            "block_length_positions": block_length,
            "method": uncertainty["method"],
            "n_bootstrap": uncertainty["n_bootstrap"],
            "anchors": uncertainty["anchors"],
            "estimators": uncertainty["estimators"],
        })
        for profile in profiles:
            for kind, entries in (("anchor", profile["anchor_readings"]),
                                  ("estimator", profile["estimator_readings"])):
                for name, entry in entries.items():
                    unc = entry.get("uncertainty") or {}
                    d_ci = unc.get("d_ci95") or [None, None]
                    t_ci = unc.get("T_log_ci95") or [None, None]
                    records.append({
                        "block_length_positions": block_length,
                        "profile_id": profile["profile_id"],
                        "n_kind": profile["n_scale"]["kind"],
                        "n_value": profile["n_scale"]["value"],
                        "reading_type": kind,
                        "name": name,
                        "d_point": entry.get("d"),
                        "d_bootstrap_median": unc.get("d_bootstrap_median"),
                        "d_se": unc.get("d_se"),
                        "d_ci95_low": d_ci[0],
                        "d_ci95_high": d_ci[1],
                        "T_log_point": entry.get("T_log"),
                        "T_log_bootstrap_median": unc.get("T_log_bootstrap_median"),
                        "T_log_se": unc.get("T_log_se"),
                        "T_log_ci95_low": t_ci[0],
                        "T_log_ci95_high": t_ci[1],
                        "n_valid": unc.get("n_valid"),
                        "uncertainty_method": unc.get("method"),
                    })
        print(f"Completed block length {block_length}/{default_block} positions", flush=True)

    result = {
        "method": "moving block bootstrap over ordered Progress positions",
        "data_source": str(INTEGRATION / "df_feat.csv"),
        "sizes_context": {"n_input_rows": n_input, "landscape_positions": int(len(landscape)),
                           "estimator_window_input_rows": int(window),
                           "mapped_default_block_positions": default_block},
        "block_lengths_tested": block_lengths,
        "n_bootstrap_per_block_length": int(n_bootstrap),
        "seed": int(seed),
        "scales": scales,
        "limitations": [
            "The intervals quantify variation across the ordered estimator landscape under the chosen moving-block design.",
            "They do not include uncertainty in n, estimator bias, data preprocessing, or the block-length choice itself.",
            "The chain-aware Binder comparison below is a separate physical observable; it is not a direct chain-level T_log uncertainty estimate.",
        ],
        "block_length_summaries": summaries,
    }
    chain_path = FINITE_SIZE / "chain_bootstrap_validation.json"
    if chain_path.exists():
        chain = json.loads(chain_path.read_text(encoding="utf-8"))
        hierarchical = chain["bootstrap_sensitivity"]["hierarchical_chain_block"]
        result["independent_chain_physics_context"] = {
            "source": str(chain_path),
            "chains_per_L_T": chain["protocol"]["chains"],
            "binder_crossing_48_64_Tc_ci95": hierarchical["binder_crossing_48_64_Tc"],
            "corrected_binder_fit_Tc_ci95": hierarchical["fits"]["corrected_Lminus2"]["Tc"],
            "corrected_binder_fit_nu_ci95": hierarchical["fits"]["corrected_Lminus2"]["nu"],
            "scope_note": "Independent-chain bootstrap validates Binder finite-size estimates; it is not a direct estimate of T_log chain-to-chain variance.",
        }

    json_path = FINITE_SIZE / "tlog_block_sensitivity.json"
    csv_path = FINITE_SIZE / "tlog_block_sensitivity.csv"
    png_path = FINITE_SIZE / "tlog_block_sensitivity.png"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(records).to_csv(csv_path, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    colors = {"saturation": "#377eb8", "criticality": "#4daf4a",
              "divergence": "#e41a1c", "null_reference": "#984ea3"}
    d_vector_keys = {"saturation": "d_sat", "criticality": "d_crit",
                     "divergence": "d_div", "null_reference": "d_null"}
    for ax, class_name in zip(axes.flat, d_vector_keys):
        points, lows, highs = [], [], []
        for block_length in block_lengths:
            estimate = next((x for x in summaries if x["block_length_positions"] == block_length), None)
            interval = (estimate or {}).get("anchors", {}).get(class_name, {})
            points.append(interval.get("median"))
            lows.append(interval.get("ci95_low"))
            highs.append(interval.get("ci95_high"))
        x = np.asarray(block_lengths, dtype=float)
        y = np.asarray(points, dtype=float)
        lo = np.asarray(lows, dtype=float)
        hi = np.asarray(highs, dtype=float)
        ax.errorbar(x, y, yerr=np.vstack([y - lo, hi - y]), fmt="o-",
                    color=colors[class_name], capsize=4)
        base = state.get("D_vector", {}).get(d_vector_keys[class_name])
        if base is not None:
            ax.axhline(float(base), color="black", linestyle="--", linewidth=1,
                       label="Point estimate")
            ax.legend(fontsize=8)
        ax.set_title(class_name.replace("_", " "))
        ax.set_xlabel("Block length (grid positions)")
        ax.set_ylabel(f"Dimension d ({class_name})")
        ax.grid(alpha=0.25)
    fig.suptitle("T_log uncertainty sensitivity to block length")
    fig.tight_layout(rect=[0.02, 0.02, 1, 0.96])
    fig.savefig(png_path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {json_path}, {csv_path}, and {png_path}")


if __name__ == "__main__":
    main()

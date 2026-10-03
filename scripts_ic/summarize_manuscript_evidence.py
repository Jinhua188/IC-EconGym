"""Read-only aggregation and plots for the submission-style manuscript."""
from pathlib import Path
import csv
import hashlib
import json
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark_results/manuscript_diagnostics"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def mean(records, field):
    return float(np.mean([float(r[field]) for r in records]))


def csv_out(name, rows):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    references = {}
    policy_stats = {}
    for task, folder in [("ic_r1", "r1_v2"), ("ic_g5", "g5_v2")]:
        rows = read(ROOT / "benchmark_results" / folder / "run_metrics.csv")
        references[task] = rows
        base = [r for r in rows if r["case"] == "base"]
        policy_stats[task] = {p: {k: mean([r for r in base if r["policy"] == p], k)
                                  for k in ["final_fill_rate", "cumulative_final_shortage", "cumulative_value_added",
                                            "private_spend", "fiscal_spend", "cumulative_welfare"]}
                              for p in sorted({r["policy"] for r in base})}
    ablations = read(OUT / "ablation_runs.csv")
    ablation_summary = []
    differences = []
    for (task, intervention, import_case, policy) in sorted({(r["task"], r["intervention"], r["import_case"], r["policy"]) for r in ablations}):
        selected = [r for r in ablations if (r["task"], r["intervention"], r["import_case"], r["policy"]) == (task, intervention, import_case, policy)]
        case = "base" if import_case == "proportional" else "import_" + import_case
        ref = {r["seed"]: r for r in references[task] if r["case"] == case and r["policy"] == policy}
        diffs = []
        for r in selected:
            reference = ref[r["seed"]]
            assert abs(float(r["shock_multiplier"]) - float(reference["shock_multiplier"])) < 1e-12
            assert abs(float(r["cumulative_final_demand"]) - float(reference["cumulative_final_demand"])) < 1e-4
            diff = float(r["final_fill_rate"]) - float(reference["final_fill_rate"])
            diffs.append(diff)
            differences.append({"task": task, "intervention": intervention, "import_case": import_case,
                                "policy": policy, "seed": r["seed"], "fill_rate_difference_vs_full": diff,
                                "shortage_difference_vs_full": float(r["cumulative_final_shortage"]) - float(reference["cumulative_final_shortage"]),
                                "private_spend_difference_vs_full": float(r["private_spend"]) - float(reference["private_spend"])})
        ablation_summary.append({"task": task, "intervention": intervention, "import_case": import_case,
                                 "policy": policy, "n": len(selected), "mean_fill_rate": mean(selected, "final_fill_rate"),
                                 "mean_difference_pp": float(np.mean(diffs) * 100),
                                 "min_difference_pp": float(min(diffs) * 100), "max_difference_pp": float(max(diffs) * 100),
                                 "mean_private_spend": mean(selected, "private_spend"), "mean_fiscal_spend": mean(selected, "fiscal_spend")})
    csv_out("ablation_paired_differences.csv", differences)
    csv_out("ablation_summary.csv", ablation_summary)

    e1 = read(OUT / "e1_absorption_runs.csv")
    e1_summary = []
    e1_diffs = []
    for condition, import_case in sorted({(r["condition"], r["import_case"]) for r in e1}):
        low = {r["seed"]: r for r in e1 if r["condition"] == condition and r["import_case"] == import_case and r["absorption"] == "0.2"}
        high = {r["seed"]: r for r in e1 if r["condition"] == condition and r["import_case"] == import_case and r["absorption"] == "0.9"}
        for seed in low:
            assert abs(float(low[seed]["cumulative_final_demand"]) - float(high[seed]["cumulative_final_demand"])) < 1e-4
            assert abs(float(low[seed]["cumulative_private_ai"]) - float(high[seed]["cumulative_private_ai"])) < 1e-4
            e1_diffs.append({"condition": condition, "import_case": import_case, "seed": seed,
                             "difference_pp": 100 * (float(high[seed]["final_fill_rate"]) - float(low[seed]["final_fill_rate"])),
                             "shortage_difference": float(high[seed]["cumulative_final_shortage"]) - float(low[seed]["cumulative_final_shortage"])})
        for absorption, records in [(0.2, list(low.values())), (0.9, list(high.values()))]:
            e1_summary.append({"condition": condition, "import_case": import_case, "absorption": absorption,
                               "n": len(records), **{k: mean(records, k) for k in ["final_fill_rate", "cumulative_final_shortage", "cumulative_private_ai", "terminal_ai_effective_mean"]}})
    csv_out("e1_summary.csv", e1_summary)
    csv_out("e1_paired_differences.csv", e1_diffs)

    # Audit all task arms: log changes do not by themselves establish mechanism validity.
    index = json.loads((ROOT / "demo_results_v2/run_index.json").read_text(encoding="utf-8"))
    task_summary = []
    for task in index["tasks"]:
        for arm in task["variants"]:
            trajectories = []
            for seed in index["seeds"]:
                traj = read(ROOT / "demo_results_v2/runs" / task["id"] / arm / f"seed_{seed}" / "trajectory.csv")
                trajectories.append(traj)
            task_summary.append({"task": task["id"], "arm": arm, "n_runs": len(trajectories),
                                 "mean_final_fill_rate": float(np.mean([sum(float(r["final_delivered"]) for r in s) / sum(float(r["final_demand"]) for r in s) for s in trajectories])),
                                 "mean_final_shortage": float(np.mean([sum(float(r["final_shortage"]) for r in s) for s in trajectories])),
                                 "terminal_hhi": float(np.mean([float(s[-1]["supplier_hhi"]) for s in trajectories])),
                                 "mean_cumulative_congestion": float(np.mean([float(s[-1]["congestion_cumulative"]) for s in trajectories])),
                                 "min_mean_health": min(float(r["edge_health_mean"]) for s in trajectories for r in s),
                                 "min_qualification": min(float(r["qualification_mean"]) for s in trajectories for r in s),
                                 "max_qualification": max(float(r["qualification_mean"]) for s in trajectories for r in s),
                                 "terminal_coordination": float(np.mean([float(s[-1]["coordination_rate"]) for s in trajectories]))})
    csv_out("task_arm_diagnostics.csv", task_summary)
    report = {"policy_baselines": policy_stats, "e1_summary": e1_summary, "ablations": ablation_summary,
              "edge_off_max_abs_fill_rate_difference": max(abs(r["fill_rate_difference_vs_full"]) for r in differences if r["intervention"] == "edge_off"),
              "qualification_log_range_all_15_tasks": [min(r["min_qualification"] for r in task_summary), max(r["max_qualification"] for r in task_summary)],
              "new_runs": 426, "old_paired_runs": 780, "existing_demo_runs": 150,
              "task_audit_note": "Three demo seeds may duplicate deterministic paths; they are not assumed to be independent statistical replicates."}
    (OUT / "evidence_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none",
                         "axes.spines.top": False, "axes.spines.right": False})
    figures = ROOT / "paper/figures"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1), layout="constrained")
    for ax, task, policies, title in [(axes[0], "ic_r1", ["demand_tracking", "buffered_smoothing"], "R1 vs. rule"),
                                     (axes[1], "ic_g5", ["linkage", "stress"], "G5 vs. uniform")]:
        refs = {r["seed"]: r for r in references[task] if r["case"] == "base" and r["policy"] == ("rule" if task == "ic_r1" else "uniform")}
        for i, p in enumerate(policies):
            vals = [100 * (float(r["final_fill_rate"]) - float(refs[r["seed"]]["final_fill_rate"])) for r in references[task] if r["case"] == "base" and r["policy"] == p]
            ax.scatter([i] * len(vals), vals, s=25, alpha=.65, color=["#c46f19", "#157a66"][i])
            ax.scatter(i, np.mean(vals), marker="_", s=400, linewidths=3, color=["#c46f19", "#157a66"][i])
        ax.axhline(0, color="#8797a6", lw=1)
        ax.set_xticks([0, 1], ["Demand tracking", "Buffered"] if task == "ic_r1" else ["Linkage", "Stress"])
        ax.set_ylabel("Paired fill-rate difference (percentage points)")
        ax.set_title(title)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
        ax.grid(axis="y", alpha=.15)
    for suffix in ["svg", "png"]:
        fig.savefig(figures / ("paired_policy_differences." + suffix), dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1), layout="constrained")
    for ax, task, policies in [(axes[0], "ic_r1", ["rule", "demand_tracking", "buffered_smoothing"]), (axes[1], "ic_g5", ["uniform", "linkage", "stress"])]:
        xpos = np.arange(3)
        for intervention, offset, color in [("full", -.23, "#2366b1"), ("edge_off", 0., "#157a66"), ("private_investment_off", .23, "#c46f19")]:
            values = []
            for p in policies:
                if intervention == "full":
                    values.append(100 * policy_stats[task][p]["final_fill_rate"])
                else:
                    values.append(100 * next(r["mean_fill_rate"] for r in ablation_summary if r["task"] == task and r["intervention"] == intervention and r["import_case"] == "proportional" and r["policy"] == p))
            ax.bar(xpos + offset, values, width=.23, label=intervention.replace("_", " "), color=color)
        ax.set_xticks(xpos, ["Rule", "Demand", "Buffered"] if task == "ic_r1" else ["Uniform", "Linkage", "Stress"])
        ax.set_ylim((94.5, 97.5) if task == "ic_r1" else (99.519, 99.522))
        ax.set_ylabel("Final-demand fill rate (%)")
        ax.set_title(task.replace("ic_", "").upper() + ": mechanism interventions")
        ax.grid(axis="y", alpha=.15)
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    for suffix in ["svg", "png"]:
        fig.savefig(figures / ("mechanism_ablations." + suffix), dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.9), layout="constrained")
    for i, case in enumerate(["proportional", "intermediate_first", "final_first"]):
        values = [r["difference_pp"] for r in e1_diffs if r["condition"] == "sector8_demand_shock" and r["import_case"] == case]
        ax.scatter([i] * len(values), values, color=["#2366b1", "#157a66", "#c46f19"][i], alpha=.7)
        ax.scatter(i, np.mean(values), marker="_", s=400, linewidths=3, color="#26374b")
    ax.axhline(0, color="#8797a6", lw=1)
    ax.set_xticks([0, 1, 2], ["Proportional", "Intermediate first", "Final first"])
    ax.set_ylabel("High vs. low absorption: fill-rate change (pp)")
    ax.set_title("E1: identical AI spending, sector-8 demand shock")
    ax.grid(axis="y", alpha=.15)
    for suffix in ["svg", "png"]:
        fig.savefig(figures / ("e1_constraint_activation." + suffix), dpi=180)
    plt.close(fig)
    print(json.dumps({"new_runs": 426, "paired_rows": len(differences), "edge_off_max_abs_difference": report["edge_off_max_abs_fill_rate_difference"],
                      "qualification_range": report["qualification_log_range_all_15_tasks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

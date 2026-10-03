"""Mechanism checks for the manuscript; unchanged settlement engine.

1. R1/G5: remove edge attenuation or private investment, matched to published
   baseline seeds, import cases and shock multipliers. Government capacity
   spending remains active when private investment is disabled.
2. E1: compare absorption 0.2/0.9 at the same AI spending, under baseline demand
   or a temporary sector-8 final-demand increase. Baseline cases are deterministic
   and run once, rather than treating duplicate seeds as independent evidence.

These are conditional interventions, not historical validation or learned policies.
"""
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
from ic_extension.entrypoint import load_task
from ic_extension.iewm13 import make

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark_results/manuscript_diagnostics"
SEEDS = list(range(42, 52))
IMPORTS = ("proportional", "intermediate_first", "final_first")
POLICIES = {"ic_r1": ("rule", "demand_tracking", "buffered_smoothing"),
            "ic_g5": ("uniform", "linkage", "stress")}


def dump_csv(name, records):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def rollout(cfg, sector="rule", government="configured"):
    world = make(cfg, sector_policy=sector, government_policy=government)
    for _ in range(30):
        world.step(world.run_agents())
    result = world.evaluate()
    result["cumulative_private_ai"] = sum(r["private_ai"] for r in world.trajectory)
    result["peak_output"] = max(r["output"] for r in world.trajectory)
    result["output_range"] = max(r["output"] for r in world.trajectory) - min(r["output"] for r in world.trajectory)
    result["peak_mean_effective_ai"] = max(r["ai_effective_mean"] for r in world.trajectory)
    result["config_sha256"] = hashlib.sha256(json.dumps(cfg, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    configs = []
    for task, policies in POLICIES.items():
        base = load_task(task)
        base.pop("variants", None)
        if task == "ic_g5":
            base["policy"]["spend_fraction"] = .25
        for intervention in ("edge_off", "private_investment_off"):
            for import_case in IMPORTS:
                for seed in SEEDS:
                    cfg = deepcopy(base)
                    cfg["import_case"] = import_case
                    cfg["seed"] = seed
                    module = "edge" if intervention == "edge_off" else "investment"
                    cfg["modules"] = [m for m in cfg["modules"] if m != module]
                    multiplier = max(0., 1 + .04 * float(np.random.default_rng(seed + 15011).normal()))
                    shock = cfg["demand_shock"] if task == "ic_r1" else cfg["shock"]
                    key = "increase" if task == "ic_r1" else "capacity_loss"
                    shock[key] = min(1., shock[key] * multiplier)
                    configs.append({"task": task, "intervention": intervention,
                                    "import_case": import_case, "seed": seed, "configuration": cfg})
                    for policy in policies:
                        result = rollout(cfg, sector=policy if task == "ic_r1" else "rule",
                                         government=policy if task == "ic_g5" else "configured")
                        records.append({"task": task, "intervention": intervention, "import_case": import_case,
                                        "seed": seed, "policy": policy, "shock_multiplier": multiplier, **result})
            print(task, intervention, "completed", flush=True)
    dump_csv("ablation_runs.csv", records)
    e1 = []
    base = load_task("ic_e1")
    base.pop("variants", None)
    for condition in ("baseline_demand", "sector8_demand_shock"):
        for import_case in IMPORTS:
            for seed in ([42] if condition == "baseline_demand" else SEEDS):
                for absorption in (.2, .9):
                    cfg = deepcopy(base)
                    cfg["import_case"] = import_case
                    cfg["seed"] = seed
                    cfg["absorption"] = [absorption] * 13
                    cfg["ai_rate"] = .02
                    cfg["demand_sector"] = 8
                    multiplier = max(0., 1 + .04 * float(np.random.default_rng(seed + 15011).normal()))
                    if condition == "sector8_demand_shock":
                        cfg["demand_shock"] = {"start": 10, "end": 20, "increase": .3 * multiplier}
                    else:
                        cfg.pop("demand_shock", None)
                    configs.append({"task": "ic_e1", "condition": condition, "import_case": import_case,
                                    "seed": seed, "absorption": absorption, "configuration": cfg})
                    e1.append({"task": "ic_e1", "condition": condition, "import_case": import_case,
                               "seed": seed, "absorption": absorption,
                               "shock_multiplier": multiplier if condition != "baseline_demand" else 1.,
                               **rollout(cfg)})
    dump_csv("e1_absorption_runs.csv", e1)
    metadata = {"version": "manuscript-diagnostics-1", "seeds": SEEDS, "imports": IMPORTS,
                "periods": 30, "new_ablation_runs": len(records), "new_e1_runs": len(e1),
                "existing_reference": {"R1": "../r1_v2/run_metrics.csv", "G5": "../g5_v2/run_metrics.csv"},
                "baseline_case_mapping": {"proportional": "base", "intermediate_first": "import_intermediate_first", "final_first": "import_final_first"},
                "engine_changes": False, "independent_external_validation": False,
                "interventions": {"edge_off": "remove edge pressure/health update; qualification and coordination remain",
                                  "private_investment_off": "disable private capex and its lagged projects; government capacity spending remains"},
                "e1": "normal demand has no random mechanism: one run per import/absorption. Shock condition uses matched seed-indexed scenario dispersion.",
                "python": platform.python_version(), "numpy": np.__version__, "configurations": configs}
    (OUT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ablation_runs": len(records), "e1_runs": len(e1)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

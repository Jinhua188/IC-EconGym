"""Paired strategy and one-factor sensitivity study for the 13-sector IEWM API.

Usage from IC_EconGym_Integrated:
  python -m scripts_ic.run_strategy_benchmark --task ic_r1 --dimension sector --ofat
  python -m scripts_ic.run_strategy_benchmark --task ic_g5 --dimension government --ofat

All results are conditional simulations. This command does not train RL or LLM
policies and does not constitute validation against independent observations.
"""
from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
import hashlib
from pathlib import Path

import numpy as np

from ic_extension.entrypoint import load_task
from ic_extension.iewm13 import make


POLICIES = {
    "sector": ("rule", "demand_tracking", "buffered_smoothing"),
    "government": ("uniform", "linkage", "stress"),
}
DEFAULT_OFAT = {
    "ic_r1": ("backlog_retention", "external_supply_elasticity",
              "capital_efficiency", "capacity_lag", "demand_shock.increase"),
    "ic_g5": ("backlog_retention", "external_supply_elasticity",
              "shock.capacity_loss", "budget_share", "edge_health_floor"),
}
FALLBACK = {
    "capital_efficiency": 0.1,
    "edge_health_floor": 0.85,
}


def get_nested(mapping: dict, path: str):
    value = mapping
    for key in path.split("."):
        value = value[key]
    return value


def set_nested(mapping: dict, path: str, value):
    cursor = mapping
    keys = path.split(".")
    for key in keys[:-1]:
        cursor = cursor[key]
    cursor[keys[-1]] = value


def cases(base: dict, ofat: bool):
    yield "base", deepcopy(base), {"kind": "baseline"}
    for name in ("intermediate_first", "final_first"):
        cfg = deepcopy(base)
        cfg["import_case"] = name
        yield f"import_{name}", cfg, {"kind": "import_allocation", "import_case": name}
    if not ofat:
        return
    for parameter in DEFAULT_OFAT.get(base["task_id"], ()):
        try:
            original = get_nested(base, parameter)
        except KeyError:
            original = FALLBACK[parameter]
        for label, multiplier in (("minus20", 0.8), ("plus20", 1.2)):
            cfg = deepcopy(base)
            value = original * multiplier
            if isinstance(original, int) and not isinstance(original, bool):
                value = max(1, round(value))
            if parameter == "edge_health_floor":
                value = min(1.0, value)
            set_nested(cfg, parameter, value)
            yield f"{parameter.replace('.', '_')}_{label}", cfg, {
                "kind": "ofat", "parameter": parameter, "original": original,
                "value": value, "multiplier": multiplier,
            }


def run_one(cfg: dict, policy: str, dimension: str, seed: int, periods: int):
    local = deepcopy(cfg)
    local["seed"] = seed
    world = make(local,
                 sector_policy=policy if dimension == "sector" else "rule",
                 government_policy=policy if dimension == "government" else "configured")
    for _ in range(periods):
        world.step(world.run_agents())
    return world.evaluate()


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=("ic_r1", "ic_g5"), required=True)
    parser.add_argument("--dimension", choices=tuple(POLICIES), required=True)
    parser.add_argument("--seeds", default="42,43,44,45,46,47,48,49,50,51")
    parser.add_argument("--periods", type=int, default=30)
    parser.add_argument("--ofat", action="store_true")
    parser.add_argument("--spend-fraction", type=float, default=0.25)
    parser.add_argument("--shock-noise-sd", type=float, default=0.04,
                        help="Relative standard deviation of a seed-indexed shock multiplier")
    parser.add_argument("--out", type=Path, default=Path("benchmark_results"))
    args = parser.parse_args(argv)
    if (args.task == "ic_r1") != (args.dimension == "sector"):
        parser.error("ic_r1 compares sector policies; ic_g5 compares government policies")
    if not 0 < args.spend_fraction <= 1:
        parser.error("spend fraction must be in (0, 1]")
    if not 0 <= args.shock_noise_sd <= 0.5:
        parser.error("shock-noise-sd must be between 0 and 0.5")
    seeds = [int(s) for s in args.seeds.split(",")]
    if len(seeds) != len(set(seeds)) or not seeds or args.periods < 1:
        parser.error("use unique seeds and a positive period count")
    cfg = load_task(args.task)
    cfg.pop("variants", None)
    if args.dimension == "government":
        cfg["policy"]["spend_fraction"] = args.spend_fraction
    args.out.mkdir(parents=True, exist_ok=True)
    rows, differences, case_meta = [], [], {}
    metrics = ("cumulative_value_added", "cumulative_shortage", "cumulative_welfare",
               "cumulative_final_shortage", "cumulative_final_delivered", "final_fill_rate",
               "mean_service_rate", "terminal_output", "fiscal_spend", "private_spend",
               "terminal_ai_effective_mean", "terminal_technology_mean",
               "terminal_edge_health_mean")
    for case_name, case_cfg, description in cases(cfg, args.ofat):
        case_meta[case_name] = description
        for seed in seeds:
            seed_cfg = deepcopy(case_cfg)
            shock_multiplier = max(0.0, 1.0 + args.shock_noise_sd *
                                   float(np.random.default_rng(seed + 15011).normal()))
            shock_path = "demand_shock.increase" if args.dimension == "sector" else "shock.capacity_loss"
            set_nested(seed_cfg, shock_path,
                       min(1.0, get_nested(seed_cfg, shock_path) * shock_multiplier))
            by_policy = {}
            for policy in POLICIES[args.dimension]:
                result = run_one(seed_cfg, policy, args.dimension, seed, args.periods)
                by_policy[policy] = result
                rows.append({"task": args.task, "case": case_name, "seed": seed,
                             "policy": policy, "shock_multiplier": shock_multiplier, **result})
            reference = by_policy[POLICIES[args.dimension][0]]
            for policy in POLICIES[args.dimension][1:]:
                for metric in metrics:
                    differences.append({"task": args.task, "case": case_name,
                                        "seed": seed, "policy": policy,
                                        "reference": POLICIES[args.dimension][0],
                                        "metric": metric,
                                        "paired_difference": by_policy[policy][metric] - reference[metric]})
    write_csv(args.out / "run_metrics.csv", rows)
    write_csv(args.out / "paired_differences.csv", differences)
    summaries = []
    for case_name in case_meta:
        for policy in POLICIES[args.dimension][1:]:
            for metric in metrics:
                values = [r["paired_difference"] for r in differences
                          if r["case"] == case_name and r["policy"] == policy and r["metric"] == metric]
                summaries.append({"case": case_name, "policy": policy,
                                  "reference": POLICIES[args.dimension][0], "metric": metric,
                                  "n_seeds": len(values), "mean_paired_difference": float(np.mean(values)),
                                  "min_paired_difference": float(np.min(values)),
                                  "max_paired_difference": float(np.max(values))})
    write_csv(args.out / "paired_summary.csv", summaries)
    metadata = {
        "task": args.task, "dimension": args.dimension, "policies": POLICIES[args.dimension],
        "seeds": seeds, "periods": args.periods, "cases": case_meta,
        "government_spend_fraction": args.spend_fraction if args.dimension == "government" else None,
        "common_exogenous_scenarios": True,
        "shock_noise_sd": args.shock_noise_sd,
        "shock_noise_applied_to": "demand_shock.increase" if args.dimension == "sector" else "shock.capacity_loss",
        "shock_noise_type": "seed-indexed scenario dispersion, not an empirical error distribution",
        "independent_external_validation": False,
        "metric_version": "v2-external-final-demand",
        "base_configuration": cfg,
        "base_configuration_sha256": hashlib.sha256(json.dumps(cfg, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "interpretation": "Matched-seed conditional mechanism simulations; no RL/LLM training, empirical policy effects, or firm IO allocation.",
    }
    (args.out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"runs": len(rows), "cases": len(case_meta), "output": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

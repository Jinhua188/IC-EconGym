"""CLI used by EconGym's --problem_scene ic_* dispatch."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
import yaml

from .model import ICEnvironment, RuleGovernmentPolicy, RuleSectorPolicy


def load_task(task_id: str, config_dir: Path | None = None) -> dict:
    config_dir = config_dir or Path(__file__).resolve().parent.parent / "cfg_ic"
    path = config_dir / f"{task_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Unknown IC scenario: {path}")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    if cfg.get("task_id") != task_id:
        raise ValueError(f"task_id mismatch in {path}")
    if not isinstance(cfg.get("modules"), list):
        raise ValueError("modules must be a list")
    return cfg


def _merge(base: dict, updates: dict) -> dict:
    result = dict(base)
    for key, value in updates.items():
        if key != "channels" and isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def run_task(task_id: str, periods: int | None = None, out_dir: Path | None = None,
             config_dir: Path | None = None, import_case: str | None = None,
             variant: str = "treatment", seed: int | None = None) -> dict:
    cfg = load_task(task_id, config_dir)
    variants = cfg.pop("variants", {})
    if variant != "treatment":
        if variant not in variants:
            raise ValueError(f"Unknown variant {variant}; available: {list(variants)}")
        cfg = _merge(cfg, variants[variant])
    if import_case:
        cfg["import_case"] = import_case
    if seed is not None:
        cfg["seed"] = int(seed)
    periods = int(periods or cfg.get("periods", 30))
    if periods < 1:
        raise ValueError("periods must be positive")
    env = ICEnvironment(cfg)
    sector_policy = RuleSectorPolicy(cfg)
    gov_policy = RuleGovernmentPolicy(cfg)
    out_dir = out_dir or Path("results_ic") / task_id / variant
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    node_rows = []
    for _ in range(periods):
        obs = env.observations()
        sector_policy.begin_period()
        gov_action = gov_policy.act(obs["government"])
        actions = [sector_policy.act(o) for o in obs["sectors"]]
        _, _, _, row = env.step(actions, gov_action)
        rows.append(row)
        for i, agent in enumerate(env.agents):
            node_rows.append({"period": row["period"], "sector_id": i + 1,
                              "label": agent.label, "output": float(env.output[i]),
                              "base_output": float(env.q0[i]), "value_added": float(env.value_added[i]),
                              "capacity": float(env.capacity[i]), "price": float(env.price[i]),
                              "backlog": float(env.backlog[i]), "ai": float(env.ai[i]),
                              "ai_effective": float(env.ai_effective[i]), "technology": float(env.tech[i])})
    for name, data in (("trajectory.csv", rows), ("node_panel.csv", node_rows)):
        with (out_dir / name).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    result = {"task_id": task_id, "variant": variant, "periods": periods, "seed": env.seed,
              "import_case": cfg.get("import_case", "proportional"),
              "source_year": 2020, "unit": "万元，固定价格，每季度",
              "evidence_level": "IO-constrained mechanism simulation; behavior parameters are scenarios",
              "sector_agents": 13, "government_agents": 1,
              "modules": cfg["modules"], "last_period": rows[-1],
              "verified_upstream_commit": "f0ccbb89869c96ea7058e9539a38c6a637402603"}
    (out_dir / "run_metadata.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="IC-EconGym 13-sector extension")
    parser.add_argument("--problem_scene", default="ic_e1")
    parser.add_argument("--ic_periods", type=int)
    parser.add_argument("--ic_out", type=Path)
    parser.add_argument("--ic_import_case", choices=["proportional", "intermediate_first", "final_first"])
    parser.add_argument("--ic_variant", default="treatment")
    parser.add_argument("--ic_seed", type=int)
    parser.add_argument("--ic_compare", action="store_true")
    args = parser.parse_args(argv)
    if args.ic_compare:
        config = load_task(args.problem_scene)
        names = ["treatment"] + list(config.get("variants", {}))
        results = [run_task(args.problem_scene, args.ic_periods,
                            (args.ic_out / name) if args.ic_out else None,
                            import_case=args.ic_import_case, variant=name, seed=args.ic_seed) for name in names]
        result = {"task_id": args.problem_scene, "variants": {x["variant"]: x["last_period"] for x in results}}
    else:
        result = run_task(args.problem_scene, args.ic_periods, args.ic_out,
                          import_case=args.ic_import_case, variant=args.ic_variant,
                          seed=args.ic_seed)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

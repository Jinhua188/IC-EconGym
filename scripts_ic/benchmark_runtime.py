"""Measure fixed-13-sector rollout cost across the 15 existing task configs."""
from __future__ import annotations

import argparse
import csv
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import psutil

from ic_extension.entrypoint import load_task
from ic_extension.iewm13 import make


TASKS = tuple(f"ic_{group}{i}" for group in "erg" for i in range(1, 6))


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="42,43,44")
    parser.add_argument("--periods", type=int, default=30)
    parser.add_argument("--out", type=Path, default=Path("benchmark_results/runtime_15tasks"))
    args = parser.parse_args(argv)
    seeds = [int(v) for v in args.seeds.split(",")]
    if not seeds or len(set(seeds)) != len(seeds) or args.periods <= 0:
        parser.error("seeds must be unique and periods positive")
    process = psutil.Process()
    rows = []
    for task in TASKS:
        cfg = load_task(task)
        cfg.pop("variants", None)
        for seed in seeds:
            start = perf_counter()
            world = make(cfg)
            world.reset(seed)
            initialized = perf_counter()
            peak_rss = process.memory_info().rss
            for _ in range(args.periods):
                world.step(world.run_agents())
                peak_rss = max(peak_rss, process.memory_info().rss)
            finished = perf_counter()
            rows.append({"task": task, "seed": seed, "periods": args.periods,
                         "sector_agents": 13, "government_agents": 1,
                         "initialize_seconds": initialized - start,
                         "rollout_seconds": finished - initialized,
                         "seconds_per_step": (finished - initialized) / args.periods,
                         "peak_process_rss_bytes": peak_rss})
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "runtime_runs.csv", rows)
    summary = []
    for task in TASKS:
        selected = [r for r in rows if r["task"] == task]
        summary.append({"task": task, "n_runs": len(selected),
                        "median_ms_per_step": float(np.median([r["seconds_per_step"] for r in selected]) * 1000),
                        "min_ms_per_step": float(np.min([r["seconds_per_step"] for r in selected]) * 1000),
                        "max_ms_per_step": float(np.max([r["seconds_per_step"] for r in selected]) * 1000),
                        "peak_process_rss_mb": max(r["peak_process_rss_bytes"] for r in selected) / 1048576})
    write_csv(args.out / "runtime_summary.csv", summary)
    meta = {"python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor(), "numpy": np.__version__,
            "seeds": seeds, "periods": args.periods, "tasks": TASKS,
            "timing_scope": "single-process environment rollout, excluding world construction; includes policy calls and RSS sampling",
            "memory_scope": "peak whole-process resident set during each run, sampled once per step; not incremental world memory",
            "agent_scaling_test": False}
    (args.out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"runs": len(rows), "median_task_ms_range": [
        min(r["median_ms_per_step"] for r in summary),
        max(r["median_ms_per_step"] for r in summary)]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Run all 15 IC tasks and their paired demonstration arms."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from collections import defaultdict

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ic_extension.entrypoint import load_task, run_task  # noqa: E402
from scripts_ic.build_dashboard import build_dashboard  # noqa: E402

TASKS = ["ic_" + x for x in ("e1", "e2", "e3", "e4", "e5",
                             "r1", "r2", "r3", "r4", "r5",
                             "g1", "g2", "g3", "g4", "g5")]


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(file)]


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_all(out_dir: Path, periods: int, seeds: list[int], arms: str,
            import_case: str | None, modules: str = "all") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = TASKS
    if modules != "all":
        selected = [t for t in TASKS if t[3] == {"empowerment": "e", "risk": "r", "governance": "g"}[modules]]
    index = {"format": "ic-econgym-demo-v2", "periods": periods, "seeds": seeds,
             "import_case": import_case or "per-task", "tasks": []}
    run_summary = []
    arm_summary = []
    for task_id in selected:
        cfg = load_task(task_id)
        if arms == "treatment":
            names = ["treatment"]
        elif arms == "v1":
            registry_names = cfg.get("v1_arm_names", [])
            names = registry_names or ["treatment"]
        else:
            names = ["treatment"] + list(cfg.get("variants", {}))
        names = list(dict.fromkeys(names))
        task = {"id": task_id, "name": cfg["name"], "question": cfg["research_question"],
                "theory": cfg.get("theory", ""), "source_v1_task_id": cfg.get("source_v1_task_id", ""),
                "variants": [], "series": {}}
        for name in names:
            runs = []
            for seed in seeds:
                target = out_dir / "runs" / task_id / name / f"seed_{seed}"
                result = run_task(task_id, periods=periods, out_dir=target,
                                  import_case=import_case, variant=name, seed=seed)
                trajectory = read_rows(target / "trajectory.csv")
                base = float(trajectory[0]["base_output"])
                summary = {"task_id": task_id, "variant": name, "seed": seed,
                           "final_output": trajectory[-1]["output"],
                           "final_value_added": trajectory[-1]["value_added"],
                           "final_shortage": trajectory[-1]["shortage"],
                           "final_service_rate": trajectory[-1]["service_rate"],
                           "final_price_index": trajectory[-1]["price_index"],
                           "final_supplier_hhi": trajectory[-1]["supplier_hhi"],
                           "fiscal_cost": trajectory[-1]["fiscal_cost_cumulative"],
                           "cumulative_output_loss": float(sum(max(base - r["output"], 0) for r in trajectory)),
                           "peak_shortage": float(max(r["shortage"] for r in trajectory)),
                           "output_path": str(target.relative_to(out_dir))}
                run_summary.append(summary)
                runs.append(trajectory)
                if result["last_period"]["period"] != periods - 1:
                    raise AssertionError(f"Incomplete task {task_id}/{name}/seed {seed}")
            fields = [k for k in runs[0][0] if k != "period"]
            means = []
            for t in range(periods):
                row = {"period": t}
                for key in fields:
                    row[key] = float(np.mean([run[t][key] for run in runs]))
                means.append(row)
            task["variants"].append(name)
            task["series"][name] = means
            matching = [r for r in run_summary if r["task_id"] == task_id and r["variant"] == name]
            agg = {"task_id": task_id, "variant": name, "n_seeds": len(seeds)}
            for key in ("final_output", "final_value_added", "final_shortage", "final_service_rate",
                        "final_price_index", "final_supplier_hhi", "fiscal_cost",
                        "cumulative_output_loss", "peak_shortage"):
                values = np.asarray([r[key] for r in matching])
                agg[key + "_mean"] = float(values.mean())
                agg[key + "_sd"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            arm_summary.append(agg)
        index["tasks"].append(task)
        print(f"{task_id}: {len(names)} arms × {len(seeds)} seeds × {periods} periods")
    write_csv(out_dir / "run_summary.csv", run_summary)
    write_csv(out_dir / "arm_summary.csv", arm_summary)
    (out_dir / "run_index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    build_dashboard(index, out_dir / "dashboard.html")
    report = {"tasks": len(index["tasks"]), "runs": len(run_summary), "periods": periods,
              "seeds": seeds, "arms": arms, "dashboard": "dashboard.html",
              "interpretation": "Demonstration results from conditional mechanisms, not empirical policy effects"}
    (out_dir / "demo_metadata.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "demo_results")
    parser.add_argument("--periods", type=int, default=30)
    parser.add_argument("--seeds", default="1")
    parser.add_argument("--arms", choices=["all", "v1", "treatment"], default="v1")
    parser.add_argument("--module", choices=["all", "empowerment", "risk", "governance"], default="all")
    parser.add_argument("--import-case", choices=["proportional", "intermediate_first", "final_first"])
    args = parser.parse_args()
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    if not seeds or args.periods < 1:
        raise ValueError("seeds and periods must be nonempty positive values")
    report = run_all(args.out, args.periods, seeds, args.arms, args.import_case, args.module)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

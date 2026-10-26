"""Audit the 15-sector run inventory and its source identities."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = WORKSPACE / "outputs/io_15_2018_2020_2023"
    input_audit = json.loads((source / "dynamic_input_audit.json").read_text(encoding="utf-8"))
    assert len(input_audit["results"]) == 9
    for record in input_audit["results"]:
        path = source / f"io_use_15_{record['year']}_{record['case']}.npz"
        assert sha(path) == record["sha256"]
        assert max(record["checks_max_abs_wanyuan"].values()) < 1e-3
        with np.load(path) as dat:
            assert dat["z_domestic"].shape == (57, 57)
            assert dat["y_domestic"].shape == (57, 4)
    assert len(list((ROOT / "cfg_ic15").glob("ic_*.yaml"))) == 15

    expected = {
        "benchmark_results/p0_v4/arm_metrics.csv": 870,
        "benchmark_results/r1_v4/run_metrics.csv": 390,
        "benchmark_results/g5_v4/run_metrics.csv": 390,
        "benchmark_results/manuscript_diagnostics_v4/ablation_runs.csv": 360,
        "benchmark_results/manuscript_diagnostics_v4/e1_absorption_runs.csv": 66,
        "benchmark_results/p1_v4/run_metrics.csv": 6000,
        "robustness_v4/run_metrics.csv": 23400,
        "robustness_v4/mechanism_grid.csv": 600,
        "benchmark_results/runtime_15tasks_v4/runtime_runs.csv": 45,
        "benchmark_results/p4_v4/step_timings.csv": 10,
    }
    for name, count in expected.items():
        table = rows(ROOT / name)
        assert len(table) == count, (name, len(table), count)
        if "final_fill_rate" in table[0]:
            fill = np.array([float(r["final_fill_rate"]) for r in table])
            assert np.all(np.isfinite(fill)) and np.all((fill >= -1e-10) & (fill <= 1 + 1e-10)), name

    locked = json.loads((ROOT / "benchmark_splits_v4/locked_scenarios_v4.json").read_text(encoding="utf-8"))
    assert all(len(locked[task][split]) == 100 for task in ("ic_r1", "ic_g5")
               for split in ("test_id", "test_ood"))
    training = []
    for task in ("ic_r1", "ic_g5"):
        for seed in range(101, 111):
            folder = ROOT / "learning/results_v4" / task / f"seed_{seed}"
            meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
            assert meta["environment_steps"] == 12000
            assert sha(folder / "best.pt") == meta["checkpoint_sha256"]
            assert sha(ROOT / "learning/ppo_v4.py") == meta["ppo_source_sha256"]
            training.append(meta)
    assert len(training) == 20
    source_hashes = {
        "model_v4.py": sha(ROOT / "ic_extension/model_v4.py"),
        "upgrade_common_v4.py": sha(ROOT / "scripts_ic/upgrade_common_v4.py"),
    }
    for path in (ROOT / "benchmark_results/p0_v4/checks.json",
                 ROOT / "benchmark_results/p1_v4/metadata.json",
                 ROOT / "robustness_v4/metadata.json",
                 ROOT / "benchmark_results/p4_v4/metadata.json"):
        meta = json.loads(path.read_text(encoding="utf-8"))
        assert meta["engine_version"] == "v0.4-ic15-experimental"
        for name, digest in source_hashes.items():
            assert any(key.endswith(name) and value == digest for key, value in meta["hashes"].items()), path

    paper = (ROOT / "paper/manuscript_zh.md").read_text(encoding="utf-8")
    assert "55.8639" in paper and "98.9009" in paper
    assert all(term not in paper for term in ("206个企业", "8,364", "53.21%", "98.77%"))
    for image in ("architecture.png", "v4_algorithm_generalization.png", "v4_learning_curves.png",
                  "v4_joint_robustness.png", "v3_external_capacity.png"):
        assert (ROOT / "paper/figures" / image).exists()
    print(json.dumps({"status": "PASS", "input_cases": 9, "tasks": 15,
                      "training_instances": 20, "run_counts": expected}, ensure_ascii=False))


if __name__ == "__main__":
    main()

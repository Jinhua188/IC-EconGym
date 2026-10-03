"""Fast data, baseline, configuration, and integration checks."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import numpy as np

from ic_extension.entrypoint import load_task, run_task
from ic_extension.model import ICEnvironment, GovernmentAction, SectorAction


def validate():
    cfg_dir = Path(__file__).resolve().parent / "cfg_ic"
    task_ids = ["ic_" + x for x in ("e1", "e2", "e3", "e4", "e5",
                                      "r1", "r2", "r3", "r4", "r5",
                                      "g1", "g2", "g3", "g4", "g5")]
    assert len(list(cfg_dir.glob("ic_*.yaml"))) == 15
    for mode in ("proportional", "intermediate_first", "final_first"):
        cfg = {"import_case": mode, "modules": [], "budget_share": 0.0}
        env = ICEnvironment(cfg)
        for _ in range(6):
            actions = [SectorAction(production_plan=float(x)) for x in env.q0]
            _, _, _, record = env.step(actions, GovernmentAction.zeros())
            assert np.allclose(env.output, env.q0, rtol=1e-9, atol=1e-2), (mode, record)
            assert record["shortage"] < 1.0, (mode, record)
            assert abs(record["final_demand"] - record["final_delivered"] - record["final_shortage"]) < 0.1
            assert 0 <= record["final_fill_rate"] <= 1.0 + 1e-12
            assert record["internal_delivered"] <= record["internal_orders"] + 0.1
    with tempfile.TemporaryDirectory() as tmp:
        arm_count = 0
        for task_id in task_ids:
            cfg = load_task(task_id)
            assert cfg["task_id"] == task_id
            result = run_task(task_id, periods=8, out_dir=Path(tmp) / task_id)
            assert result["sector_agents"] == 13
            assert np.isfinite(result["last_period"]["output"])
            assert result["last_period"]["output"] >= 0
            assert (Path(tmp) / task_id / "node_panel.csv").exists()
            if task_id.startswith("ic_g"):
                total = ICEnvironment(cfg).budget_remaining
                assert result["last_period"]["fiscal_cost_cumulative"] <= total + 1e-5
            for arm in cfg.get("v1_arm_names", []):
                assert arm in cfg["variants"], (task_id, arm)
                sample = run_task(task_id, periods=6, out_dir=Path(tmp) / task_id / arm,
                                  variant=arm)
                assert np.isfinite(sample["last_period"]["output"])
                arm_count += 1
        assert len(task_ids) == 15
    print(json.dumps({"status": "pass", "tasks": len(task_ids),
                      "v1_arms": arm_count, "baseline_import_cases": 3,
                      "baseline_periods": 6}, ensure_ascii=False))


if __name__ == "__main__":
    validate()

# IC-EconGym

**An Input–Output-Constrained Multi-Agent Testbed for Semiconductor Industrial Policy and Supply-Chain Resilience**

[中文说明](README_zh.md) · [Chinese manuscript](paper/manuscript_zh.md) · [Mechanisms](MECHANISMS.md) · [Data card](DATA_CARD.md) · [Task specifications](TASKS.md) · [Reproduction](REPRODUCIBILITY.md)

IC-EconGym is a Python environment with **13 industrial sector agents and one government agent**, **15 configured tasks**, and **three accounting-consistent import allocation assumptions**. Orders, source-specific materials, capacity, allocation and fiscal spending are settled under a common input–output boundary.

Current evidence covers accounting checks, heuristic paired-policy experiments and fixed-size rollout timing. Dynamic behavior parameters are scenarios; independent external validation and RL/LLM baselines remain outstanding. The project is a research testbed, with conditional simulation results.

## Quick start

```bash
python -m pip install -r requirements_ic.txt
python validate_extension.py
python -m ic_extension.entrypoint --problem_scene ic_e1 --ic_periods 30
python -m scripts_ic.run_all_tasks --out demo_results_v2 --seeds 1,2,3 --arms v1
python -m http.server 8000
```

Open `http://localhost:8000/docs/` for the project page, `docs/demo.html` for task replay, or `docs/observer.html` for recorded sector states. These are static replay interfaces; changing their selectors does not run a new simulation.

## Architecture

![Architecture](paper/figures/architecture.png)

The 2020 accounting table was split from 42 to 55 sectors using revenue shares. Thirteen related sectors are decision agents; the other 42 domestic sectors, imports and final demand remain explicit boundaries. Monetary flows use fixed-base ten-thousand CNY units, with annual baseline flows divided into four equal quarters.

## Repository map

| Directory | Contents |
|---|---|
| `ic_extension/` | Environment, role constraints, policies and World13 adapter |
| `cfg_ic/` | E1–E5 empowerment, R1–R5 risk, G1–G5 governance |
| `scripts_ic/` | Task runner, paired benchmarks, runtime and external-baseline interface |
| `benchmark_results/` | 780 paired trajectories summarized at run level; 45 timing runs |
| `demo_results_v2/` | 150 replay runs across 50 comparison arms |
| `paper/` | Chinese manuscript, figures and computed result summary |
| `docs/` | GitHub Pages project page, task demo, observer and paper |

## Reproducible policy comparison

```bash
python -m scripts_ic.run_strategy_benchmark --task ic_r1 --dimension sector --ofat --out benchmark_results/r1_v2
python -m scripts_ic.run_strategy_benchmark --task ic_g5 --dimension government --ofat --out benchmark_results/g5_v2
python -m scripts_ic.benchmark_runtime --out benchmark_results/runtime_v2
```

Matched seeds share exogenous shocks. Final-demand fill rate is logged independently of policy-generated internal orders. See the manuscript for metric interpretation, fiscal comparability and sensitivity limits.

## Publication status

[PDF manuscript](paper/IC-EconGym_中文论文完善稿.pdf).

Version 0.2.0 is a research prototype with a Chinese manuscript. No acceptance, DOI or arXiv identifier is asserted. Author information and licensing are to be supplied by the project owner. GitHub Actions validate the environment and deploy `docs/` to Pages after push. Set Pages source to **GitHub Actions**.

## References and attribution

- [EconGym](https://github.com/Miracle1207/EconGym): task-oriented economic benchmarking.
- [WonderEcon](https://github.com/Planet-300894/WonderEcon): economic trajectory observation and interaction.
- [Economic world model blueprint](https://arxiv.org/abs/2608.06020): systems framing and evaluation boundaries.

This repository does not redistribute the reference projects. See [third-party notices](THIRD_PARTY_NOTICES.md).


项目主页：https://Jinhua188.github.io/IC-EconGym/  
源码：https://github.com/Jinhua188/IC-EconGym  
更新页面：`python -m pip install -r requirements_site.txt` 后执行 `python -m scripts_ic.build_project_site`。修改 `paper/manuscript_zh.md` 后推送 `main`，Pages 自动重建论文与演示。

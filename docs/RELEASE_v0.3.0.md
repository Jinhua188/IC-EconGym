# Draft GitHub Release — IC-EconGym v0.3.0

**Suggested tag:** `v0.3.0`  
**Suggested title:** `IC-EconGym v0.3.0 — Learning, Robustness and External-Validation Release`

> Draft only. VERSION is set to 0.3.0 for release preparation; the tag, Release and DOI remain unpublished until the gates in RELEASE_READINESS.json are confirmed.

## Release positioning

This is a **research-prototype benchmark release**, not a calibrated digital twin or real-world policy forecasting product.

v0.3.0 formalizes the experimental work previously described as `v0.3-experimental` and adds open-source governance, citation metadata and release/DOI procedures.

## What is included

### Core environment

- 13 input–output-related industrial-sector decision agents + 1 government agent;
- 15 configured tasks across AI empowerment (E1–E5), risk (R1–R5) and governance (G1–G5);
- source-specific domestic/import input constraints, inventory, capacity, rationing, project lags and fiscal-budget execution;
- three accounting-consistent import-allocation assumptions.

### Diagnostics and benchmark evidence

- 870 task-diagnostic trajectories across configured arms and seeds;
- R1 sector IPPO and G5 government PPO with 20 independent training instances in total;
- 6,000 locked test trajectories across in-distribution and unseen scenarios;
- 23,400 joint-parameter / alternative-rationing evaluations;
- 600 mechanism-scan runs plus targeted threshold diagnostics;
- a local manufacturing-capacity external-validation case;
- fixed-agent inference/runtime and batch-throughput measurements.

### Results intentionally retained

This release does **not** filter out unfavorable results:

- R1 IPPO increases its training reward but performs substantially worse than the transparent rule baseline on locked final-demand delivery tests;
- G5 PPO does not show a clearly separated improvement over uniform allocation under the current protocol;
- the local capacity-queue rule improves on a flat baseline in the holdout period but is inferior to a simple linear trend;
- several configured mechanisms are non-binding or fail to activate under their original task settings, and these failures remain documented.

## Scientific boundary

The release supports claims about executable conditional mechanisms, benchmark interfaces, diagnostic behavior and local validation checks. It does **not** establish:

- causal effects of real-world industrial policies;
- a complete firm-level semiconductor transaction network;
- empirically identified nationwide dynamic parameters;
- LLM-agent superiority or general economic-world-model validity.

Synthetic supplier channels and candidate firm edges must not be interpreted as observed transaction links.

## Governance and citation additions

- Apache-2.0 license for project-authored source code, with explicit third-party/data-rights scope;
- `CITATION.cff` for GitHub/Zenodo citation metadata;
- contribution and governance policies;
- Issue Forms for bugs, research questions, benchmark proposals and data/validation evidence;
- PR template and CODEOWNERS;
- branch/release/Zenodo setup checklist.

## Reproduction

```bash
python -m pip install -r requirements_ic.txt
python validate_extension.py
python -m scripts_ic.run_all_tasks --out demo_results_v2 --seeds 1,2,3 --arms v1
```

See `REPRODUCIBILITY.md`, `EXPERIMENT_UPGRADE.md`, `DATA_CARD.md` and the manuscript for task-specific commands and interpretation.

## Before publishing this release

- [x] Set `VERSION` to `0.3.0` for the pending release line (not proof of publication).
- [x] Record owner-confirmed software author Jinhua Gu and ORCID in CITATION.cff; affiliation in AUTHOR_METADATA.md.
- [ ] Confirm that all included source/data files may legally be redistributed.
- [ ] Run `python validate_extension.py`, `python -m scripts_ic.verify_upgrade` and `python -m scripts_ic.check_governance`; refresh and verify `MANIFEST.sha256`.
- [ ] Confirm the human release gates, then run `python -m scripts_ic.check_governance --publication`. This must fail while confirmations are pending.
- [ ] Confirm the selected main-branch candidate passes Pages deployment; record the source commit before tagging. The current Pages workflow deploys main, not tag pushes.
- [ ] Enable the repository in Zenodo before creating the GitHub Release.
- [ ] Create the immutable `v0.3.0` GitHub Release.
- [ ] Wait for Zenodo archival and record the version-specific DOI.
- [ ] Add the DOI to `CITATION.cff` and README on `main` without moving the `v0.3.0` tag.

## Citation

A DOI will be added after Zenodo archives this release. For exact reproducibility, cite the DOI associated with this specific release version.

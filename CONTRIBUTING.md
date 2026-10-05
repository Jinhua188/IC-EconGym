# Contributing to IC-EconGym

Thank you for helping improve IC-EconGym. The project welcomes contributions that strengthen scientific clarity, reproducibility, mechanism design and benchmark quality.

## 1. Contribution workflow

For contributors without write access:

1. **Open an Issue first** for a scientific mechanism, new benchmark task, new external dataset/validation case, or a substantial algorithmic change.
2. Fork the repository and create a focused branch, e.g. `feat/r1-mappo-baseline` or `fix/final-demand-metric`.
3. Make the smallest coherent change that can be independently reviewed.
4. Run relevant validation and reproduction commands.
5. Open a Pull Request using the repository template.
6. A maintainer decides whether the PR is merged. Opening a PR does not guarantee inclusion.

Small documentation fixes and obvious bugs may be submitted directly as a PR.

## 2. Scientific contribution classes

### A. Bug or implementation fix

A bug is a mismatch between documented behavior and implementation, a numerical/engineering defect, or a reproducibility failure. Please provide a minimal reproduction.

### B. Mechanism or research-question proposal

A new economic mechanism is **not** automatically a bug fix. State:

- the scientific question;
- the economic mechanism and causal channel inside the model;
- the state variables and actions affected;
- the constraint that should bind or become observable;
- what result would count as mechanism activation;
- which literature or data motivates the mechanism;
- which parameters are estimated, calibrated, proxied or scenario-assigned.

### C. New benchmark task

A task should include:

- a task identifier and human-readable name;
- a precise intervention/shock;
- observation and action permissions;
- common resource/budget constraints;
- primary and secondary metrics;
- a diagnostic showing that the intended mechanism can actually activate;
- at least one transparent baseline;
- reproducible seeds/splits and metadata.

### D. New strategy or learning baseline

New baselines must use the same observation permissions, feasible-action projection and external resources as the strategies they are compared with, unless the scientific purpose is explicitly to change those conditions.

Please report:

- algorithm and hyperparameters;
- training budget and number of independent training instances;
- checkpoint-selection rule;
- locked test scenarios;
- final-demand delivery separately from training reward;
- private/fiscal resource use where relevant;
- runtime or compute budget when it affects comparability.

Do not tune on the locked test set. The v0.3 test cases and their published scores are public: unseen scenarios refer to the original frozen training run, not secret future tests. New algorithms can overfit public cases; disclose any prior exposure and use a separately versioned prospective test for new generalization claims.

### E. Data or external-validation contribution

Every new data source must document:

- original source and URL/identifier;
- observation date or vintage;
- units and transformations;
- license or redistribution status;
- mapping from source variables to model variables;
- whether the data are used for calibration, validation, proxy construction or descriptive context;
- known missingness and identification limits.

Do not commit restricted source files merely because they are publicly viewable elsewhere.

## 3. Evidence-boundary rule

Use the strongest wording supported by the evidence, and no stronger.

Preferred labels in text and PR descriptions:

- **model-internal / conditional simulation** — result follows within a specified model configuration;
- **local external check** — a component is compared with an independent observed series or event;
- **empirically calibrated** — a parameter was estimated/calibrated from relevant data;
- **causal real-world claim** — requires a separate identification design and should not be inferred from the simulator alone.

Synthetic supplier channels, scenario parameters and candidate firm edges must never be described as observed real-world transaction networks.

## 4. Reproduction checks

At minimum run:

```bash
python -m pip install -r requirements_ic.txt
python validate_extension.py
python -m pip install -r requirements_governance.txt
python -m scripts_ic.check_governance
```

For changes to benchmark logic, also run the affected task/strategy scripts and include commands and output paths in the PR.

For changes that alter reported manuscript results, update the relevant result artifacts, `CHANGELOG.md`, metadata/hash manifests and manuscript tables/figures in the same PR when feasible.

## 5. Style and scope

- Keep model behavior explicit and inspectable.
- Prefer configuration over hidden hard-coded constants.
- Preserve units and accounting identities.
- Do not silently change locked benchmark splits.
- Do not convert model assumptions into empirical facts in documentation.
- Avoid adding dependencies unless they materially improve the research workflow.

## 6. Rights and attribution

By submitting a contribution intended for inclusion in Apache-2.0-covered project code, you agree that the merged contribution may be distributed under Apache-2.0, unless an alternative arrangement is agreed before submission.

You must have the right to submit all code, data, text and media in your contribution. Cite third-party methods and sources where appropriate.

## 7. Authorship and academic credit

A code contribution does not automatically determine paper authorship. Paper authorship follows the contribution and authorship policy of the relevant manuscript/team. Significant software, benchmark, data and validation contributions should be acknowledged and may be credited as contributors in release metadata where appropriate.

For questions, open an Issue rather than sending unpublished data or credentials through a public thread.

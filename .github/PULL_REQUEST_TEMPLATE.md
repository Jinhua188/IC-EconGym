## Summary

What does this PR change, and why is it needed?

## Contribution type

- [ ] Bug / implementation fix
- [ ] New or revised economic mechanism
- [ ] New benchmark task
- [ ] Rule / optimization baseline
- [ ] RL / MARL / LLM-agent baseline
- [ ] Data / calibration / external validation
- [ ] Reproducibility / performance
- [ ] Documentation / website / metadata
- [ ] Governance / release engineering

## Scientific claim and evidence boundary

What claim can this PR support? Mark the strongest applicable level.

- [ ] Model-internal / conditional simulation only
- [ ] Local external check
- [ ] Empirically calibrated component
- [ ] Other (explain)

Describe what this PR **does not** establish:

## Mechanism / benchmark integrity

- [ ] The intended mechanism can be shown to activate or bind, or non-activation is explicitly reported.
- [ ] Locked test scenarios were not used for training, tuning or checkpoint selection.
- [ ] Observation permissions and feasible action/resource constraints are comparable across claimed baselines.
- [ ] Final-demand delivery is reported separately from policy-generated internal orders when relevant.
- [ ] Resource use (private/fiscal/compute) is reported when it affects comparability.

## Data and rights

- [ ] No restricted or unlicensed third-party material is newly redistributed.
- [ ] New data sources include provenance, units, transformations and license/redistribution status.
- [ ] Synthetic/proxy/candidate relationships are labeled as such and are not described as observed transactions.

## Reproduction

Commands run:

```bash
# paste commands here
```

Key output paths / expected checks:

## Tests

- [ ] `python validate_extension.py`
- [ ] Affected task(s) rerun
- [ ] Relevant figures/tables regenerated if outputs changed
- [ ] Metadata/hash manifests updated if needed
- [ ] Documentation updated

## Release impact

- [ ] No release-note entry needed
- [ ] Patch-level change
- [ ] Minor-version scientific/benchmark change
- [ ] Breaking change / requires explicit migration note

Related Issue(s):

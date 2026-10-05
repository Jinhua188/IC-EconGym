# IC-EconGym Governance

## Purpose

IC-EconGym is governed as an academic research software and benchmark project. Openness means that others may inspect, fork, test and propose changes; it does not mean that the canonical repository is jointly writable by all visitors.

## Roles

### Repository owner / lead maintainer

`@Jinhua188` is the current repository owner and final merge/release authority.

Responsibilities include:

- maintaining the canonical `main` branch;
- deciding release scope and version numbers;
- approving changes to benchmark definitions, locked splits and scientific claims;
- managing write/admin permissions;
- resolving license and data-rights questions before merge;
- designating future maintainers or reviewers.

### Maintainer

A maintainer is a trusted collaborator explicitly granted repository permissions. Maintainer status is not implied by authorship, issue participation or prior PRs.

### Contributor

Any person who opens Issues, reviews experiments or submits PRs. Contributors normally work through forks and PRs and do not receive direct write access by default.

## Decision model

The project uses **maintainer review, not open voting**, for canonical changes. Scientific disagreement is welcome and should be preserved in Issues/Discussions where useful, but the lead maintainer decides what enters an official release.

For a material scientific change, review should answer four questions:

1. Is the mechanism or algorithm implemented as described?
2. Does the experiment isolate or at least diagnose the intended channel?
3. Are resource, observation and test-set comparisons fair?
4. Does the public wording remain inside the evidence boundary?

## Protected artifacts

The following are treated as high-governance artifacts:

- `main` branch;
- release tags `v*`;
- `benchmark_splits/` locked test definitions;
- `CITATION.cff`, `LICENSE*`, `NOTICE`, `THIRD_PARTY_NOTICES.md`;
- published manuscript result tables/figures;
- provenance, verification and hash manifests.

Changes to these should always go through a PR and explicit maintainer review.

## Branch and merge policy

- `main` is the canonical development/release branch.
- Contributors should not push directly to `main`.
- Force pushes and branch deletion should be disabled for `main`.
- Required automated checks should pass before merge.
- During a single-maintainer phase, PRs may be merged by the owner after checks without an external approval; once a second trusted maintainer is appointed, require at least one approving review for material changes.
- Squash merge is preferred for small PRs; merge commits may be used for release branches or multi-commit contributions where history is scientifically meaningful.

## Benchmark integrity

Locked test sets must not be changed to improve an algorithm's reported score. If a split must be corrected, the project must:

1. document why;
2. version the new split;
3. retain the previous split when feasible;
4. rerun affected baselines;
5. state that old and new results are not directly identical benchmarks.

## Release policy

- Every public scientific release receives a Git tag.
- Release notes state new capabilities, changed assumptions, known failures and evidence boundaries.
- Released tags are immutable; do not move an existing tag to new commits.
- Zenodo archives should be linked to the corresponding immutable release.

## Security and private reports

Do not post credentials, private data, embargoed manuscripts or restricted datasets in public Issues. Security-sensitive problems should follow `SECURITY.md`.

## Changes to governance

Governance changes themselves require a PR and should be mentioned in release notes when they materially affect contribution, licensing or benchmark integrity.

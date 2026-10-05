# License scope and data-rights boundary

## Covered Work

The Apache License 2.0 in `LICENSE` applies to original IC-EconGym source code in `ic_extension/*.py`, `scripts_ic/*.py`, `learning/*.py`, original root Python scripts, original workflow code in `.github/workflows/`, and project-authored task/role configuration in `cfg_ic/` and `ic_extension/data/sector_roles.yaml`, unless a file carries separate terms. It applies only to material the contributor has authority to license; third-party code retains its own terms.

Operational documentation covered by Apache-2.0: root README files and `AUTHOR_METADATA.md`; `CONTRIBUTING.md`, `GOVERNANCE.md`, `ROADMAP.md`, `SECURITY.md`, `LICENSE_SCOPE.md`, `THIRD_PARTY_NOTICES.md`, `NOTICE`, `PUBLISHING.md`, `GITHUB_SETTINGS_CHECKLIST.md`, `ZENODO_RELEASE_GUIDE.md`, `RELEASE_v0.3.0.md`, `RELEASE_PREPARATION.md`, `CHANGELOG.md`, `REPRODUCIBILITY.md`, `EXPERIMENT_UPGRADE.md`, `DATA_CARD.md`, `TASKS.md`, `MECHANISMS.md`, `IEWM13_ADAPTATION.md`; project-authored Issue/PR templates and citation metadata. This covers original explanatory text, not reproduced third-party tables, figures or quotations. Identical generated copies of these documents retain the same scope.

## Separately governed artifacts

| Artifact | Scope and current status |
|---|---|
| `ic_extension/data/*.npz` and numerical extracts | Processed statistical data; Apache-2.0 is not a data-license grant. Source rights and redistribution confirmation remain to be reviewed. |
| `calibration/` data and proxy tables | Derived from supplied statistical/manuscript/AI sources; processing code is covered, underlying records and derived tables are not automatically relicensed. |
| `external_validation/` and source manifests | Official disclosure-derived numerical series and provenance; corporate source terms remain relevant. Raw PDFs are not distributed. |
| `learning/results/` checkpoints | Generated model weights; a separate artifact-license decision and provenance review are required. |
| `benchmark_results/`, `robustness/`, `demo_results*/`, locked scenarios and generated figures | Research artifacts; source-code licensing does not establish a blanket artifact license. Their release rights review is recorded separately. |
| `paper/` and generated paper pages/PDFs | Manuscript, bibliographic evidence and figures; no new manuscript license is granted here. |
| `reference/`, external research files, statistical workbooks, reports, trademarks and logos | Original rights holders' terms apply; a public link is not a redistribution license. |
| `docs/` | A mixed generated site. Original code retains its license; copied documents and artifacts retain their category-specific scope. |

See `RIGHTS_REGISTRY.csv`, `DATA_CARD.md`, `DATA_PROVENANCE.json` and `THIRD_PARTY_NOTICES.md`. The registry records review status rather than creating rights. Excluding an artifact from Apache-2.0 does not itself establish permission to redistribute it. Pending categories must be cleared or removed from a formal release archive.

## Contributions

Contributions intentionally submitted for inclusion in the covered Work are governed by Apache-2.0 Section 5, unless the contributor explicitly states otherwise and a separate agreement is reached before inclusion. Contributors must have authority to submit code, data, weights, documents and media. Paper authorship is determined separately from software contribution credit.

# DOI / Zenodo release guide for IC-EconGym

## Recommended strategy

Use **GitHub Release → Zenodo GitHub integration** as the canonical archive path for IC-EconGym software releases.

Keep `CITATION.cff` as the single repository metadata source unless you specifically need Zenodo-only fields such as grants or communities. If both `.zenodo.json` and `CITATION.cff` are present, Zenodo gives `.zenodo.json` precedence and ignores `CITATION.cff` for GitHub release archiving.

## One-time setup

1. Sign in to Zenodo.
2. Link your GitHub account in Zenodo's linked-account settings.
3. Open the Zenodo GitHub integration page and **Sync now**.
4. Find `Jinhua188/IC-EconGym` and enable it.
5. Confirm `CITATION.cff` contains the owner-confirmed author list and optional ORCID iDs before the release.
6. Do not add a fake DOI. The first GitHub/Zenodo archive can mint the DOI.

## v0.3.0 release procedure

### 1. Freeze the scientific snapshot

- update `VERSION` to `0.3.0`;
- update `CHANGELOG.md`;
- freeze benchmark splits and result summaries;
- run release/verification checks;
- regenerate `MANIFEST.sha256` or equivalent hashes;
- confirm licensing and third-party-data boundaries.

### 2. Validate citation metadata

`CITATION.cff` should contain:

- title;
- software version;
- owner-confirmed authors;
- a real release date once the release is ready;
- ORCID iDs where available;
- Apache-2.0 license for project-authored software;
- repository and project-page URLs;
- keywords and abstract.

The DOI field may be absent before the first archive.

CFF 1.2.0 does not define an `affiliation` field. Keep any confirmed institution information in a separate author document or in the Zenodo record. Do not add fields that fail the schema. `date-released` remains absent during preparation; enter the actual date once publication is authorized.

The GitHub integration archives the repository snapshot. It does not automatically filter data or manuscripts excluded by LICENSE_SCOPE.md. Complete RIGHTS_REGISTRY.csv review, or remove restricted material from the release commit, before archiving. A code-only Apache-2.0 license must not be represented as a license for every archived file.

Before tagging, run:

```bash
python -m scripts_ic.check_governance --publication
```

The command must pass with author, rights and Zenodo confirmations. For learning checks, also run `python -m scripts_ic.verify_upgrade` in the documented learning environment.

### 3. Create an immutable Git tag

Preferred:

```bash
git checkout main
git pull --ff-only
git tag -a v0.3.0 -m "IC-EconGym v0.3.0"
git push origin v0.3.0
```

If you use signed tags, substitute your normal signed-tag workflow.

### 4. Create the GitHub Release

Using GitHub CLI:

```bash
gh release create v0.3.0 --verify-tag \
  --title "IC-EconGym v0.3.0 — Learning, Robustness and External-Validation Release" \
  --notes-file RELEASE_v0.3.0.md
```

Do not move or rewrite the `v0.3.0` tag after publication.

### 5. Let Zenodo archive the release

Once the repository is enabled, Zenodo's GitHub integration processes new GitHub releases. When processing finishes, open the Zenodo record and record its DOI.

For exact reproducibility, cite the **version-specific DOI** attached to the archived release. Zenodo also links versions as a version family; project-level citations may use the family/concept identifier where appropriate, while benchmark papers should normally cite the exact software version they evaluated.

### 6. Add the DOI back to GitHub

After the DOI exists:

- add `doi: "10.5281/zenodo.XXXXXXX"` to `CITATION.cff` on `main`;
- add a DOI badge/link to `README.md`;
- optionally add the DOI to the manuscript/software availability statement.

Do **not** rewrite the old release tag merely to insert its own DOI. The archived release remains immutable. If you need the DOI embedded inside an archived source snapshot, make a small follow-up release such as `v0.3.1` after the metadata update.

## Future versions

For `v0.4.0`, `v0.5.0`, etc.:

1. update `CITATION.cff` version before release;
2. create a new immutable GitHub Release;
3. allow Zenodo to create a linked new version record;
4. cite the exact version DOI in papers that depend on a frozen benchmark.

## Manual DOI reservation — when to use it

Zenodo can reserve a DOI in a draft deposit before publication. This is useful when you must print the DOI inside a document before publishing that record. For the normal IC-EconGym GitHub integration workflow, automatic DOI assignment after the GitHub Release is simpler and reduces the risk of duplicate or mismatched deposits.

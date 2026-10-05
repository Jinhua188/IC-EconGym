# GitHub settings checklist for IC-EconGym

Ruleset configuration is versioned in `.github/rulesets/`. Committing files alone does not enforce rules. The following live settings were applied and read back through GitHub on 2026-10-05:

| Setting | Verified live state |
|---|---|
| main protection | Active [ruleset 24476846](https://github.com/Jinhua188/IC-EconGym/rules/24476846); PR required; `validate` and `governance` from GitHub Actions (app 15368); strict checks; conversations resolved; 0 approving reviews |
| main ref operations | Deletion and force push restricted by the ruleset; repository-admin emergency bypass retained as proposed |
| release-tag integrity | Active [ruleset 24476850](https://github.com/Jinhua188/IC-EconGym/rules/24476850); all `v*` tag updates and deletions blocked, with no bypass actors |
| release-tag creation | Active [ruleset 24476851](https://github.com/Jinhua188/IC-EconGym/rules/24476851); creation restricted to repository admins, currently the owner |
| private vulnerability reporting | Enabled; use repository Security → Report a vulnerability |
| merge settings | Squash and merge commits enabled; automatic branch deletion after merge enabled |
| Zenodo | Not connected, as confirmed by the owner; no DOI asserted |

Admin bypass on main is for emergencies and does not replace the normal PR workflow. Tag immutability has no bypass actor while the ruleset remains active; an admin can still alter repository settings, which must be documented. No collaborator or reviewer permissions were added.


## 1. Protect `main` with a ruleset / branch protection

Recommended during the current single-maintainer phase:

- target branch: `main`;
- require changes through Pull Requests;
- require relevant Actions/status checks to pass;
- require all review conversations to be resolved;
- block force pushes;
- block branch deletion;
- keep repository-owner/admin bypass available for emergencies;
- **do not require an external approving review yet if @Jinhua188 is the only trusted maintainer**, otherwise the owner may create an unnecessary self-review bottleneck.

After a second trusted maintainer is appointed:

- require at least **1 approving review** for material PRs;
- require CODEOWNERS review for protected scientific/governance files;
- consider dismissing stale approvals when protected files change.

## 2. Protect release tags

Use a tag ruleset for `v*`:

- restrict deletion;
- restrict force updates / tag recreation;
- currently only repository admins may create release tags; expanding this role requires an explicit governance/settings change.

Published scientific tags should be immutable.

## 3. Actions and Pages

- keep the existing validation workflow enabled;
- require its successful status check before benchmark-affecting merges;
- keep GitHub Pages source set to GitHub Actions;
- avoid giving workflows broader write permissions than necessary.

## 4. Repository features

Recommended:

- Issues: ON;
- Pull Requests: ON;
- Discussions: optional but useful for broad research questions that are not actionable Issues;
- Wikis: optional; keep canonical scientific documentation in version-controlled files;
- private vulnerability reporting: ON if available.

## 5. Merge methods

Recommended:

- Squash merge: ON;
- Merge commit: ON when preserving scientific history is useful;
- Rebase merge: optional;
- Automatically delete head branches after merge: ON.

## 6. Access policy

- do not grant write/admin access merely because someone wants to test the platform;
- default external workflow: Fork → Branch → PR;
- grant `Write` only to trusted recurring maintainers;
- reserve `Admin` for the repository owner or a very small governance group.

## 7. Labels to create

Suggested labels:

- `bug`
- `research-question`
- `mechanism`
- `benchmark`
- `baseline`
- `data`
- `validation`
- `reproducibility`
- `documentation`
- `governance`
- `breaking-change`
- `good-first-issue`
- `needs-evidence`
- `evidence-boundary`

## 8. Release gate for v0.3.0

Before clicking **Publish release**:

- governance files merged;
- branch rules active;
- `VERSION=0.3.0`;
- owner-confirmed software author in CITATION.cff (completed: Jinhua Gu and supplied ORCID);
- license scope reviewed;
- public data rights checked;
- release tests green;
- Zenodo integration enabled;
- draft release notes reviewed.

## Official references

- [GitHub ruleset API](https://docs.github.com/en/rest/repos/rules)
- [Protected branches and admin bypass](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)

# GitHub server settings

Verified through GitHub settings on 3 October 2026.

## Main branch

- Pull requests required, including administrators; bypass disabled.
- Required checks from GitHub Actions: `Repository and approval checks`, `gitleaks`, and `analyze` (CodeQL).
- Branch must be up to date; review conversations must be resolved.
- Force pushes and branch deletion prohibited.
- Approval count is zero for the solo-owner workflow. CODEOWNERS requests owner review but an independent approving review is not enforced. Add that requirement when a second maintainer is available.

## Actions

- Default token permissions: read contents and packages.
- Workflow PR creation/approval disabled.
- Full-length commit SHA pinning enforced.
- External actions restricted to `actions/checkout@*`, `actions/setup-python@*`, `github/codeql-action/*`, and `gitleaks/gitleaks-action@*`; actions in rjw3000 repositories are also allowed by GitHub's selected-actions policy.
- All external contributors require approval before fork PR workflows run.

## Security and bots

- Private vulnerability reporting enabled.
- Dependency graph and Dependabot vulnerability alerts/security updates enabled.
- Existing secret protection and push protection verified enabled.
- CodeQL advanced setup active; high-or-higher security threshold and error-level standard threshold retained.
- Dependabot version updates configured weekly. Autofix suggestions are enabled; no automatic merging or approving bot configured.

Recheck settings after policy changes. These protections cover the repository, not production application security.

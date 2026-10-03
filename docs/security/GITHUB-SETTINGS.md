# GitHub server settings

Committed workflows are separate from server settings. Verify these in repository Settings before treating protection as enforced:

- Main branch: require pull requests, passing CI/CodeQL/Secret scan checks, resolved conversations, no force pushes or deletion. Owner review policy is in CODEOWNERS; configure enforcement to fit the solo-owner workflow without impossible self-approval requirements.
- Actions: default read-only token; disable workflow PR approval; allow only reviewed actions; require pinned SHAs where available.
- Security: enable private vulnerability reporting, Dependabot alerts/security updates, secret scanning, and push protection where supported.
- Bot PRs remain review-required. Do not add auto-merge/auto-approve bots.

Server configuration is not asserted as enabled by this document.

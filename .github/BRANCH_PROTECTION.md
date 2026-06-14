# Branch protection — `main`

Branch protection is enforced on GitHub for the `main` branch.
These settings protect production code and legal assets across the GyroERP organization.

## Rules on all repositories

| Rule | backend | frontend | database |
|------|:-------:|:--------:|:--------:|
| Pull request required before merge | Yes | Yes | Yes |
| Minimum approving reviews | 1 | 1 | 1 |
| Dismiss stale reviews on new pushes | Yes | Yes | Yes |
| Require approval on last push | Yes | Yes | Yes |
| Resolve all conversations before merge | Yes | Yes | Yes |
| Block force pushes | Yes | Yes | Yes |
| Block branch deletion | Yes | Yes | Yes |
| Apply rules to administrators | Yes | Yes | Yes |

## Backend-only (CI)

The backend repo also requires these status checks to pass before merge:

- **Django checks** — `manage.py check`, migration check, tests
- **Ruff** — lint and format

Code owner review is required (`CODEOWNERS` → `@TheodoreAsher`).

## Workflow for changes

1. Create a feature branch from `main`
2. Open a pull request
3. Wait for required checks (backend) and at least **one approval**
4. Merge via pull request — **never push directly to `main`**

```bash
git checkout -b feature/my-change
git push -u origin feature/my-change
gh pr create --fill
```

## Re-applying protection (maintainers)

JSON templates live in `scripts/`:

- `branch-protection-backend.json` — backend (includes CI checks)
- `branch-protection-base.json` — frontend / database

```powershell
gh api --method PUT repos/GyroERP/backend/branches/main/protection `
  --input scripts/branch-protection-backend.json

gh api --method PUT repos/GyroERP/frontend/branches/main/protection `
  --input scripts/branch-protection-base.json

gh api --method PUT repos/GyroERP/database/branches/main/protection `
  --input scripts/branch-protection-base.json
```

## Solo maintainer note

With **admin rules enforced** and **1 approval required**, you cannot approve your own pull requests.
Add a trusted collaborator as reviewer, or adjust the approval count in the JSON templates above.

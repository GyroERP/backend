# Release management — GyroERP Backend

Releases follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`) and are managed entirely in GitHub.

---

## Release pipeline

```
development → staging → beta-release → release/x.y.z → main + tag vX.Y.Z
```

| Stage | Branch | QA gate |
|-------|--------|---------|
| Development | `development` | Unit tests + lint (CI) |
| Staging | `staging` | Integration / staging QA |
| Beta | `beta-release` | UAT / stakeholder beta |
| Release candidate | `release/x.y.z` | Release QA checklist |
| Production | `main` + tag | Final approval + GitHub Release |

---

## Creating a version release

### 1. Create release branch from beta

```bash
git checkout beta-release
git pull origin beta-release
git checkout -b release/1.0.0
git push -u origin release/1.0.0
```

### 2. Open PR: `release/1.0.0` → `main`

Use the **Promotion** PR template. Complete the release checklist in the PR.

### 3. Merge to `main` and tag

After merge:

```bash
git checkout main
git pull origin main
git tag -a v1.0.0 -m "GyroERP Backend v1.0.0"
git push origin v1.0.0
```

Pushing a `v*.*.*` tag triggers [`.github/workflows/release.yml`](.github/workflows/release.yml) to create a **GitHub Release** with generated notes.

### 4. Sync back to development

Open PR: `main` → `development` (or cherry-pick) so hotfixes and release fixes propagate.

---

## Version numbering

| Change | Bump | Example |
|--------|------|---------|
| Breaking API / schema | MAJOR | 1.0.0 → 2.0.0 |
| New feature, backward compatible | MINOR | 1.0.0 → 1.1.0 |
| Bug fix, backward compatible | PATCH | 1.0.0 → 1.0.1 |

Document changes in [CHANGELOG.md](CHANGELOG.md) under the release version.

---

## GitHub Release checklist

Before tagging `vX.Y.Z`:

- [ ] All promotion PRs merged (dev → staging → beta → release → main)
- [ ] [CHANGELOG.md](CHANGELOG.md) updated
- [ ] Migration notes documented (if any)
- [ ] Staging + beta QA sign-off in promotion PRs
- [ ] No open `priority:critical` or `priority:high` bugs for this release
- [ ] Security review for auth/permission changes

---

## Pre-release tags (optional)

For beta testing on `beta-release`:

```bash
git tag -a v1.0.0-beta.1 -m "Beta 1 for 1.0.0"
git push origin v1.0.0-beta.1
```

Pre-release tags do not trigger production release workflow.

---

## Rollback

If production issues occur after release:

1. Open `hotfix/*` from `main`
2. Fix, PR to `main`, tag `vX.Y.Z+1` (patch bump)
3. Cherry-pick to `development`

Do **not** force-push or rewrite `main` history.

---

## GitHub-only tooling

| Tool | Use |
|------|-----|
| **Issues** | Track release scope and bugs |
| **Projects** | Release milestone column / iteration |
| **Milestones** | Group issues per version (e.g. `v1.0.0`) |
| **Releases** | Published artifacts and notes |
| **Actions** | CI + automated release draft |

See [BRANCHING.md](BRANCHING.md) for the full branch workflow.

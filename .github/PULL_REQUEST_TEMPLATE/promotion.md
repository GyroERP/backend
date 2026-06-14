## Promotion PR

| Field | Value |
|-------|-------|
| **From** | <!-- e.g. development --> |
| **To** | <!-- e.g. staging --> |
| **Version / milestone** | <!-- e.g. v1.0.0 milestone --> |

## Summary

Describe what is being promoted and why now.

## QA sign-off

| Environment | Tester | Date | Result |
|-------------|--------|------|--------|
| Development | | | Pass / Fail |
| Staging | | | Pass / Fail / N/A |
| Beta | | | Pass / Fail / N/A |

## Release checklist

- [ ] All linked issues reviewed and acceptable for this stage
- [ ] CI green on source branch
- [ ] [CHANGELOG.md](../CHANGELOG.md) updated (required for beta → release → main)
- [ ] No open `priority:critical` bugs for this promotion
- [ ] Database migrations reviewed (if any)
- [ ] Rollback plan noted (if risky change)

## Allowed promotion paths

| From | To |
|------|-----|
| `development` | `staging` |
| `staging` | `beta-release` |
| `beta-release` | `release/x.y.z` |
| `release/x.y.z` | `main` |

See [BRANCHING.md](../BRANCHING.md) and [RELEASE.md](../RELEASE.md).

## Approvals

- [ ] Code owner review
- [ ] QA approval documented above

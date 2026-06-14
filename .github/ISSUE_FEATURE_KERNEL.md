## Feature goal

Implement **GyroERP Kernel** — the foundational backend layer that all ERP modules
(inventory, sales, finance, etc.) will build upon.

## Scope

| Component | Description |
|-----------|-------------|
| `kernel` Django app | Core package structure and registration |
| API v1 namespace | `/api/v1/` routing convention |
| Base model mixins | Timestamps, soft-delete, UUID PK |
| RBAC foundation | Roles, permissions, DRF integration |
| Audit log base | Create/update/delete tracking |
| Module registry | Plugin pattern for future ERP apps |

## Acceptance criteria

- [ ] `kernel` app created and registered in Django settings
- [ ] `/api/v1/` router established
- [ ] Base mixins available for future modules
- [ ] RBAC models with permission checks in DRF
- [ ] Audit logging hooks implemented
- [ ] Module registration pattern documented with example stub
- [ ] Tests for kernel core behavior
- [ ] Documentation updated in README / BRANCHING.md

## Branch

Work on: **`feature/<issue#>-gyroerp-kernel`** branched from **`development`**

## References

- [BRANCHING.md](https://github.com/GyroERP/backend/blob/development/BRANCHING.md)
- [PROJECT.md](https://github.com/GyroERP/.github/blob/main/PROJECT.md)
- Epic context: kernel blocks all other backend modules

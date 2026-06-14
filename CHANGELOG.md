# Changelog

All notable changes to the GyroERP backend are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Core ERP modules (inventory, sales, purchasing, accounting)
- API v1 namespace and OpenAPI documentation
- Multi-language (i18n) support
- Role-based access control (RBAC)

## [0.1.0] - 2026-06-14

### Added

- Django 5.2 project scaffold with REST Framework and django-filter
- Split settings: development, production, and shared base
- Environment-based configuration (`.env` / `.env.example`)
- Health check endpoint at `/health/`
- Docker and Docker Compose setup with PostgreSQL
- CI workflow (Django checks, tests, Ruff lint)
- Repository documentation: README, AUTHORS, CODE_OF_CONDUCT, SUPPORT, SECURITY
- Git/GitHub scaffolding: `.gitignore`, `.gitattributes`, Dependabot, issue templates
- Legal and licensing files (GyroERP Community License)

[Unreleased]: https://github.com/GyroERP/backend/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GyroERP/backend/releases/tag/v0.1.0

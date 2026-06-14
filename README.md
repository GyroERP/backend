# GyroERP Backend

**GyroERP** is a modern ERP platform — **by Muhammad Ahsan**.

This repository contains the Django REST API backend for inventory, finance,
operations, and business workflows. It is designed for global teams with
internationalization, timezone-aware data, and a scalable API-first architecture.

[![CI](https://github.com/GyroERP/backend/actions/workflows/ci.yml/badge.svg)](https://github.com/GyroERP/backend/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Django](https://img.shields.io/badge/django-5.2-green.svg)
![License](https://img.shields.io/badge/license-GyroERP%20Community%20License-lightgrey.svg)

## Related repositories

| Repository | Description |
|------------|-------------|
| [GyroERP/frontend](https://github.com/GyroERP/frontend) | Web application UI |
| [GyroERP/database](https://github.com/GyroERP/database) | Database schemas and migrations |
| [GyroERP/.github](https://github.com/GyroERP/.github) | Organization profile and community docs |

## Branching & releases

All backend work follows the **development → staging → beta-release → main** pipeline.

| Doc | Purpose |
|-----|---------|
| [BRANCHING.md](BRANCHING.md) | Branch rules, naming, PR workflow |
| [RELEASE.md](RELEASE.md) | Versioning, tags, GitHub Releases |

**Active integration branch:** `development` — always branch from `development`, never from `main`.

## Tech stack

- **Python 3.12+**
- **Django 5.2** + **Django REST Framework**
- **PostgreSQL** (production) / SQLite (local dev)
- **Docker** for consistent environments worldwide

## Quick start (local)

### Prerequisites

- Python 3.12 or newer
- Git

### Setup

```bash
git clone https://github.com/GyroERP/backend.git
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env and set DJANGO_SECRET_KEY to a long random string

python manage.py migrate
python manage.py runserver
```

Open:

- API health check: http://127.0.0.1:8000/health/
- Admin: http://127.0.0.1:8000/admin/

Create a superuser:

```bash
python manage.py createsuperuser
```

## Quick start (Docker)

```bash
git clone https://github.com/GyroERP/backend.git
cd backend
cp .env.example .env
# Set DJANGO_SECRET_KEY in .env

docker compose up --build
```

The API runs at http://localhost:8000 with PostgreSQL on port 5432.

## Environment variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Required. Long random string — never commit this. |
| `DJANGO_DEBUG` | `True` for local dev, `False` for production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `DJANGO_SETTINGS_MODULE` | `gyroerp.settings.development` (default via manage.py) |
| `DATABASE_URL` | Optional. PostgreSQL URL; defaults to SQLite locally |

See [`.env.example`](.env.example) for the full list.

## Settings modules

| Module | Use case |
|--------|----------|
| `gyroerp.settings.development` | Local development (`manage.py` default) |
| `gyroerp.settings.production` | Production / Docker / WSGI |

## Development

```bash
# System checks
python manage.py check

# Tests
python manage.py test

# Lint
ruff check .
ruff format --check .
```

## Project structure

```
backend/
├── gyroerp/              # Django project
│   ├── settings/         # base, development, production
│   ├── urls.py
│   └── views.py          # health check, shared views
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
└── docker-compose.yml
```

## Contributing

Contributions are welcome under the terms in [CONTRIBUTING.md](CONTRIBUTING.md).
Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating.

## Security

Report vulnerabilities privately — see [SECURITY.md](SECURITY.md).
Do **not** open public issues for security problems.

## Support

See [SUPPORT.md](SUPPORT.md) for help channels.

## Authors

GyroERP was founded by **Muhammad Ahsan**. See [AUTHORS.md](AUTHORS.md).

## License

GyroERP is **source-available** software under the
[GyroERP Community License](LICENSE). It is not OSI open source.

- Internal use, evaluation, and community contributions are permitted under the license.
- Commercial redistribution, SaaS hosting, resale, and rebranding require written permission.

| Contact | Email |
|---------|-------|
| Commercial licensing | licensing@gyroerp.com |
| Security | security@gyroerp.com |
| Legal / trademarks | legal@gyroerp.com |

See also [COPYRIGHT.md](COPYRIGHT.md), [TRADEMARKS.md](TRADEMARKS.md), and [NOTICE](NOTICE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

# Agent Instructions

## Tech Stack & Environment
- **Runtime**: Python 3.13 (managed by `uv`)
- **Framework**: Flask
- **Web Server**: Gunicorn (production via Docker/Nginx)
- **Linting/Formatting**: [Ruff](https://astral.sh/ruff)
- **Testing**: `pytest`
- **Deployment**: Docker / Docker Compose

## Key Commands
- **Run locally**: `python app.py`
- **Run tests**: `python -m pytest` (run from repo root; bare `pytest` fails with `ModuleNotFoundError: No module named 'app'` because the root isn't on `sys.path`)
- **Linting**: `ruff check .`
- **Formatting**: `ruff format .`
- **Setup environment**: Configure `config/.env` (referenced in `README.md`)
- **Docker Compose**: `docker-compose up -d`

## Project Architecture
- `app.py`: Application entry point.
- `core/`: Main business logic, including:
  - `core/route/`: Flask blueprints/routes.
  - `core/service/`: Business logic services (e.g., `orcid_service.py`).
  - `core/utils/`: General utilities.
- `static/`: Static assets with content hashing for long-lived caching.
- `templates/`: Jinja2 templates.

## Conventions & Quirks
- **Static Assets**: Uses content hashing for cache invalidation. The custom `_serve_static` view function in `app.py` handles fingerprinting and cache headers.
- **Reverse Proxy**: Uses `ProxyFix` (one hop) to handle headers from Nginx.
- **Session**: Uses `crossref_session` cookie name.
- **Configuration**: Environment-specific settings are loaded from `config/.env` and applied via `settings.py`.

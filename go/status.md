# Migration Status Summary

## Objective
- Convert the Crossref search Python/Flask application to Go, writing all Go code in the `go/` directory under the repo root `/Users/oem/src/crossref/search/`.
- Plan: `MIGRATION_PLAN.md` (repo root)

## Important Details
- **Repo root**: `/Users/oem/src/crossref/search/` — **Go target dir**: `go/` — **Module**: `crossref_search` — **Go**: 1.24
- **Constraints**: Stdlib only (no external deps); mirror Python behaviour faithfully
- **URL Encoding Decision**: Using Go stdlib (`net/url`) for all API URL and Request URL construction. This avoids the quirkier `furl` double-encoding behavior (re-encoding of already-encoded paths/queries) while maintaining compatible output (e.g., space → `+`).
- **Template Strategy**: Port ~28 Jinja2 templates to Go `html/template` using `{{define}}`/`{{template}}` named-template pattern; context to include: {page, items, signed_in, orcid_info, flashes, expired_session, static_url, csrf_token}.
- **Session Strategy**: Signed-cookie (HMAC-SHA256) mirroring Flask's default; cookie name `crossref_session`, Secure/HttpOnly, 30-day lifetime
- **Static Assets**: Content-hash manifest (SHA-256 first 10 hex chars) built from `../static/` relative to `go/`; serve with 1-year immutable cache for known hashes, 1-hour cache for fallbacks (mirrors `app.py:_serve_static`).
- **CORS**: `https://assets.crossref.org`, `https://search-cdn.production.crossref.org`
- **CSRF**: Only the `/search/references` POST form needs token (double-submit cookie pattern)
- **ProxyFix**: Trust one hop of X-Forwarded-For/X-Forwarded-Proto/X-Forwarded-Host.
- **ORCID**: Manual implementation; Python `verify=False` → Go `InsecureSkipVerify` client.
- **Pagination**: 20 rows/page, 10 page limit (200 items max), offset-based via Crossref API

## Work State

### Completed
- **Repo scan**: All Python source files and tests read
- **`go/go.mod`**: Module `crossref_search`, go 1.24
- **`go/config/config.go`**: `Settings` struct + `Load()` from env vars
- **`go/core/constants.go`**: Scalar and regex constants
- **`go/core/errors/errors.go`**: `APIConnectionException`, `OrcidAPIException`, etc.
- **`go/core/session/session.go`**: Signed cookie session, flash, CSRF
- **`go/core/static_assets/static_assets.go`**
- **`go/core/utils/utils.go`**: Core utilities (IP, Headers, DOI, etc.)
- **`go/core/service/orcid_service.go`**: ORCID claim logic (ported)
- **Build Fixes (Session 1)**: Resolved compilation errors in `config` (shadowing), `session` (b64decode signature mismatch), and `orcid_service` (import paths). (`go build ./...` and `go vet ./...` passed).
- **`go/core/service/pagination.go`**: Ported `flask_paginate` with `bootstrap4` framework (verbatim replication of `Links()` HTML, `prev_page`, `next_page`, and `single_page`).

### Active / Next
- **`go/core/service/search_service.go`**: Port of `search_service.py` (~500 lines). Includes `get_api_url`, `search_query`, `resolve_references`, `all_funders_data`, and `csv_data`.
- **`go/core/service/auth_service.go`**: Port of `auth_service.py` session management.
- **Go route/handler files**: Search, Auth (ORCID), Healthcheck, and Error handlers.
- **Go templates**: Port ~28 Jinja2 templates to `go/templates/` (base, layout, splash, results, etc.).
- **`go/main.go`**: Entry point, server bootstrap, router wiring, template loading, static file serving.
- **Tests**: Mirror Python pytest suite in Go.
- **Verification**: `go vet`, `go test`, and running the server for smoke-testing.

## Relevant Files
- `/Users/oem/src/crossref/search/app.py` (Source Truth)
- `/Users/oem/src/crossref/search/core/service/search_service.py` (Largest File)
- `/Users/oem/src/crossref/search/templates/` (Jinja2 source)
- `/Users/oem/src/crossref/search/.venv/lib/python3.13/site-packages/flask_paginate/` (Pagination reference)

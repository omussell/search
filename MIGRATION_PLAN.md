# Migration Plan: Python to Go Conversion

## Overview
This document outlines the strategy for migrating the Crossref search service from a Python/Flask stack to a Go-based architecture. The goal is to improve performance, concurrency handling, and type safety while maintaining the existing functionality of the search engine and ORCID integration.

## Architecture Mapping

| Component | Python / Flask | Go Equivalent |
| --- | --- | --- |
| Web Framework | Flask | Gin or Echo |
| Routing | Blueprints | Gin Router Groups |
| HTTP Client | `requests` | `net/http` or `resty` |
| Template Engine | Jinja2 | `html/template` |
| Configuration | `settings.py` | `envconfig` or `viper` |
| Concurrency | Threaded/Asyncio | Goroutines & Channels |
| Session Mgmt | Flask Sessions | Redis-backed session store |

## Component Breakdown

### 1. Routing & Controllers
- **Current**: Blueprints define paths like `/search`, `/auth`, and `/help`.
- **Proposed**: Use Gin Router Groups to mirror the current URL structure.
- **Tasks**:
    - Implement a `Router` package to initialize all groups.
    - Create `Handler` packages for `Search`, `Auth`, `Home`, and `HealthCheck`.
    - Implement a global `ErrorHandler` middleware to mirror the `app.errorhandler` decorators.

### 2. Services Layer
- **Search Service** (`core/service/search_service.py`):
    - Port the `get_api_url` logic to a Go function that builds URLs based on categories.
    - Implement the result parsing logic (`add_item_data`, `add_published_date`, etc.) using Go structs and custom unmarshaling.
    - Port the CSV generation logic using the standard `encoding/csv` package.
- **Auth Service** (`core/service/auth_service.py`):
    - Replace Flask session writes with a dedicated `SessionStore` interface.
    - Implement ORCID token refresh and validation logic.
- **Utils**:
    - Direct port of `prepare_api_headers`, `get_doi_url`, and `get_host_url` into a `utils` package.

### 3. Configuration & Constants
- **Constants**: Port `core/constants.py` to a `config` package using typed constants.
- **Environment**: Maintain compatibility with current environment variables (e.g., `ORCID_CLIENT_ID`, `BASE_API_URL`).

### 4. Data Models
- Define strict Go structs for:
    - Crossref API Responses (Internal).
    - Frontend Result Items (Public).
    - ORCID Profile Info.
- Leverage Go's `json` tags to handle the transition from Python's dynamic dictionaries to typed structs.

### 5. Static Assets
- Replication of the fingerprinting logic:
    - Maintain the static manifest.
    - Implement a middleware to handle the `_serve_static` logic (matching hashed names to original files).

## Migration Steps

### Phase 1: Foundation
1. Initialize Go project structure.
2. Set up configuration management and environment loading.
3. Implement base middleares (CORS, Logging, ProxyFix-equivalent).

### Phase 2: Data & Services
1. Define unified Data Models.
2. Port the Search Service (API interaction & data parsing).
3. Port the Auth Service and Session management.

### Phase 3: Routing & UI
1. Implement the full Blueprint routing map.
2. Port Jinja2 templates to Go `html/template`.
3. Implement the specific "Splash" and "Results" logic.

### Phase 4: Verification
1. Parallel testing: Run both Python and Go versions against the same inputs.
2. Validation of CSV output parity.
3. Load testing to verify Go's performance benefits.

## Risks & Considerations
- **Session Persistence**: Flask's signed cookies are session-based; Go's implementation will need a consistent strategy (JWT or Statefull Store).
- **Data Parsing**: Python's `None` and `NaN` handling differs from Go's `nil` and `omitempty`. Careful attention to optional API fields is required.
- **Error Handling**: Translate Python's `try/except` blocks into explicit Go `if err != nil` patterns.

# AGENTS.md

This repository contains a Python FastAPI backend in `backend/` and a React/Vite frontend in `frontend/`.

## Project focus

The Python backend is the primary codebase to follow for server-side changes.

- Framework: FastAPI
- Async database driver: Motor for MongoDB Atlas
- Validation: Pydantic v2
- Settings: `app.config.Settings` via `pydantic-settings`
- Authentication: JWT helpers in the backend utilities

## Key backend entry points

- `backend/app/config.py` — environment-backed application settings
- `backend/app/database/connection.py` — singleton MongoDB client and dependency accessors
- `backend/app/utils/dependencies.py` — reusable FastAPI dependency helpers
- `backend/requirements.txt` — backend dependency list

## Working conventions

1. Keep backend code under `backend/app/`.
2. Prefer the existing layered structure:
   - `routers/` for API endpoints
   - `schemas/` for request/response models
   - `services/` for business logic
   - `models/` for document-shaping helpers or lightweight data representations
   - `utils/` for shared dependencies and security helpers
3. Use `Settings` from `app.config` instead of reading environment variables directly.
4. Use `get_database()` and the existing async database singleton rather than creating ad-hoc Mongo clients.
5. Prefer Pydantic schemas for API contracts and validation.
6. Keep the backend dependency footprint aligned with `backend/requirements.txt`.

## Preferred development workflow

From the backend directory:

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

If you need to inspect or modify configuration, check the `.env` values that feed `Settings` in `backend/app/config.py`.

## Agent guidance

- When adding a new endpoint, place the route in the routers package, validate input with a schema, and keep side effects or business logic in services.
- When adding a new config value, update the `Settings` model in `backend/app/config.py` and keep the default behavior documented.
- When working on auth or security, follow the existing JWT and dependency patterns instead of introducing a different auth flow.
- Do not convert the backend to a synchronous ORM-based pattern unless the repo explicitly changes direction; the current stack is FastAPI + Motor + Pydantic.

## Relevant docs

- [backend/README.md](backend/README.md)
- [backend/requirements.txt](backend/requirements.txt)
- [backend/app/config.py](backend/app/config.py)
- [backend/app/database/connection.py](backend/app/database/connection.py)

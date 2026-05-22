# twitter-brown-fastapi – iRails Backend Agent Instructions

## Stack

- Python 3.11.x currently used in this repo because `irails` is installed there
- iRails 1.6.x as the FastAPI MVC framework
- FastAPI under the hood for HTTP routing and request parsing
- SQLAlchemy 2.x in synchronous mode with `psycopg2`
- Alembic through the iRails project layout in `data/alembic/`
- PyJWT for JWT creation and verification
- bcrypt for password hashing
- redis-py for JWT blacklist storage on sign-out
- Pydantic for request validation at the controller boundary

## Commands

```bash
# Development
cd twitter-brown-fastapi
python main.py

# iRails CLI (run inside this directory)
irails run --host 0.0.0.0 --port 8000
irails migrate
irails test
```

## Project Layout

```text
twitter-brown-fastapi/
├── main.py                     # iRails app bootstrap
├── common/                     # shared auth, settings, response helpers
├── apps/
│   ├── authentication/
│   │   ├── manifest.yaml
│   │   ├── controllers/
│   │   └── services/
│   ├── users/
│   │   ├── manifest.yaml
│   │   ├── controllers/
│   │   ├── models/
│   │   └── services/
│   └── posts/
│       ├── manifest.yaml
│       ├── controllers/
│       ├── models/
│       └── services/
├── configs/
│   ├── general.yaml
│   ├── database.yaml
│   ├── authencation.yaml
│   └── alembic.ini
├── data/alembic/
├── public/
└── uploads/
```

## Architecture

- iRails loads apps from `apps/*/manifest.yaml`.
- `manifest.yaml` must list the packages that need importing. In this repo that means `models`, `services`, and `controllers` where applicable.
- Package `__init__.py` files must import concrete modules. iRails imports package roots, not every file automatically.
- Controllers own HTTP parsing and response shape.
- Services own DB reads, writes, and serialization helpers.
- Models map directly to the shared PostgreSQL schema from the root `CLAUDE.md`.
- Shared cross-app code belongs in `common/`.

## Routing Conventions

- Use `@route(path="/api/{controller}", auth="none")` for API controllers.
- Use `@api.get`, `@api.post`, `@api.patch`, `@api.delete` for actions.
- Collection root routes must use `/`, not an empty string.
- Keep controller names aligned with desired path names:
  - `AuthController` → `/api/auth`
  - `UsersController` → `/api/users`
  - `PostsController` → `/api/posts`

## Authentication Conventions

- JWT algorithm: HS256
- JWT expiry: 7 days
- JWT blacklist keys stored in Redis with remaining TTL on sign-out
- Password hashing: bcrypt cost 12+
- Do not use iRails Casbin auth for API authorization in this project. Route auth stays `none`; controller methods enforce bearer-token auth with helpers from `common/auth.py`.

## Response Conventions

- Success envelope:

```json
{ "data": { } }
{ "data": [], "meta": { "page": 1, "limit": 20, "total": 0 } }
```

- Error envelope:

```json
{ "error": { "code": "SNAKE_CASE_CODE", "message": "Human readable", "details": {} } }
```

- JSON keys must remain `snake_case`.
- Delete endpoints should return `204` with no body.

## Model Conventions

- Use PostgreSQL UUID columns via `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)`.
- All timestamps must be timezone-aware.
- Keep table names exactly aligned with the shared schema: `users`, `posts`, `likes`, `reposts`, `comments`, `follows`.
- Keep schema-compatible unique constraints for like/repost/follow pairs.

## App Responsibilities

### authentication

- Auth endpoints: signup, signin, signout, forgot-password, reset-password
- No DB models in this app right now
- Uses `users.User` through the service layer

### users

- Owns `User` and `Follow` models
- Owns public profile, me/profile update, follow/unfollow, followers/following endpoints

### posts

- Owns `Post`, `Like`, `Repost`, `Comment` models
- Owns feed, post CRUD, likes, reposts, and comments endpoints

## Important iRails Notes

- iRails imports config at module import time.
- `main.py` contains a small `NullTranslations` guard because iRails can fail before translations are loaded.
- If you add a new app, create `manifest.yaml`, package `__init__.py` files, and update `configs/general.yaml` `app.enabled`.
- Missing `views/` folders are acceptable for this API-only project.

## Database / Environment

- Default database URL in this scaffold:

```text
postgresql+psycopg2://postgres:postgres@localhost:5432/x_clone_dev
```

- Default Redis URL in helpers:

```text
redis://localhost:6379/0
```

- If Postgres is not running, iRails will fail during startup while testing the DB connection.

## What To Preserve

- API contract from the repo root `CLAUDE.md`
- Snake_case JSON keys
- UUID primary keys
- UTC timestamps
- Shared endpoint paths and status codes across Node.js, FastAPI, and Django backends

## What Not To Do

- Do not introduce async SQLAlchemy patterns into this project unless the whole iRails setup is deliberately migrated.
- Do not move logic into templates or HTML views.
- Do not return raw ORM models directly from controllers.
- Do not use camelCase in JSON responses.

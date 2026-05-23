# twitter-brown-fastapi (iRails)

FastAPI backend implemented with iRails for the X Clone monorepo.

## Requirements

- Python 3.11
- PostgreSQL + Redis running (from repo root)

```bash
cd /home/rtoledo/www/x_clone
docker compose up -d postgres redis
```

## Project Setup

```bash
cd x_irails_fastapi
asdf exec python -m pip install -r requirements.txt
```

## Useful Commands

### Run server

```bash
cd x_irails_fastapi
asdf exec python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Database migration (upgrade)

```bash
cd x_irails_fastapi
asdf exec python -m alembic -c configs/alembic.ini upgrade head
```

### Database migration (downgrade)

```bash
cd x_irails_fastapi
asdf exec python -m alembic -c configs/alembic.ini downgrade -1
```

### Check Alembic revision

```bash
cd x_irails_fastapi
asdf exec python -m alembic -c configs/alembic.ini current
```

### Run with iRails directly

```bash
cd x_irails_fastapi
/Users/rodrigotoledo/.asdf/installs/python/3.11.9/bin/irails --help
```

The `irails` package is installed, but this machine does not currently have an
asdf shim named `irails`, so `irails migrate -u` may print `command not found`.
Use the Alembic commands above for migrations.

## Quick Health Checks

### Check config URL used by Alembic

```bash
cd x_irails_fastapi
asdf exec python -c "from alembic.config import Config; c=Config('configs/alembic.ini'); print(c.get_main_option('sqlalchemy.url'))"
```

Expected (local):

```text
postgresql+psycopg2://postgres:postgres@localhost:5432/postgres
```

### Check current migration file(s)

```bash
cd x_irails_fastapi
ls -1 data/alembic/versions
```

## Troubleshooting

### `requirements.txt` not found

Run commands inside this directory:

```bash
cd x_irails_fastapi
```

### `irails: command not found`

Use Alembic through the pinned asdf Python:

```bash
asdf exec python -m alembic -c configs/alembic.ini upgrade head
```

### Postgres auth warning during migration check

Ensure this file has a real password (not `***`):

- `configs/alembic.ini`

And verify `configs/database.yaml` uses the same credentials as your running Postgres.

### Check the pinned Python

```bash
cd x_irails_fastapi
asdf exec python --version
asdf exec python -m alembic -c configs/alembic.ini current
```

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
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Useful Commands

### Run server

```bash
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
irails run --host 0.0.0.0 --port 8000
```

### Database migration (upgrade)

```bash
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
irails migrate -u
```

### Database migration (downgrade)

```bash
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
irails migrate -d
```

### Check Alembic revision

```bash
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
alembic -c configs/alembic.ini current
```

### Run with global iRails (if you are not using venv)

```bash
cd twitter-brown-fastapi
irails run --host 0.0.0.0 --port 8000
irails migrate -u
```

## Quick Health Checks

### Check config URL used by Alembic

```bash
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
python3 -c "from alembic.config import Config; c=Config('configs/alembic.ini'); print(c.get_main_option('sqlalchemy.url'))"
```

Expected (local):

```text
postgresql+psycopg2://postgres:postgres@localhost:5432/x_clone_dev
```

### Check current migration file(s)

```bash
cd twitter-brown-fastapi
ls -1 data/alembic/versions
```

## Troubleshooting

### `requirements.txt` not found

Run commands inside this directory:

```bash
cd twitter-brown-fastapi
```

### `irails migrate` only prints usage

That is expected without a flag. Use:

- `-u` for upgrade
- `-d` for downgrade

### Postgres auth warning during migration check

Ensure this file has a real password (not `***`):

- `configs/alembic.ini`

And verify `configs/database.yaml` uses the same credentials as your running Postgres.

### `source venv/bin/activate` behaves unexpectedly

```bash
cd twitter-brown-fastapi
python3 -m venv venv
source venv/bin/activate
python --version
irails --help
```

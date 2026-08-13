#!/usr/bin/env sh
set -eu

alembic upgrade head
python -m app.cli seed-rbac
python -m app.cli seed-demo
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

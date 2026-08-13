#!/usr/bin/env sh
set -eu

alembic upgrade head
python -m app.cli seed-rbac

case "${SEED_DEMO_DATA:-true}" in
    1|true|TRUE|yes|YES)
        python -m app.cli seed-demo
        ;;
esac

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

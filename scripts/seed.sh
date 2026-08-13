#!/usr/bin/env sh
set -eu

docker compose run --rm backend python -m app.cli seed-rbac


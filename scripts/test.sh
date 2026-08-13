#!/usr/bin/env sh
set -eu

docker compose run --rm backend pytest
docker compose run --rm frontend pnpm test -- --run


#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Arquivo .env criado. Revise as credenciais antes de uso fora do desenvolvimento."
fi

docker compose up --build


#!/usr/bin/env bash
# Start the local stack, initialize the database, and expose helpful curl hints.
set -euo pipefail

if [ ! -f .env ]; then
  cp .env.example .env
fi

set -a
source .env
set +a

docker compose up -d --build

echo "Waiting for Postgres to be ready..."
for i in {1..30}; do
  if docker compose exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  sleep 1
  if [ "$i" -eq 30 ]; then
    echo "Postgres did not become ready in time" >&2
    exit 1
  fi
done

docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init.sql

echo "API running at http://localhost:8000"
echo "Try:"
echo "  curl -X POST \"http://localhost:8000/ingest?mode=mock\""
echo "  curl \"http://localhost:8000/latest?nace=47&metric=uidxnom\""

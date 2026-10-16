#!/usr/bin/env bash
# Runs ON THE SERVER (deploy.sh calls it). Order matters: migrate BEFORE the new
# app starts, otherwise the app (and its startup job) can hit missing tables/columns.
set -euo pipefail
cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml"

# First deploy only: create the server's secrets. They never leave the server.
if [ ! -f .env ]; then
  : "${DOMAIN:?DOMAIN must be set on the first deploy}"
  (umask 077 && printf 'DOMAIN=%s\nPOSTGRES_PASSWORD=%s\n' "$DOMAIN" "$(openssl rand -hex 24)" > .env)
  echo "  created deploy/.env with a new random database password"
fi

echo "  1/4 database + cache";  $COMPOSE up -d --wait db redis
echo "  2/4 build";             $COMPOSE build backend
echo "  3/4 migrate + seed";    $COMPOSE run --rm --no-deps backend alembic upgrade head
                                $COMPOSE run --rm --no-deps backend python -m app.seed
echo "  4/4 start everything";  $COMPOSE up -d --wait # returns only when every container is healthy

docker image prune -f > /dev/null # drop old image layers so the small disk doesn't fill up

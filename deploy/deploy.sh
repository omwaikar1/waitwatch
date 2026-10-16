#!/usr/bin/env bash
# Deploy the backend to the server. Run from your Mac:
#   deploy/deploy.sh <server-ip>
# Safe to re-run: it copies the latest code, migrates, seeds and restarts.
set -euo pipefail

IP="${1:?usage: deploy/deploy.sh <server-ip>}"
HOST="ubuntu@$IP"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="${IP//./-}.sslip.io" # 1.2.3.4 -> 1-2-3-4.sslip.io

echo "→ Waiting for the server's first-boot setup (cloud-init.sh) to finish"
ssh "$HOST" 'until [ -f /var/lib/waitwatch-ready ]; do sleep 5; done'

echo "→ Copying code to $HOST"
# --delete removes files deleted locally; excluded files (like the server's .env) are kept
rsync -az --delete \
  --exclude '.env' --exclude '__pycache__' --exclude '.pytest_cache' --exclude '*.md' \
  "$ROOT/backend" "$ROOT/deploy" "$HOST:~/waitwatch/"

echo "→ Building and starting on the server"
ssh "$HOST" "DOMAIN=$DOMAIN bash ~/waitwatch/deploy/server-up.sh"

echo "✓ Deployed: https://$DOMAIN/health"

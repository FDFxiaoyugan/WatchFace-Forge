#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
TEMP_FILE="$PROJECT_DIR/.env.tmp"

umask 077
API_KEY="wff_$(openssl rand -hex 24)"

if test -f "$ENV_FILE"; then
  grep -v '^WFF_API_KEYS=' "$ENV_FILE" >"$TEMP_FILE" || true
else
  : >"$TEMP_FILE"
fi
printf 'WFF_API_KEYS=%s\n' "$API_KEY" >>"$TEMP_FILE"
mv "$TEMP_FILE" "$ENV_FILE"

printf 'WFF API key written to %s\n' "$ENV_FILE"
printf '%s\n' "$API_KEY"

#!/bin/bash
# Riruru auto-restart wrapper: keeps the bot alive across crashes/kills.
cd /root/riruru
# Load secrets from .env (gitignored, never committed)
set -a
[ -f .env ] && source .env
set +a
echo $$ > /tmp/opencode/runner.pid
while true; do
    echo "[runner] starting bot at $(date -u +%FT%TZ)"
    python3 -u riruru.py >> /tmp/opencode/riruru_test.log 2>&1
    echo "[runner] bot exited (code $?) at $(date -u +%FT%TZ) — restarting in 5s"
    sleep 5
done

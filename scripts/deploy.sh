#!/bin/bash
set -e

COMPOSE="docker compose"

echo ""
echo "════════════════════════════════════════"
echo "  RAG Deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════"

# ── 1. Skip git pull (Code is uploaded via SCP) ────────────────────────
echo ""
echo ">>> [1/6] Code pushed locally, skipping git pull..."
# git pull origin main

# ── 2. Build frontend dist ────────────────────────────────
echo ""
echo ">>> [2/6] Building frontend..."
docker build -t rag-frontend-builder ./frontend
docker run --rm -v "$(pwd)/frontend/dist:/out" rag-frontend-builder \
    sh -c "cp -r /app/dist/. /out/"

# ── 3. Rebuild backend and chatbot ──────────────────────────────
# Qdrant and Postgres are NEVER restarted (data safety)
echo ""
echo ">>> [3/6] Rebuilding backend and chatbot images..."
$COMPOSE build backend rag-chatbot

# ── 4. Restart backend, chatbot + nginx only ──────────────────────
echo ""
echo ">>> [4/6] Restarting backend, chatbot and nginx..."
$COMPOSE up -d --no-deps backend rag-chatbot nginx

# ── 5. Wait for backend healthy ───────────────────────────
echo ""
echo ">>> [5/6] Waiting for backend to be healthy..."
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    STATUS=$($COMPOSE ps backend --format json 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health','unknown'))" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "healthy" ]; then
        echo "    Backend healthy after ${WAITED}s"
        break
    fi
    echo "    Waiting... (${WAITED}s/${MAX_WAIT}s) status: $STATUS"
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "    WARNING: Backend not healthy after ${MAX_WAIT}s"
    echo "    Check: docker compose logs backend --tail=40"
fi

# ── 6. Cleanup + status ───────────────────────────────────
echo ""
echo ">>> [6/6] Cleaning up old images..."
docker image prune -f

echo ""
echo "════════════════════════════════════════"
echo "  Container status:"
$COMPOSE ps
echo ""
echo "  Run smoke tests: ./scripts/smoke_test.sh"
echo "════════════════════════════════════════"

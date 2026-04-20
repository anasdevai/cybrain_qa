#!/bin/bash
# hotpatch.sh — Upload only changed files and restart backend + nginx
# Usage: bash hotpatch.sh [server_ip] [ssh_key_path]
# Example: bash hotpatch.sh 65.21.244.158 ~/.ssh/id_ed25519

set -e

SERVER_IP="${1:-65.21.244.158}"
SSH_KEY="${2:-$HOME/.ssh/id_ed25519}"
REMOTE_USER="root"
REMOTE_PATH="/opt/hybrid-rag/Main"
COMPOSE="docker compose"

echo ""
echo "════════════════════════════════════════"
echo "  Hotpatch Deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Server: $SERVER_IP"
echo "════════════════════════════════════════"

SCP="scp -i $SSH_KEY -o StrictHostKeyChecking=no"
SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$SERVER_IP"

# ── 1. Upload changed backend files ──────────────────────────────────────
echo ""
echo ">>> [1/4] Uploading changed files..."
$SCP chain/rag_chain.py   "$REMOTE_USER@$SERVER_IP:$REMOTE_PATH/chain/rag_chain.py"
$SCP main.py               "$REMOTE_USER@$SERVER_IP:$REMOTE_PATH/main.py"

# ── 2. Upload changed frontend file ──────────────────────────────────────
$SCP frontend/src/App.jsx  "$REMOTE_USER@$SERVER_IP:$REMOTE_PATH/frontend/src/App.jsx"
echo "    Uploaded: chain/rag_chain.py, main.py, frontend/src/App.jsx"

# ── 3. Rebuild frontend dist + backend image, restart containers ─────────
echo ""
echo ">>> [2/4] Rebuilding frontend dist on server..."
$SSH "cd $REMOTE_PATH && \
  docker build -t rag-frontend-builder ./frontend && \
  docker run --rm -v \"\$(pwd)/frontend/dist:/out\" rag-frontend-builder \
    sh -c 'cp -r /app/dist/. /out/'"

echo ""
echo ">>> [3/4] Rebuilding backend image and restarting..."
$SSH "cd $REMOTE_PATH && \
  $COMPOSE build backend && \
  $COMPOSE up -d --no-deps backend nginx"

# ── 4. Wait for healthy ───────────────────────────────────────────────────
echo ""
echo ">>> [4/4] Waiting for backend to be healthy..."
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
  STATUS=$($SSH "cd $REMOTE_PATH && $COMPOSE ps backend --format json 2>/dev/null | \
    python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('Health','unknown'))\" 2>/dev/null || echo unknown")
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
  echo "    Check: ssh $REMOTE_USER@$SERVER_IP 'cd $REMOTE_PATH && docker compose logs backend --tail=40'"
fi

echo ""
echo "════════════════════════════════════════"
echo "  Done. Smoke test:"
echo "  curl http://$SERVER_IP:8085/health"
echo "════════════════════════════════════════"

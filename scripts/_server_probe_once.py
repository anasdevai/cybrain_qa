#!/usr/bin/env python3
"""One-off remote diagnostics via SSH. Do not commit secrets."""
import os
import sys

HOST = os.environ.get("DEBUG_SSH_HOST", "65.21.244.158")
USER = os.environ.get("DEBUG_SSH_USER", "root")
PWD = os.environ.get("DEBUG_SSH_PASS", "")

SCRIPT = r"""
set -euo pipefail
echo "========== 127.0.0.1:8000 /api/stats =========="
curl -sS --connect-timeout 5 http://127.0.0.1:8000/api/stats || echo "stats_failed"
echo
echo "========== GET /api/sops (count) =========="
curl -sS http://127.0.0.1:8000/api/sops | head -c 2000
echo
echo
echo "========== GET /api/public/sops (default effective) =========="
curl -sS "http://127.0.0.1:8000/api/public/sops" | head -c 2000
echo
echo
echo "========== GET /api/public/sops?status=all =========="
curl -sS "http://127.0.0.1:8000/api/public/sops?status=all" | head -c 2000
echo
echo
echo "========== Qdrant local 127.0.0.1:6333 root =========="
curl -sS -o /dev/null -w "http_code=%{http_code}\n" --connect-timeout 3 http://127.0.0.1:6333/ || echo "curl_6333_failed"
echo
echo "========== Processes: qdrant / uvicorn =========="
pgrep -af qdrant 2>/dev/null || echo "no_qdrant_process"
pgrep -af uvicorn 2>/dev/null | head -3
echo
echo "========== systemd: qdrant docker backend =========="
systemctl is-active qdrant 2>/dev/null || echo "qdrant_service_inactive"
systemctl is-active docker 2>/dev/null || true
systemctl is-active cybrain-backend 2>/dev/null || echo "cybrain_backend_service_unknown"
echo
echo "========== journal cybrain-backend (last 40) =========="
journalctl -u cybrain-backend -n 40 --no-pager 2>/dev/null || echo "no_journal_cybrain"
echo
echo "========== .env (names only, values redacted) =========="
for f in /root/cybrain-backend/.env /var/www/cybrain/../.env; do
  if [ -f "$f" ]; then echo "FILE: $f"; grep -E '^(DATABASE_URL|QDRANT_URL|QDRANT_API_KEY|CHATBOT_USE_LOCAL_DB|CHAT_QUERY_TIMEOUT|GEMINI|POSTGRES_)' "$f" | sed 's/=.*/=<redacted>/' || true; fi
done
echo
echo "========== POST /api/ai/query timing (one short question) =========="
curl -sS -o /tmp/aiq.json -w "curl_time_total_sec=%{time_total}\n" -X POST http://127.0.0.1:8000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is our procedure for calibration?"}' || true
head -c 1200 /tmp/aiq.json 2>/dev/null; echo; echo
python3 - <<'PY' 2>/dev/null || true
import json
try:
  with open("/tmp/aiq.json") as f: j = json.load(f)
  print("routed_to:", j.get("routed_to"))
  print("retrieval_stats:", j.get("retrieval_stats"))
  print("answer_len:", len((j.get("answer") or "")))
except Exception as e:
  print("parse_err", e)
PY
echo
echo "========== PostgreSQL: table counts (from DATABASE_URL) =========="
if [ -f /root/cybrain-backend/.env ]; then
  set -a
  # shellcheck disable=SC1091
  source /root/cybrain-backend/.env 2>/dev/null || true
  set +a
  export DATABASE_URL
  DBURL="${DATABASE_URL:-}"
  if [ -n "$DBURL" ]; then
    python3 - <<'PY' || true
import os, re, subprocess, sys
u = os.environ.get("DATABASE_URL", "")
# sqlalchemy URLs: postgresql+psycopg://user:pass@host:port/db
u = re.sub(r"^postgresql\+[a-z0-9]+", "postgresql", u, flags=re.I)
# psycopg3 libpq: postgresql://...
if "@" in u and u.startswith("postgresql"):
    # Use psql with URI if available
    p = subprocess.run(
        ["psql", u, "-At", "-c",
         "SELECT 'sops', count(*)::text FROM sops UNION ALL SELECT 'knowledge_chunks', count(*)::text FROM knowledge_chunks "
         "UNION ALL SELECT 'sop_versions', count(*)::text FROM sop_versions UNION ALL SELECT 'chat_sessions', count(*)::text FROM chat_sessions;"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    print(p.stdout or p.stderr or p.returncode)
else:
    print("no_parsable_DATABASE_URL", file=sys.stderr)
PY
  else
    echo "no DATABASE_URL in env after source"
  fi
fi
echo
echo "========== Sample: sop_versions.external_status for current rows =========="
if [ -f /root/cybrain-backend/.env ]; then
  set -a; source /root/cybrain-backend/.env 2>/dev/null || true; set +a
  export DATABASE_URL
  python3 - <<'PY' 2>/dev/null || true
import os, re, subprocess
u = os.environ.get("DATABASE_URL", "")
u = re.sub(r"^postgresql\+[a-z0-9]+", "postgresql", u, flags=re.I)
if "@" in u and u.startswith("postgresql"):
    sql = "SELECT s.sop_number, s.is_active, v.external_status FROM sops s LEFT JOIN sop_versions v ON v.id = s.current_version_id LIMIT 20;"
    p = subprocess.run(["psql", u, "-c", sql], capture_output=True, text=True, timeout=15)
    print(p.stdout)
PY
fi
echo
echo "========== DONE =========="
"""

def main() -> None:
    try:
        import paramiko
    except ImportError:
        print("Install paramiko: pip install paramiko", file=sys.stderr)
        sys.exit(1)
    if not PWD:
        print("Set DEBUG_SSH_PASS or pass as env", file=sys.stderr)
        sys.exit(1)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname=HOST, username=USER, password=PWD, timeout=30)
    remote_path = "/tmp/cybrain_probe.sh"
    sftp = c.open_sftp()
    with sftp.file(remote_path, "w") as f:
        f.write(SCRIPT.lstrip("\n"))
    sftp.chmod(remote_path, 0o700)
    sftp.close()
    stdin, stdout, stderr = c.exec_command(f"bash {remote_path}", timeout=240)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    print(out)
    if err.strip():
        print("--- stderr ---", file=sys.stderr)
        print(err, file=sys.stderr)
    c.close()

if __name__ == "__main__":
    main()

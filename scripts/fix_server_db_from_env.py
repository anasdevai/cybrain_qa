#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def sql_quote(value: str) -> str:
    return value.replace("'", "''")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.is_file():
        raise SystemExit("Missing root .env")

    cfg = load_env(env_path)
    db_user = cfg.get("POSTGRES_USER", "postgres")
    db_pass = cfg.get("POSTGRES_PASSWORD", "")
    db_name = cfg.get("POSTGRES_DB", "server_db")
    if not db_pass:
        raise SystemExit("POSTGRES_PASSWORD is missing in .env")

    ssh_pass = os.environ.get("DEBUG_SSH_PASS") or os.environ.get("DEPLOY_SSH_PASS")
    if not ssh_pass:
        raise SystemExit("Set DEBUG_SSH_PASS or DEPLOY_SSH_PASS")

    database_url = f"postgresql+psycopg://{db_user}:{db_pass}@127.0.0.1:5432/{db_name}"
    user_sql = sql_quote(db_user)
    pass_sql = sql_quote(db_pass)
    db_sql = sql_quote(db_name)

    remote_cmd = f"""
set -euo pipefail
sudo -u postgres psql -c "CREATE USER \\"{user_sql}\\" WITH PASSWORD '{pass_sql}';" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER \\"{user_sql}\\" WITH PASSWORD '{pass_sql}';"
sudo -u postgres psql -c "CREATE DATABASE \\"{db_sql}\\" OWNER \\"{user_sql}\\";" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \\"{db_sql}\\" TO \\"{user_sql}\\";"
if [ -f /root/cybrain-backend/.env ]; then
  grep -v '^DATABASE_URL=' /root/cybrain-backend/.env > /tmp/cybrain_env_fixed || true
else
  : > /tmp/cybrain_env_fixed
fi
echo "DATABASE_URL={database_url}" >> /tmp/cybrain_env_fixed
mv /tmp/cybrain_env_fixed /root/cybrain-backend/.env
chmod 600 /root/cybrain-backend/.env
cd /root/cybrain-backend
./venv/bin/pip install -q 'psycopg[binary]>=3.1.0'
systemctl restart cybrain-backend
sleep 4
curl -sS http://127.0.0.1:8000/api/health
echo
systemctl is-active cybrain-backend
"""

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="65.21.244.158", username="root", password=ssh_pass, timeout=30)
    _, stdout, stderr = client.exec_command(remote_cmd, timeout=300)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    print(out, end="")
    if err.strip():
        print(err, file=sys.stderr, end="")
    rc = stdout.channel.recv_exit_status()
    client.close()
    if rc != 0:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()

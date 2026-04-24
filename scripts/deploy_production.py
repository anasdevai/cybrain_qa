#!/usr/bin/env python3
"""
Deploy backend + frontend dist to the production server over SSH (paramiko).
Does not print or commit secrets. Set DEPLOY_SSH_PASS (or DEBUG_SSH_PASS) in the environment.

Usage (from repo root):
  set DEPLOY_SSH_PASS=...
  python scripts/deploy_production.py
"""
from __future__ import annotations

import os
import sys
import shutil
import tarfile
import tempfile
import subprocess
from pathlib import Path

HOST = os.environ.get("DEPLOY_SSH_HOST", "65.21.244.158")
USER = os.environ.get("DEPLOY_SSH_USER", "root")
PWD = os.environ.get("DEPLOY_SSH_PASS") or os.environ.get("DEBUG_SSH_PASS", "")

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"

REMOTE_BACKEND_TAR = "/tmp/cybrain_backend_deploy.tgz"
REMOTE_FRONT_TAR = "/tmp/cybrain_frontend_deploy.tgz"

NGINX_BODY = r"""server {
    listen 80;
    server_name 65.21.244.158;

    client_max_body_size 50M;

    root /var/www/cybrain;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
    }
}
"""

def _tar_filter(ti: tarfile.TarInfo) -> tarfile.TarInfo | None:
    p = Path(ti.name)
    if any(part in ("__pycache__", "venv", ".venv", "node_modules", ".git") for part in p.parts):
        return None
    if p.suffix == ".pyc" or p.name.endswith(".pyo"):
        return None
    if any(x in p.parts for x in (".hf-cache", "models", ".cache")):
        return None
    if p.name == ".env" and ti.isfile():
        return None
    return ti


def _make_backend_tar(path: Path) -> Path:
    tdir = Path(tempfile.mkdtemp())
    out = tdir / "backend.tgz"
    with tarfile.open(out, "w:gz", format=tarfile.GNU_FORMAT) as tar:
        tar.add(
            path,
            arcname="cybrain-backend",
            filter=_tar_filter,
        )
    return out


def _make_frontend_tar(dist: Path) -> Path:
    if not dist.is_dir():
        raise SystemExit(f"Missing {dist} — run npm run build in frontend/ first")
    tdir = Path(tempfile.mkdtemp())
    out = tdir / "frontend.tgz"
    with tarfile.open(out, "w:gz", format=tarfile.GNU_FORMAT) as tar:
        for f in dist.rglob("*"):
            if f.is_file():
                tar.add(f, arcname=f.relative_to(dist))
    return out


def _sftp_put(sftp, local: str, remote: str) -> None:
    sftp.put(local, remote, confirm=True)
    sftp.chmod(remote, 0o600)


def main() -> None:
    if not PWD:
        print("Set DEPLOY_SSH_PASS or DEBUG_SSH_PASS", file=sys.stderr)
        sys.exit(1)
    if not BACKEND.is_dir():
        print(f"Missing {BACKEND}", file=sys.stderr)
        sys.exit(1)

    print("[local] npm run build (production env)")
    env = {**os.environ, "CI": "1"}
    npm = shutil.which("npm") or "npm"
    subprocess.run(
        [npm, "run", "build"],
        cwd=str(FRONTEND),
        env=env,
        check=True,
    )
    if not DIST.is_dir():
        raise SystemExit("frontend build did not create dist/")

    print("[local] pack archives")
    btar = _make_backend_tar(BACKEND)
    ftar = _make_frontend_tar(DIST)
    try:
        import paramiko
    except ImportError:
        print("pip install paramiko", file=sys.stderr)
        sys.exit(1)

    print(f"[remote] {USER}@{HOST} upload + install")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname=HOST, username=USER, password=PWD, timeout=60)
    tr = c.get_transport()
    if tr:
        tr.set_keepalive(30)
    sftp = c.open_sftp()
    ch = sftp.get_channel()
    if ch is not None:
        ch.settimeout(900.0)
    for p in (REMOTE_BACKEND_TAR, REMOTE_FRONT_TAR):
        try:
            sftp.remove(p)
        except FileNotFoundError:
            pass
        except OSError:
            pass
    _sftp_put(sftp, str(btar), REMOTE_BACKEND_TAR)
    _sftp_put(sftp, str(ftar), REMOTE_FRONT_TAR)
    with sftp.open("/tmp/cybrain.nginx", "w") as nginxf:
        nginxf.write(NGINX_BODY.encode("utf-8"))
    sftp.chmod("/tmp/cybrain.nginx", 0o644)
    # Optional: push local .env (overrides server DB creds — use only when server DB matches local)
    if os.environ.get("DEPLOY_PUSH_ROOT_ENV", "").lower() in ("1", "true", "yes") and (ROOT / ".env").is_file():
        with sftp.open("/tmp/cybrain.env.incoming", "w") as eout:
            eout.write((ROOT / ".env").read_bytes())
        sftp.chmod("/tmp/cybrain.env.incoming", 0o600)
    sftp.close()

    remote = r"""
set -euo pipefail
# Preserve live database config and secrets
ENV_BAK="/tmp/cybrain.env.restore.$$"
if [ -f /root/cybrain-backend/.env ]; then
  cp -a /root/cybrain-backend/.env "$ENV_BAK"
fi
VENV_BAK="/tmp/cybrain-venv-bak.$$"
if [ -d /root/cybrain-backend/venv ]; then
  cp -a /root/cybrain-backend/venv "$VENV_BAK"
fi

mkdir -p /root
cd /root
rm -rf /root/cybrain-backend
tar xzf """ + REMOTE_BACKEND_TAR + r""" -C /root
if [ -d "$VENV_BAK" ]; then
  rm -rf /root/cybrain-backend/venv
  mv "$VENV_BAK" /root/cybrain-backend/venv
fi
if [ -f /tmp/cybrain.env.incoming ]; then
  mv -f /tmp/cybrain.env.incoming /root/cybrain-backend/.env
  chmod 600 /root/cybrain-backend/.env
elif [ -f "$ENV_BAK" ]; then
  mv "$ENV_BAK" /root/cybrain-backend/.env
fi
cd /root/cybrain-backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
./venv/bin/pip install -q -U pip
./venv/bin/pip install -q -r requirements.txt
install -m 644 /tmp/cybrain.nginx /etc/nginx/sites-available/cybrain
ln -sf /etc/nginx/sites-available/cybrain /etc/nginx/sites-enabled/cybrain
rm -f /etc/nginx/sites-enabled/default
systemctl restart cybrain-backend
# Model load can take 15–30s on first start; smoke test must not false-fail
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf --connect-timeout 2 http://127.0.0.1:8000/api/health >/dev/null; then
    break
  fi
  sleep 2
done
systemctl is-active cybrain-backend || true

mkdir -p /var/www/cybrain
cd /var/www/cybrain
# Atomic swap of static assets
rm -rf /var/www/cybrain.next
mkdir -p /var/www/cybrain.next
tar xzf """ + REMOTE_FRONT_TAR + r""" -C /var/www/cybrain.next
chown -R root:root /var/www/cybrain.next
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete /var/www/cybrain.next/ /var/www/cybrain/
else
  find /var/www/cybrain -mindepth 1 -delete
  cp -a /var/www/cybrain.next/. /var/www/cybrain/
fi
rm -rf /var/www/cybrain.next
nginx -t
systemctl reload nginx
echo "========== smoke =========="
curl -sS -o /dev/stdout -w "\nhttp_public_health=%{http_code}\n" --connect-timeout 5 http://127.0.0.1:8000/api/health
curl -sS -o /dev/stdout -w "\nhttp_public_nginx=%{http_code}\n" --connect-timeout 5 http://127.0.0.1/api/health
"""
    stdin, stdout, stderr = c.exec_command(remote, timeout=600)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    print(out)
    if err.strip():
        print("--- remote stderr ---", file=sys.stderr)
        print(err, file=sys.stderr)
    exit_c = stdout.channel.recv_exit_status()
    c.close()
    if exit_c != 0:
        sys.exit(exit_c)
    print("[done] Public checks: open http://%s/ and verify API http://%s/api/health" % (HOST, HOST))


if __name__ == "__main__":
    main()

"""One-shot deploy: SCP 3 files + rebuild backend + restart containers."""
import paramiko, os, sys, time

HOST     = "65.21.244.158"
USER     = "root"
PASSWORD = "Cph181ko!!"
REMOTE   = "/opt/hybrid-rag"

FILES = [
    ("chain/rag_chain.py",      f"{REMOTE}/chain/rag_chain.py"),
    ("main.py",                  f"{REMOTE}/main.py"),
    ("frontend/src/App.jsx",     f"{REMOTE}/frontend/src/App.jsx"),
]

BASE = os.path.dirname(os.path.abspath(__file__))

def run(ssh, cmd, label=""):
    print(f"\n>>> {label or cmd[:80]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    for line in iter(stdout.readline, ""):
        print("   ", line, end="")
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        err = stderr.read().decode()
        print(f"   STDERR: {err}")
    return exit_code

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f"Connecting to {HOST}...")
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("Connected.")

# ── 1. Upload files ──────────────────────────────────────────────────────
sftp = ssh.open_sftp()
for local_rel, remote_path in FILES:
    local_abs = os.path.join(BASE, local_rel)
    print(f"  Uploading {local_rel} -> {remote_path}")
    sftp.put(local_abs, remote_path)
sftp.close()
print("Files uploaded.")

# ── 2. Rebuild frontend dist ─────────────────────────────────────────────
run(ssh,
    f"cd {REMOTE} && "
    "docker build -t rag-frontend-builder ./frontend && "
    "docker run --rm -v \"$(pwd)/frontend/dist:/out\" rag-frontend-builder "
    "sh -c 'cp -r /app/dist/. /out/'",
    "Rebuilding frontend dist")

# ── 3. Rebuild backend image ─────────────────────────────────────────────
run(ssh,
    f"cd {REMOTE} && docker compose build backend",
    "Rebuilding backend image")

# ── 4. Restart backend + nginx ───────────────────────────────────────────
run(ssh,
    f"cd {REMOTE} && docker compose up -d --no-deps backend nginx",
    "Restarting backend + nginx")

# ── 5. Wait for healthy ───────────────────────────────────────────────────
print("\n>>> Waiting for backend health...")
for i in range(24):
    time.sleep(5)
    _, out, _ = ssh.exec_command(
        f"cd {REMOTE} && docker compose ps backend --format json 2>/dev/null | "
        "python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('Health','unknown'))\" 2>/dev/null || echo unknown"
    )
    status = out.read().decode().strip()
    print(f"   [{(i+1)*5}s] status: {status}")
    if status == "healthy":
        break

# ── 6. Smoke test ─────────────────────────────────────────────────────────
run(ssh, "curl -sf http://localhost:8000/health", "Smoke test /health")

ssh.close()
print("\n════════════════════════════════════════")
print("  Deploy complete.")
print(f"  App: http://{HOST}:8085")
print("════════════════════════════════════════")

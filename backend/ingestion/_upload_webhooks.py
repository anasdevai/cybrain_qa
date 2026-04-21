"""Upload routers/webhooks.py, rebuild, restart, verify."""
import paramiko, os, time

HOST = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"
REMOTE = "/opt/hybrid-rag"
BASE = os.path.dirname(os.path.abspath(__file__))

def run(ssh, cmd, label=""):
    label = label or cmd[:70]
    print(f"\n>>> {label}")
    _, stdout, _ = ssh.exec_command(cmd, get_pty=True)
    for line in iter(stdout.readline, ""):
        print("  ", line, end="")
    code = stdout.channel.recv_exit_status()
    print(f"  [exit {code}]")
    return code

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("Connected.")

# Upload routers/webhooks.py
sftp = ssh.open_sftp()
sftp.put(os.path.join(BASE, "routers", "webhooks.py"), f"{REMOTE}/routers/webhooks.py")
print("Uploaded routers/webhooks.py")
sftp.close()

# Rebuild (fast — only COPY . . layer)
run(ssh, f"cd {REMOTE} && docker compose build backend 2>&1", "Rebuild backend")

# Restart
run(ssh, f"cd {REMOTE} && docker compose up -d --no-deps backend 2>&1", "Restart backend")

# Wait for healthy
print("\n>>> Waiting for healthy (up to 90s)...")
for i in range(18):
    time.sleep(5)
    _, out, _ = ssh.exec_command(
        "docker inspect --format='{{.State.Health.Status}}' "
        "$(cd /opt/hybrid-rag && docker compose ps -q backend) 2>/dev/null || echo unknown"
    )
    status = out.read().decode().strip()
    print(f"  [{(i+1)*5}s] {status}")
    if status == "healthy":
        print("\n  HEALTHY!")
        run(ssh, "curl -sf http://localhost:8000/health && echo ' -> OK'", "Smoke test")
        break
else:
    run(ssh, f"cd {REMOTE} && docker compose logs --tail=20 backend 2>&1", "Backend logs")

ssh.close()
print("\nDone.")

import paramiko, time, sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('65.21.244.158', username='root', password='Cph181ko!!', timeout=15)
print("Connected.")

def run(cmd, label):
    print(f"\n>>> {label}")
    _, out, err = ssh.exec_command(cmd, get_pty=True)
    for line in iter(out.readline, ""):
        print("  ", line, end="")
    code = out.channel.recv_exit_status()
    print(f"  [exit {code}]")
    return code

# Rebuild backend with no-cache so langchain-qdrant gets installed
run("cd /opt/hybrid-rag && docker compose build --no-cache backend 2>&1", "Rebuilding backend image (no-cache)")

# Start backend only
run("cd /opt/hybrid-rag && docker compose up -d --no-deps backend 2>&1", "Starting backend container")

# Wait for healthy
print("\n>>> Waiting for backend to be healthy (up to 120s)...")
for i in range(24):
    time.sleep(5)
    _, o, _ = ssh.exec_command("cd /opt/hybrid-rag && docker inspect --format='{{.State.Health.Status}}' $(docker compose ps -q backend) 2>/dev/null || echo unknown")
    status = o.read().decode().strip()
    print(f"  [{(i+1)*5}s] status: {status}")
    if status == "healthy":
        break

# Smoke test
run("curl -sf http://localhost:8000/health && echo OK || echo FAIL", "Smoke test /health")

# Restart nginx to pick up new frontend dist
run("cd /opt/hybrid-rag && docker compose up -d --no-deps nginx 2>&1", "Restarting nginx")

ssh.close()
print("\n════════════════════════════════")
print("  Done. http://65.21.244.158:8085")
print("════════════════════════════════")

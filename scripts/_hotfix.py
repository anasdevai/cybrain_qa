"""
_hotfix.py
Fix two issues:
1. Upload storage/runtime_sync.py (missing on server)
2. The rag_chain.py was uploaded to wrong path — fix it
3. Restart backend
"""
import paramiko
import os
import time

HOST     = "65.21.244.158"
USER     = "root"
PASSWORD = "Cph181ko!!"
REMOTE   = "/opt/hybrid-rag"
BASE     = os.path.dirname(os.path.abspath(__file__))

def run(ssh, cmd, label=""):
    label = label or cmd[:80]
    print(f"\n>>> {label}")
    _, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    for line in iter(stdout.readline, ""):
        print("  ", line, end="")
    code = stdout.channel.recv_exit_status()
    print(f"  [exit {code}]")
    return code

print(f"Connecting to {HOST}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=20)
print("Connected.\n")

sftp = ssh.open_sftp()

# Fix 1: Upload missing storage/runtime_sync.py
local = os.path.join(BASE, "storage", "runtime_sync.py")
remote = f"{REMOTE}/storage/runtime_sync.py"
print(f">>> Uploading storage/runtime_sync.py -> {remote}")
sftp.put(local, remote)
print("  Done.")

# Fix 2: chain/rag_chain.py was already uploaded correctly in previous run
# but double-check it's in the right place
local2 = os.path.join(BASE, "chain", "rag_chain.py")
remote2 = f"{REMOTE}/chain/rag_chain.py"
print(f">>> Uploading chain/rag_chain.py -> {remote2}")
sftp.put(local2, remote2)
print("  Done.")

# Also re-upload main.py to be safe
local3 = os.path.join(BASE, "main.py")
remote3 = f"{REMOTE}/main.py"
print(f">>> Uploading main.py -> {remote3}")
sftp.put(local3, remote3)
print("  Done.")

sftp.close()

# Restart backend (no rebuild needed — files are copied into running container via volume or we need to rebuild)
# Check if there's a volume mount or if files are baked into image
run(ssh, f"cd {REMOTE} && docker compose config | grep -A5 'backend:' | head -20", "Check backend config")
run(ssh, f"cd {REMOTE} && cat Dockerfile", "Check Dockerfile")

ssh.close()

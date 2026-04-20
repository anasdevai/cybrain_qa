"""
_check_and_sync.py
Check what's on the server vs local, then upload missing modules.
"""
import paramiko
import os
import stat

HOST     = "65.21.244.158"
USER     = "root"
PASSWORD = "Cph181ko!!"
REMOTE   = "/opt/hybrid-rag"
BASE     = os.path.dirname(os.path.abspath(__file__))

def run(ssh, cmd, label=""):
    label = label or cmd[:80]
    print(f"\n>>> {label}")
    _, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    lines = []
    for line in iter(stdout.readline, ""):
        print("  ", line, end="")
        lines.append(line)
    code = stdout.channel.recv_exit_status()
    print(f"  [exit {code}]")
    return code, "".join(lines)

print(f"Connecting to {HOST}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=20)
print("Connected.\n")

# Check what's on the server
run(ssh, f"ls -la {REMOTE}/", "Server root listing")
run(ssh, f"ls -la {REMOTE}/storage/ 2>/dev/null || echo 'MISSING: storage/'", "storage/ on server")
run(ssh, f"ls -la {REMOTE}/routers/ 2>/dev/null || echo 'MISSING: routers/'", "routers/ on server")
run(ssh, f"ls -la {REMOTE}/retrieval/ 2>/dev/null || echo 'MISSING: retrieval/'", "retrieval/ on server")
run(ssh, f"ls -la {REMOTE}/schemas/ 2>/dev/null || echo 'MISSING: schemas/'", "schemas/ on server")

ssh.close()

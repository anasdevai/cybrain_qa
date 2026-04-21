"""
Step 1: Check server state and set up SSH key auth.
"""
import paramiko
import sys
import os

SERVER = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

def run_cmd(ssh, cmd, print_output=True):
    """Run a command on the server and return stdout."""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if print_output:
        if out.strip():
            print(out)
        if err.strip():
            print(f"[stderr] {err}")
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {USER}@{SERVER}...")
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
    print("Connected!\n")
    
    # Check what's already on the server
    print("=" * 60)
    print("SERVER STATE CHECK")
    print("=" * 60)
    
    print("\n--- OS Info ---")
    run_cmd(ssh, "cat /etc/os-release | head -5")
    
    print("\n--- Disk Space ---")
    run_cmd(ssh, "df -h /")
    
    print("\n--- Memory ---")
    run_cmd(ssh, "free -h")
    
    print("\n--- Running Docker Containers ---")
    run_cmd(ssh, "docker ps -a 2>/dev/null || echo 'Docker not running'")
    
    print("\n--- Docker Compose Status ---")
    run_cmd(ssh, "cd /opt/hybrid-rag && docker compose ps 2>/dev/null || echo 'No compose project found'")
    
    print("\n--- Existing project directory ---")
    run_cmd(ssh, "ls -la /opt/hybrid-rag/ 2>/dev/null || echo 'No /opt/hybrid-rag directory'")
    
    print("\n--- Python version ---")
    run_cmd(ssh, "python3 --version 2>/dev/null || echo 'Python not found'")
    
    print("\n--- Node version ---")
    run_cmd(ssh, "node --version 2>/dev/null || echo 'Node not found'")
    
    print("\n--- Docker version ---")
    run_cmd(ssh, "docker --version 2>/dev/null || echo 'Docker not found'")
    
    print("\n--- Docker Compose version ---")
    run_cmd(ssh, "docker compose version 2>/dev/null || echo 'Docker compose not found'")
    
    print("\n--- Nginx status ---")
    run_cmd(ssh, "systemctl is-active nginx 2>/dev/null || echo 'nginx not active'")
    
    print("\n--- PostgreSQL status ---")
    run_cmd(ssh, "systemctl is-active postgresql 2>/dev/null || echo 'postgresql not active'")
    
    print("\n--- Listening Ports ---")
    run_cmd(ssh, "ss -tlnp | grep -E '(80|443|8000|8001|5432|8085)'")
    
    print("\n--- Existing .env on server ---")
    run_cmd(ssh, "cat /opt/hybrid-rag/.env 2>/dev/null || echo 'No .env found'")
    run_cmd(ssh, "cat /opt/hybrid-rag/backend/.env 2>/dev/null || echo 'No backend/.env found'")
    
    print("\n--- Existing nginx config ---")
    run_cmd(ssh, "ls /etc/nginx/sites-enabled/ 2>/dev/null || echo 'No nginx sites'")
    run_cmd(ssh, "cat /etc/nginx/sites-enabled/hybrid-rag 2>/dev/null || echo 'No hybrid-rag nginx config'")
    
    ssh.close()
    print("\n\nDone! Server state check complete.")

if __name__ == "__main__":
    main()

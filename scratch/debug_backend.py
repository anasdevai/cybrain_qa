"""
Debug and fix backend startup issues on the server.
"""
import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SERVER = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"
REMOTE_BACKEND = "/root/cybrain-backend"

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
    return ssh

def run_cmd(ssh, cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out.strip():
        print(out.rstrip())
    if err.strip():
        print(f"[stderr] {err.rstrip()}")
    return out, err, exit_code

def main():
    ssh = ssh_connect()
    
    # Stop existing services
    print("=== Stopping existing backend ===")
    run_cmd(ssh, "systemctl stop cybrain-backend 2>/dev/null; pkill -f 'uvicorn app.main' 2>/dev/null; sleep 2")
    
    # Check what's in the app directory
    print("\n=== Files in app/ ===")
    run_cmd(ssh, f"ls -la {REMOTE_BACKEND}/app/")
    
    # Check Python version and available packages
    print("\n=== Python packages ===")
    run_cmd(ssh, f"cd {REMOTE_BACKEND} && source venv/bin/activate && pip list 2>&1 | grep -iE '(fastapi|uvicorn|sqlalchemy|psycopg|jose|passlib|langchain|google|dotenv|httpx|email)'")
    
    # Try importing the app
    print("\n=== Test import ===")
    run_cmd(ssh, f"""
        cd {REMOTE_BACKEND} && source venv/bin/activate
        python3 -c "
import sys
print(f'Python: {{sys.version}}')
print(f'CWD modules:')

# Test each import individually
modules = [
    ('fastapi', 'from fastapi import FastAPI'),
    ('cors', 'from fastapi.middleware.cors import CORSMiddleware'),
    ('database', 'from app.database import Base, engine'),
    ('routes', 'from app.routes import router'),
    ('public_routes', 'from app.public_routes import public_router'),
    ('ai_routes', 'from app.ai_routes import ai_router'),
    ('auth_routes', 'from app.auth_routes import router as auth_router'),
    ('chat_history_routes', 'from app.chat_history_routes import router as chat_history_router'),
]

for name, imp in modules:
    try:
        exec(imp)
        print(f'  [OK] {{name}}')
    except Exception as e:
        print(f'  [FAIL] {{name}}: {{e}}')
" 2>&1
    """)
    
    # Check database.py reads the right .env
    print("\n=== database.py content ===")
    run_cmd(ssh, f"cat {REMOTE_BACKEND}/app/database.py")
    
    # Check systemd journal
    print("\n=== systemd journal (last 30 lines) ===")
    run_cmd(ssh, "journalctl -u cybrain-backend --no-pager -n 30 2>&1")
    
    # Check log file
    print("\n=== Backend log file ===")
    run_cmd(ssh, "tail -40 /var/log/cybrain-backend.log 2>/dev/null || echo 'no log file'")
    run_cmd(ssh, "tail -40 /var/log/cybrain-backend-error.log 2>/dev/null || echo 'no error log'")
    
    ssh.close()

if __name__ == "__main__":
    main()

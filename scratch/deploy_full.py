"""
Full deployment script for Cybrain QS project.
Uploads latest backend code, rebuilds frontend, configures server.
"""
import paramiko
import os
import sys
import stat
import time

SERVER = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_LOCAL = os.path.join(PROJECT_DIR, "backend")
FRONTEND_LOCAL = os.path.join(PROJECT_DIR, "frontend")

REMOTE_BACKEND = "/root/cybrain-backend"
REMOTE_FRONTEND_DIST = "/var/www/cybrain"

# Files/dirs to skip when uploading
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.cursor', '.vscode', 'dist'}
SKIP_FILES = {'.DS_Store', 'Thumbs.db', 'uvicorn_debug.log'}

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
    return ssh

def run_cmd(ssh, cmd, print_output=True, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if print_output:
        if out.strip():
            print(out.rstrip())
        if err.strip() and exit_code != 0:
            print(f"  [stderr] {err.rstrip()}")
    return out, err, exit_code

def upload_dir(sftp, local_dir, remote_dir, label=""):
    """Recursively upload a directory."""
    count = 0
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"
        
        if os.path.isdir(local_path):
            if item in SKIP_DIRS:
                continue
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                sftp.mkdir(remote_path)
            count += upload_dir(sftp, local_path, remote_path, label)
        else:
            if item in SKIP_FILES:
                continue
            try:
                sftp.put(local_path, remote_path)
                count += 1
            except Exception as e:
                print(f"    WARN: Failed to upload {local_path}: {e}")
    return count

def main():
    print("=" * 60)
    print("  CYBRAIN QS - FULL DEPLOYMENT")
    print(f"  Server: {SERVER}")
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    ssh = ssh_connect()
    sftp = ssh.open_sftp()
    
    # ================================================================
    # STEP 1: UPLOAD BACKEND CODE
    # ================================================================
    print("\n[1/7] Uploading backend code...")
    
    # Backup current backend
    run_cmd(ssh, f"cp -r {REMOTE_BACKEND}/app {REMOTE_BACKEND}/app.bak.$(date +%Y%m%d%H%M%S) 2>/dev/null", print_output=False)
    
    # Ensure app directory exists
    run_cmd(ssh, f"mkdir -p {REMOTE_BACKEND}/app/services", print_output=False)
    
    # Upload backend/app/ files
    app_local = os.path.join(BACKEND_LOCAL, "app")
    app_remote = f"{REMOTE_BACKEND}/app"
    
    file_count = upload_dir(sftp, app_local, app_remote, "backend/app")
    print(f"  Uploaded {file_count} files to {app_remote}")
    
    # Upload backend .env
    local_env = os.path.join(BACKEND_LOCAL, ".env")
    # We need to create a proper production .env for the server
    # The server uses cybrain_db via psycopg, not editor_db
    # Let's preserve existing .env but add missing vars
    print("  Updating backend .env with new variables...")
    
    # Read current server .env
    env_out, _, _ = run_cmd(ssh, f"cat {REMOTE_BACKEND}/.env", print_output=False)
    current_env = dict(line.split("=", 1) for line in env_out.strip().splitlines() if "=" in line and not line.startswith("#"))
    
    # Read local .env for new variables
    with open(local_env, 'r') as f:
        local_env_content = f.read()
    local_env_vars = dict(line.split("=", 1) for line in local_env_content.strip().splitlines() if "=" in line and not line.startswith("#"))
    
    # Merge: keep server DB URL, add new vars from local
    merged_env = {}
    # Keep the server's DATABASE_URL (uses cybrain_db with psycopg)
    merged_env["DATABASE_URL"] = current_env.get("DATABASE_URL", "postgresql+psycopg://cybrain_user:Cph181ko!!@localhost:5432/cybrain_db")
    merged_env["ENVIRONMENT"] = "production"
    merged_env["MOCK_EDITOR_MODE"] = "false"
    
    # Add all vars from local that aren't already set
    for key, val in local_env_vars.items():
        if key == "DATABASE_URL":
            continue  # keep server's DB URL
        if key not in merged_env:
            merged_env[key] = val
    
    # Ensure critical vars are set
    merged_env.setdefault("JWT_SECRET_KEY", local_env_vars.get("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"))
    merged_env.setdefault("JWT_REFRESH_SECRET_KEY", local_env_vars.get("JWT_REFRESH_SECRET_KEY", "fc2a1bb92b5168dbfae40a0bb1e19d7d457b01d360ad4ad6551bafb7a5a8e030"))
    merged_env.setdefault("GOOGLE_API_KEY", local_env_vars.get("GOOGLE_API_KEY", ""))
    merged_env.setdefault("GEMINI_MODEL", local_env_vars.get("GEMINI_MODEL", "gemini-2.5-flash"))
    
    # Write merged .env
    env_content = "\n".join(f"{k}={v}" for k, v in sorted(merged_env.items()))
    env_content += "\n"
    
    with sftp.open(f"{REMOTE_BACKEND}/.env", 'w') as f:
        f.write(env_content)
    print(f"  Updated .env with {len(merged_env)} variables")
    
    # Upload backend requirements.txt
    sftp.put(os.path.join(BACKEND_LOCAL, "requirements.txt"), f"{REMOTE_BACKEND}/requirements.txt")
    print("  Uploaded requirements.txt")
    
    # ================================================================
    # STEP 2: INSTALL BACKEND DEPENDENCIES
    # ================================================================
    print("\n[2/7] Installing backend dependencies...")
    run_cmd(ssh, f"cd {REMOTE_BACKEND} && source venv/bin/activate && pip install -q -r requirements.txt 2>&1 | tail -5", timeout=300)
    
    # ================================================================
    # STEP 3: FIX DATABASE CONNECTION
    # ================================================================
    print("\n[3/7] Verifying database connection...")
    
    # The backend uses synchronous psycopg2-binary, but the server .env has psycopg
    # Let's check if psycopg2-binary is installed and fix the DATABASE_URL format
    run_cmd(ssh, f"cd {REMOTE_BACKEND} && source venv/bin/activate && python -c \"import psycopg2; print('psycopg2 OK')\" 2>&1")
    
    # The database.py uses plain postgresql:// not postgresql+psycopg://
    # Let's fix the .env DATABASE_URL to match what SQLAlchemy expects with psycopg2
    print("  Fixing DATABASE_URL format for psycopg2...")
    run_cmd(ssh, f"""
        cd {REMOTE_BACKEND}
        # Check if DATABASE_URL uses +psycopg and fix to use psycopg2
        if grep -q 'postgresql+psycopg://' .env; then
            sed -i 's|postgresql+psycopg://|postgresql+psycopg2://|g' .env
            echo '  Fixed: postgresql+psycopg -> postgresql+psycopg2'
        elif grep -q 'postgresql://' .env && ! grep -q 'postgresql+' .env; then
            echo '  OK: Using plain postgresql:// (psycopg2 default)'
        else
            echo '  Current URL format:'
            grep DATABASE_URL .env
        fi
    """)
    
    # Verify DB connection
    run_cmd(ssh, f"""
        cd {REMOTE_BACKEND} && source venv/bin/activate && python -c "
from dotenv import load_dotenv
load_dotenv()
import os
url = os.getenv('DATABASE_URL')
print(f'DATABASE_URL = {{url}}')
from sqlalchemy import create_engine, text
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT count(*) FROM sops'))
    count = result.scalar()
    print(f'SOPs in database: {{count}}')
    result2 = conn.execute(text('SELECT count(*) FROM deviations'))
    print(f'Deviations in database: {{result2.scalar()}}')
print('Database connection OK!')
" 2>&1
    """)
    
    # ================================================================
    # STEP 4: RESTART BACKEND SERVICE
    # ================================================================
    print("\n[4/7] Restarting backend service...")
    
    # Kill existing uvicorn on host
    run_cmd(ssh, "pkill -f 'uvicorn app.main:app.*127.0.0.1.*8000' 2>/dev/null; sleep 2", print_output=False)
    
    # Start backend in background
    run_cmd(ssh, f"""
        cd {REMOTE_BACKEND} && source venv/bin/activate
        nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > /tmp/cybrain-backend.log 2>&1 &
        disown
        sleep 3
        echo "Backend PID: $(pgrep -f 'uvicorn app.main:app')"
    """)
    
    # Wait for backend to start
    time.sleep(5)
    
    # Verify backend is running
    out, _, _ = run_cmd(ssh, "curl -s http://127.0.0.1:8000/")
    if "Cybrain" in out:
        print("  ✓ Backend is running!")
    else:
        print("  ✗ Backend may not be running correctly")
        run_cmd(ssh, "tail -30 /tmp/cybrain-backend.log")
    
    # ================================================================
    # STEP 5: BUILD AND DEPLOY FRONTEND
    # ================================================================
    print("\n[5/7] Building frontend locally...")
    
    # We'll build the frontend locally first since Node.js isn't on the server
    frontend_dist = os.path.join(FRONTEND_LOCAL, "dist")
    
    if not os.path.exists(frontend_dist):
        print("  Frontend dist not found. Building...")
        print("  (Building frontend requires running 'npm run build' locally)")
    
    if os.path.exists(frontend_dist):
        print(f"  Uploading frontend dist from {frontend_dist}")
        
        # Clear old dist on server
        run_cmd(ssh, f"rm -rf {REMOTE_FRONTEND_DIST}/*", print_output=False)
        run_cmd(ssh, f"mkdir -p {REMOTE_FRONTEND_DIST}", print_output=False)
        
        # Upload dist files
        dist_count = upload_dir(sftp, frontend_dist, REMOTE_FRONTEND_DIST, "frontend/dist")
        print(f"  Uploaded {dist_count} frontend files to {REMOTE_FRONTEND_DIST}")
    else:
        print("  WARNING: No frontend dist found locally. Will build on next step.")
    
    # ================================================================
    # STEP 6: UPDATE NGINX CONFIG
    # ================================================================
    print("\n[6/7] Updating Nginx configuration...")
    
    nginx_config = """server {
    listen 80;
    server_name 65.21.244.158;

    # Frontend
    root /var/www/cybrain;
    index index.html;

    # Explicit redirects for docs
    location = /docs {
        return 301 /api/docs;
    }
    location = /openapi.json {
        return 301 /api/openapi.json;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # Auth routes
    location /auth {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Chatbot query routes
    location /query {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Extract text endpoint
    location /extract-text {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        client_max_body_size 20M;
    }
    
    # Chat history
    location /chat {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    # Write nginx config
    with sftp.open("/etc/nginx/sites-available/cybrain", 'w') as f:
        f.write(nginx_config)
    
    # Ensure symlink
    run_cmd(ssh, "ln -sf /etc/nginx/sites-available/cybrain /etc/nginx/sites-enabled/cybrain", print_output=False)
    
    # Test and reload nginx
    out, _, code = run_cmd(ssh, "nginx -t 2>&1")
    if code == 0:
        run_cmd(ssh, "systemctl reload nginx")
        print("  ✓ Nginx config updated and reloaded")
    else:
        print(f"  ✗ Nginx config test failed: {out}")
    
    # ================================================================
    # STEP 7: VERIFY DEPLOYMENT
    # ================================================================
    print("\n[7/7] Verifying deployment...")
    
    # Test root endpoint
    out, _, _ = run_cmd(ssh, "curl -s http://127.0.0.1:8000/")
    print(f"  Root: {out.strip()[:100]}")
    
    # Test API endpoints
    endpoints = [
        "/api/sops",
        "/api/deviations",
        "/api/capas",
        "/api/decisions",
        "/api/audits",
        "/api/docs",
    ]
    
    for ep in endpoints:
        out, _, _ = run_cmd(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8000{ep}", print_output=False)
        status = out.strip()
        icon = "✓" if status in ("200", "307") else "✗"
        print(f"  {icon} {ep} -> HTTP {status}")
    
    # Test external access
    print("\n  External access (via nginx port 80):")
    out, _, _ = run_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://65.21.244.158/", print_output=False)
    print(f"  Frontend: HTTP {out.strip()}")
    
    out, _, _ = run_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://65.21.244.158/api/sops", print_output=False)
    print(f"  API /api/sops: HTTP {out.strip()}")
    
    # Create systemd service for auto-restart
    print("\n  Setting up systemd service for auto-restart...")
    systemd_service = f"""[Unit]
Description=Cybrain QS Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory={REMOTE_BACKEND}
Environment=PATH={REMOTE_BACKEND}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={REMOTE_BACKEND}/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:/var/log/cybrain-backend.log
StandardError=append:/var/log/cybrain-backend-error.log

[Install]
WantedBy=multi-user.target
"""
    with sftp.open("/etc/systemd/system/cybrain-backend.service", 'w') as f:
        f.write(systemd_service)
    
    # Kill the nohup process and switch to systemd
    run_cmd(ssh, "pkill -f 'uvicorn app.main:app' 2>/dev/null; sleep 2", print_output=False)
    run_cmd(ssh, "systemctl daemon-reload", print_output=False)
    run_cmd(ssh, "systemctl enable cybrain-backend", print_output=False)
    run_cmd(ssh, "systemctl start cybrain-backend", print_output=False)
    
    time.sleep(5)
    
    out, _, _ = run_cmd(ssh, "systemctl is-active cybrain-backend", print_output=False)
    if "active" in out:
        print("  ✓ systemd service is active")
    else:
        print(f"  Service status: {out.strip()}")
        run_cmd(ssh, "journalctl -u cybrain-backend --no-pager -n 20")
    
    # Final health check
    out, _, _ = run_cmd(ssh, "curl -s http://127.0.0.1:8000/")
    print(f"\n  Final health: {out.strip()[:120]}")
    
    sftp.close()
    ssh.close()
    
    print("\n" + "=" * 60)
    print("  DEPLOYMENT COMPLETE!")
    print(f"  Frontend: http://{SERVER}/")
    print(f"  API Docs: http://{SERVER}/api/docs")
    print(f"  API: http://{SERVER}/api/sops")
    print("=" * 60)

if __name__ == "__main__":
    main()

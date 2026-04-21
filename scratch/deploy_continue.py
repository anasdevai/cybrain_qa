"""
Continue deployment from step 4 - verify backend, upload frontend, nginx, systemd.
"""
import paramiko
import os
import sys
import time

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SERVER = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_LOCAL = os.path.join(PROJECT_DIR, "frontend")
REMOTE_BACKEND = "/root/cybrain-backend"
REMOTE_FRONTEND_DIST = "/var/www/cybrain"

SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.cursor', '.vscode'}
SKIP_FILES = {'.DS_Store', 'Thumbs.db'}

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

def upload_dir(sftp, local_dir, remote_dir):
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
            count += upload_dir(sftp, local_path, remote_path)
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
    ssh = ssh_connect()
    sftp = ssh.open_sftp()
    
    # ================================================================
    # STEP 4: Check and fix backend startup
    # ================================================================
    print("\n[4/7] Checking backend status...")
    
    # Kill any existing uvicorn processes (from previous deploy attempt)
    run_cmd(ssh, "pkill -f 'uvicorn app.main:app' 2>/dev/null; sleep 2", print_output=False)
    time.sleep(3)
    
    # Check the server .env
    print("  Current .env:")
    run_cmd(ssh, f"cat {REMOTE_BACKEND}/.env")
    
    # Check if the backend starts correctly
    print("\n  Starting backend with test run...")
    out, err, code = run_cmd(ssh, f"""
        cd {REMOTE_BACKEND} && source venv/bin/activate
        timeout 10 uvicorn app.main:app --host 127.0.0.1 --port 8000 2>&1 | head -30 || true
    """, timeout=30)
    
    # Check for import errors in the output
    if "Error" in out or "Error" in (err or ""):
        print("  [!] Backend has errors, checking details...")
        # Try importing the app module directly
        run_cmd(ssh, f"""
            cd {REMOTE_BACKEND} && source venv/bin/activate
            python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.main import app
    print('Import OK - app loaded successfully')
except Exception as e:
    print(f'Import FAILED: {{e}}')
    import traceback
    traceback.print_exc()
" 2>&1
        """)
    
    # Start the backend properly
    print("\n  Starting backend service...")
    run_cmd(ssh, f"""
        cd {REMOTE_BACKEND} && source venv/bin/activate
        nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > /var/log/cybrain-backend.log 2>&1 &
        disown
        sleep 4
        echo "Backend PIDs: $(pgrep -f 'uvicorn app.main:app' | tr '\\n' ' ')"
    """)
    
    time.sleep(3)
    
    # Verify
    out, _, _ = run_cmd(ssh, "curl -s http://127.0.0.1:8000/", print_output=False)
    if "Cybrain" in out:
        print(f"  [OK] Backend is running: {out.strip()[:100]}")
    else:
        print(f"  [WARN] Backend response: {out.strip()[:200]}")
        print("  Checking logs...")
        run_cmd(ssh, "tail -40 /var/log/cybrain-backend.log")
    
    # ================================================================
    # STEP 5: Upload frontend dist
    # ================================================================
    print("\n[5/7] Uploading frontend dist...")
    
    frontend_dist = os.path.join(FRONTEND_LOCAL, "dist")
    
    if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
        # Clear old dist on server
        run_cmd(ssh, f"rm -rf {REMOTE_FRONTEND_DIST}/*", print_output=False)
        run_cmd(ssh, f"mkdir -p {REMOTE_FRONTEND_DIST}/assets", print_output=False)
        
        # Upload dist files
        dist_count = upload_dir(sftp, frontend_dist, REMOTE_FRONTEND_DIST)
        print(f"  Uploaded {dist_count} frontend files to {REMOTE_FRONTEND_DIST}")
        
        # Verify
        run_cmd(ssh, f"ls -la {REMOTE_FRONTEND_DIST}/")
        run_cmd(ssh, f"ls -la {REMOTE_FRONTEND_DIST}/assets/")
    else:
        print(f"  [WARN] No frontend dist found at {frontend_dist}")
    
    # ================================================================
    # STEP 6: Update Nginx config
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

        # Cache static assets
        location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
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
    
    with sftp.open("/etc/nginx/sites-available/cybrain", 'w') as f:
        f.write(nginx_config)
    
    run_cmd(ssh, "ln -sf /etc/nginx/sites-available/cybrain /etc/nginx/sites-enabled/cybrain", print_output=False)
    
    out, err, code = run_cmd(ssh, "nginx -t 2>&1")
    if "successful" in out or "successful" in (err or ""):
        run_cmd(ssh, "systemctl reload nginx")
        print("  [OK] Nginx config updated and reloaded")
    else:
        # nginx -t outputs to stderr
        out2, err2, code2 = run_cmd(ssh, "nginx -t 2>&1", print_output=False)
        combined = out2 + (err2 or "")
        if code2 == 0:
            run_cmd(ssh, "systemctl reload nginx")
            print("  [OK] Nginx config updated and reloaded")
        else:
            print(f"  [FAIL] Nginx config test failed:\n{combined}")
    
    # ================================================================
    # STEP 7: Set up systemd service + verify
    # ================================================================
    print("\n[7/7] Setting up systemd service and final verification...")
    
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
    run_cmd(ssh, "systemctl enable cybrain-backend 2>/dev/null", print_output=False)
    run_cmd(ssh, "systemctl start cybrain-backend", print_output=False)
    
    time.sleep(5)
    
    out, _, _ = run_cmd(ssh, "systemctl is-active cybrain-backend", print_output=False)
    status = out.strip()
    if status == "active":
        print(f"  [OK] systemd service is {status}")
    else:
        print(f"  [!] Service status: {status}")
        run_cmd(ssh, "journalctl -u cybrain-backend --no-pager -n 30")
    
    # Final API verification
    print("\n  --- Final Endpoint Tests ---")
    time.sleep(3)
    
    endpoints = [
        ("Root", "http://127.0.0.1:8000/"),
        ("API Docs", "http://127.0.0.1:8000/api/docs"),
        ("SOPs", "http://127.0.0.1:8000/api/sops"),
        ("Deviations", "http://127.0.0.1:8000/api/deviations"),
        ("CAPAs", "http://127.0.0.1:8000/api/capas"),
        ("Decisions", "http://127.0.0.1:8000/api/decisions"),
        ("Audits", "http://127.0.0.1:8000/api/audits"),
        ("Stats", "http://127.0.0.1:8000/api/stats"),
        ("Search", "http://127.0.0.1:8000/api/search?q=test"),
    ]
    
    for label, url in endpoints:
        out, _, _ = run_cmd(ssh, f"curl -s -o /dev/null -w '%{{http_code}}' '{url}'", print_output=False)
        code = out.strip()
        ok = "[OK]" if code in ("200", "307") else "[!!]"
        print(f"  {ok} {label}: HTTP {code}")
    
    # External access
    print("\n  --- External Access (via nginx :80) ---")
    out, _, _ = run_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://65.21.244.158/", print_output=False)
    print(f"  Frontend: HTTP {out.strip()}")
    
    out, _, _ = run_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://65.21.244.158/api/sops", print_output=False)
    print(f"  API /api/sops: HTTP {out.strip()}")
    
    out, _, _ = run_cmd(ssh, "curl -s -o /dev/null -w '%{http_code}' http://65.21.244.158/api/docs", print_output=False)
    print(f"  API /api/docs: HTTP {out.strip()}")
    
    # Show a sample of data
    print("\n  --- Sample Data ---")
    out, _, _ = run_cmd(ssh, "curl -s http://127.0.0.1:8000/api/sops | python3 -c \"import sys,json; data=json.load(sys.stdin); print(f'SOPs: {len(data)} records'); [print(f'  - {s[\\\"sop_number\\\"]}: {s[\\\"title\\\"]}') for s in data[:3]]\" 2>&1", print_output=True)
    
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

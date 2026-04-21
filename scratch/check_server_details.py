"""
Check the host-level cybrain backend and nginx config
"""
import paramiko

SERVER = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

def run_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out.strip():
        print(out)
    if err.strip():
        print(f"[stderr] {err}")
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
    
    print("=== cybrain-backend directory ===")
    run_cmd(ssh, "ls -la /root/cybrain-backend/ 2>/dev/null | head -30")
    
    print("\n=== cybrain-backend app structure ===")
    run_cmd(ssh, "ls -la /root/cybrain-backend/app/ 2>/dev/null | head -20")
    
    print("\n=== cybrain-backend .env ===")
    run_cmd(ssh, "cat /root/cybrain-backend/.env 2>/dev/null")
    
    print("\n=== cybrain-backend main.py (first 30 lines) ===")
    run_cmd(ssh, "head -30 /root/cybrain-backend/app/main.py 2>/dev/null")
    
    print("\n=== nginx cybrain config ===")
    run_cmd(ssh, "cat /etc/nginx/sites-enabled/cybrain 2>/dev/null")
    
    print("\n=== nginx default config ===")
    run_cmd(ssh, "cat /etc/nginx/sites-enabled/default 2>/dev/null || echo 'no default'")
    
    print("\n=== Host health check (127.0.0.1:8000) ===")
    run_cmd(ssh, "curl -s http://127.0.0.1:8000/ 2>/dev/null")
    
    print("\n=== Host API test (127.0.0.1:8000/api/sops) ===")
    run_cmd(ssh, "curl -s http://127.0.0.1:8000/api/sops 2>/dev/null | head -c 300")
    
    print("\n=== External test (port 80) ===")
    run_cmd(ssh, "curl -s http://localhost/ 2>/dev/null | head -c 500")
    
    print("\n=== External API test (port 80) ===")
    run_cmd(ssh, "curl -s http://localhost/api/sops 2>/dev/null | head -c 300")
    
    print("\n=== systemd cybrain service ===")
    run_cmd(ssh, "systemctl status cybrain-backend 2>/dev/null || systemctl list-units | grep cybrain 2>/dev/null || echo 'no systemd cybrain service'")
    
    print("\n=== pm2 list ===")
    run_cmd(ssh, "pm2 list 2>/dev/null || echo 'pm2 not installed'")
    
    ssh.close()

if __name__ == "__main__":
    main()

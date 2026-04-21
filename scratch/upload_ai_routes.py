"""
Upload ai_routes.py to the server
"""
import paramiko
import os

SERVER = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
    
    sftp = ssh.open_sftp()
    
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app", "ai_routes.py")
    remote_path = "/root/cybrain-backend/app/ai_routes.py"
    
    print(f"Uploading {local_path} to {remote_path}")
    sftp.put(local_path, remote_path)
    
    sftp.close()
    
    # Check if backend successfully starts now
    stdin, stdout, stderr = ssh.exec_command("cd /root/cybrain-backend && source venv/bin/activate && python3 -c 'from app.main import app; print(\"IMPORT SUCCESS\")'")
    exit_code = stdout.channel.recv_exit_status()
    print("Import exit code:", exit_code)
    print("Import out:", stdout.read().decode())
    print("Import err:", stderr.read().decode())

    # restart systemd
    ssh.exec_command("systemctl restart cybrain-backend")
    
    ssh.close()

if __name__ == "__main__":
    main()

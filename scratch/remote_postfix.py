import paramiko

HOST = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

COMMANDS = [
    "sudo -u postgres psql -d cybrain_db -c \"GRANT ALL PRIVILEGES ON DATABASE cybrain_db TO cybrain_user;\"",
    "sudo -u postgres psql -d cybrain_db -c \"GRANT USAGE ON SCHEMA public TO cybrain_user;\"",
    "sudo -u postgres psql -d cybrain_db -c \"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cybrain_user;\"",
    "sudo -u postgres psql -d cybrain_db -c \"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cybrain_user;\"",
    "sudo -u postgres psql -d cybrain_db -c \"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cybrain_user;\"",
    "sudo -u postgres psql -d cybrain_db -c \"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cybrain_user;\"",
    "systemctl restart cybrain-backend",
    "systemctl is-active cybrain-backend",
    "curl -sS http://127.0.0.1:8000/api/health",
    "curl -sS http://127.0.0.1:8000/api/sops | head -c 300",
    "curl -sS http://127.0.0.1/api/health",
]


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    try:
        for cmd in COMMANDS:
            print(f"--- RUN: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode("utf-8", "ignore")
            err = stderr.read().decode("utf-8", "ignore")
            print(out)
            print(err)
            rc = stdout.channel.recv_exit_status()
            print(f"exit_code={rc}")
            if rc != 0:
                raise SystemExit(rc)
    finally:
        client.close()


if __name__ == "__main__":
    main()

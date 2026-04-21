import paramiko

HOST = "65.21.244.158"
USER = "root"
PASSWORD = "Cph181ko!!"

COMMANDS = [
    "python3 - <<'PY'\nfrom pathlib import Path\np=Path('/root/deploy_remote.sh')\np.write_text(p.read_text().replace('\\r\\n','\\n'))\nprint('normalized')\nPY",
    "bash /root/deploy_remote.sh",
]


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    try:
        for cmd in COMMANDS:
            print(f"--- RUN: {cmd.splitlines()[0]} ---")
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

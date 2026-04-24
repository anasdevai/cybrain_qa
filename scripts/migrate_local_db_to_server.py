#!/usr/bin/env python3
from __future__ import annotations

import os
import select
import socket
import socketserver
import threading
from pathlib import Path

import paramiko
import psycopg

CORE_TABLE_ORDER = [
    "users",
    "chat_sessions",
    "chat_messages",
    "sop_versions",
    "sops",
    "deviations",
    "capas",
    "audit_findings",
    "decisions",
    "sop_deviation_links",
    "deviation_capa_links",
    "capa_audit_links",
    "audit_decision_links",
    "decision_sop_links",
    "ai_action_logs",
    "ai_link_suggestions",
]


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


class Handler(socketserver.BaseRequestHandler):
    ssh_transport: paramiko.Transport
    chain_host: str
    chain_port: int

    def handle(self) -> None:
        chan = self.ssh_transport.open_channel(
            "direct-tcpip",
            (self.chain_host, self.chain_port),
            self.request.getpeername(),
        )
        if chan is None:
            return
        try:
            while True:
                r, _, _ = select.select([self.request, chan], [], [])
                if self.request in r:
                    data = self.request.recv(1024 * 64)
                    if not data:
                        break
                    chan.send(data)
                if chan in r:
                    data = chan.recv(1024 * 64)
                    if not data:
                        break
                    self.request.send(data)
        finally:
            chan.close()
            self.request.close()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env_cfg = load_env(root / ".env")

    ssh_host = os.environ.get("DEPLOY_SSH_HOST", "65.21.244.158")
    ssh_user = os.environ.get("DEPLOY_SSH_USER", "root")
    ssh_pass = os.environ.get("DEPLOY_SSH_PASS") or os.environ.get("DEBUG_SSH_PASS")
    if not ssh_pass:
        raise SystemExit("Set DEPLOY_SSH_PASS or DEBUG_SSH_PASS")

    src_dsn = (
        f"host={env_cfg.get('POSTGRES_HOST', '127.0.0.1')} "
        f"port={env_cfg.get('POSTGRES_PORT', '5432')} "
        f"dbname={env_cfg.get('POSTGRES_DB', 'server_db')} "
        f"user={env_cfg.get('POSTGRES_USER', 'postgres')} "
        f"password={env_cfg.get('POSTGRES_PASSWORD', '')}"
    )
    dst_db = env_cfg.get("POSTGRES_DB", "server_db")
    dst_user = env_cfg.get("POSTGRES_USER", "postgres")
    dst_pass = env_cfg.get("POSTGRES_PASSWORD", "")
    dst_dsn = (
        f"host=127.0.0.1 port=6543 dbname={dst_db} user={dst_user} password={dst_pass}"
    )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ssh_host, username=ssh_user, password=ssh_pass, timeout=30)
    transport = client.get_transport()
    if transport is None:
        raise RuntimeError("SSH transport unavailable")

    class ForwardServer(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

    Handler.ssh_transport = transport
    Handler.chain_host = "127.0.0.1"
    Handler.chain_port = 5432
    server = ForwardServer(("127.0.0.1", 6543), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print("Tunnel opened: localhost:6543 -> remote 127.0.0.1:5432")
    with psycopg.connect(src_dsn) as src_conn, psycopg.connect(dst_dsn) as dst_conn:
        src_conn.autocommit = True
        dst_conn.autocommit = False

        with src_conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname='public'
                ORDER BY tablename
                """
            )
            src_tables = {r[0] for r in cur.fetchall() if r[0] != "alembic_version"}
        with dst_conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname='public'
                ORDER BY tablename
                """
            )
            dst_tables = {r[0] for r in cur.fetchall() if r[0] != "alembic_version"}
        tables = [t for t in CORE_TABLE_ORDER if t in src_tables and t in dst_tables]
        print(f"Tables to copy (core/common): {len(tables)}")

        with dst_conn.cursor() as dcur:
            dcur.execute("SET session_replication_role = replica")
            if tables:
                table_list = ", ".join(f'"public"."{t}"' for t in tables)
                dcur.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE")
            dst_conn.commit()

        for table in tables:
            with src_conn.cursor() as scur:
                scur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name=%s
                    ORDER BY ordinal_position
                    """,
                    (table,),
                )
                src_cols = [r[0] for r in scur.fetchall()]
            with dst_conn.cursor() as dcur:
                dcur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name=%s
                    ORDER BY ordinal_position
                    """,
                    (table,),
                )
                dst_cols = {r[0] for r in dcur.fetchall()}
            cols = [c for c in src_cols if c in dst_cols]
            if not cols:
                continue
            col_csv = ", ".join(f'"{c}"' for c in cols)
            copied = 0
            with src_conn.cursor() as scur, dst_conn.cursor() as dcur:
                with scur.copy(
                    f'COPY (SELECT {col_csv} FROM "public"."{table}") TO STDOUT WITH CSV'
                ) as out_copy:
                    with dcur.copy(
                        f'COPY "public"."{table}" ({col_csv}) FROM STDIN WITH CSV'
                    ) as in_copy:
                        for chunk in out_copy:
                            in_copy.write(chunk)
                            copied += chunk.count(b"\n")
            dst_conn.commit()
            print(f"Copied {table}: ~{copied} rows")

        with dst_conn.cursor() as dcur:
            dcur.execute("SET session_replication_role = origin")
            dst_conn.commit()

    server.shutdown()
    server.server_close()
    client.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()

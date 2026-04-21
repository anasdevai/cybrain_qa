#!/usr/bin/env bash
set -euo pipefail

TS=$(date +%Y%m%d%H%M%S)
echo "START:$TS"

cp /root/cybrain-backend/.env /root/cybrain-backend/.env.bak.$TS || true
sudo -u postgres pg_dump -Fc -d cybrain_db -f /tmp/cybrain_db_predeploy_$TS.dump
cp /tmp/cybrain_db_predeploy_$TS.dump /root/cybrain_db_predeploy_$TS.dump

rm -rf /root/deploy_tmp_backend && mkdir -p /root/deploy_tmp_backend
tar -xzf /root/backend_latest.tar.gz -C /root/deploy_tmp_backend

systemctl stop cybrain-backend
find /root/cybrain-backend -mindepth 1 -maxdepth 1 ! -name venv ! -name .env -exec rm -rf {} +
cp -a /root/deploy_tmp_backend/. /root/cybrain-backend/

sed -i "s#^DATABASE_URL=.*#DATABASE_URL=postgresql+psycopg2://cybrain_user:Cph181ko!!@localhost:5432/cybrain_db#" /root/cybrain-backend/.env
grep -q '^ENVIRONMENT=' /root/cybrain-backend/.env || echo 'ENVIRONMENT=production' >> /root/cybrain-backend/.env

/root/cybrain-backend/venv/bin/pip install -r /root/cybrain-backend/requirements.txt

sudo -u postgres dropdb --if-exists cybrain_db
sudo -u postgres createdb -O cybrain_user cybrain_db
cp /root/local_editor_db_latest.sql /tmp/local_editor_db_latest.sql
chmod 644 /tmp/local_editor_db_latest.sql
sudo -u postgres psql -d cybrain_db -f /tmp/local_editor_db_latest.sql

rm -rf /var/www/cybrain/*
tar -xzf /root/frontend_dist_latest.tar.gz -C /var/www/cybrain
chown -R www-data:www-data /var/www/cybrain

systemctl daemon-reload
systemctl restart cybrain-backend
systemctl is-active cybrain-backend

nginx -t
systemctl reload nginx

curl -sS http://127.0.0.1:8000/api/health
echo
curl -sS http://127.0.0.1/api/health || true
echo

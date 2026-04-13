#!/label/bash

# ─── 1. Backend Python Setup ────────────────────────────
cd /root/cybrain-backend
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install uvicorn[standard] gunicorn

# ─── 2. Environment Variables ───────────────────────────
cat <<EOF > /root/cybrain-backend/.env
DATABASE_URL=postgresql://cybrain_user:choose_a_strong_password@localhost:5432/cybrain_db
ENVIRONMENT=production
MOCK_EDITOR_MODE=false
EOF

# ─── 3. Frontend Move ───────────────────────────────────
mkdir -p /var/www/cybrain
cp -r /root/cybrain-frontend/dist/* /var/www/cybrain/
chown -R www-data:www-data /var/www/cybrain

# ─── 4. Systemd Service ─────────────────────────────────
cat <<EOF > /etc/systemd/system/cybrain-backend.service
[Unit]
Description=Cybrain QS FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/cybrain-backend
Environment="PATH=/root/cybrain-backend/venv/bin"
EnvironmentFile=/root/cybrain-backend/.env
ExecStart=/root/cybrain-backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cybrain-backend
systemctl restart cybrain-backend

# ─── 5. Nginx Configuration ─────────────────────────────
cat <<EOF > /etc/nginx/sites-available/cybrain
server {
    listen 80;
    server_name 65.21.244.158;

    # Frontend
    root /var/www/cybrain;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Backend
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cybrain /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

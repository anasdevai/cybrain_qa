# 🚀 Deployment Plan: Hybrid RAG Chatbot (SOPSearch AI)

## 📋 Project Overview

**Hybrid RAG Chatbot** is an enterprise-grade SOP (Standard Operating Procedure) search system featuring:
- **Backend**: FastAPI (Python 3.12+) with async PostgreSQL
- **Frontend**: React + Vite (SPA)
- **Vector DB**: Qdrant (cloud or self-hosted)
- **Relational DB**: PostgreSQL (async)
- **AI Models**: Google Gemini 2.5 Flash, BGE embeddings, Cross-Encoder reranker
- **Auth**: JWT-based authentication

---

## 🎯 Deployment Architecture

```
┌─────────────────────────────────────────────┐
│         Ubuntu Server (4GB RAM)             │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │   Nginx      │─────▶│  FastAPI Backend│ │
│  │  (Reverse    │      │  (Uvicorn)      │ │
│  │   Proxy)     │      │  Port: 8000     │ │
│  └──────────────┘      └────────┬────────┘ │
│         │                       │          │
│         │ Port 80/443           │ Port 5173│
│         ▼                       ▼          │
│  ┌──────────────────────────────────────┐  │
│  │   React Frontend (Static Files)      │  │
│  │   (Built & Served by Nginx)          │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  External Services:                         │
│  - Qdrant Cloud (vector DB)                 │
│  - Google Gemini API (LLM)                  │
│  - PostgreSQL (local or managed)            │
└─────────────────────────────────────────────┘
```

---

## 📦 Prerequisites on Server

### System Requirements
- **OS**: Ubuntu 22.04/24.04 LTS
- **RAM**: 4GB minimum (8GB recommended for embedding models)
- **CPU**: 2+ cores
- **Storage**: 20GB+ (for models, logs, frontend build)
- **Network**: Outbound access to Qdrant Cloud & Google APIs

### Required Software
1. **Python 3.12+** (via deadsnakes PPA or pyenv)
2. **Node.js 18+** (for frontend build)
3. **PostgreSQL 14+** (local installation)
4. **Nginx** (reverse proxy + static file serving)
5. **Git** (version control)
6. **uv** (Python package manager - faster than pip)

---

## 🔧 Deployment Steps

### Step 1: Server Preparation

```bash
# Connect to your server
ssh root@AI-Law-Firm-ubuntu-4gb-hel1-1

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
  python3.12 python3.12-venv python3.12-dev \
  postgresql postgresql-contrib \
  nginx git curl wget \
  build-essential

# Install Node.js 20.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Create deployment user (optional, recommended)
sudo useradd -m -s /bin/bash hybridrag
sudo usermod -aG sudo hybridrag
```

---

### Step 2: PostgreSQL Setup

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE hybrid_rag_db;
CREATE USER hybridrag_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE hybrid_rag_db TO hybridrag_user;
\c hybrid_rag_db
GRANT ALL ON SCHEMA public TO hybridrag_user;
ALTER DATABASE hybrid_rag_db OWNER TO hybridrag_user;
EOF

# Test connection
psql -U hybridrag_user -d hybrid_rag_db -h localhost -c "SELECT 1;"
```

---

### Step 3: Application Deployment

#### 3.1 Clone Repository

```bash
# Create app directory
sudo mkdir -p /opt/hybrid-rag
sudo chown -R $USER:$USER /opt/hybrid-rag
cd /opt/hybrid-rag

# Clone your repository (or upload via SCP/SFTP)
git clone <your-repo-url> .
# OR upload from local:
# On your Windows machine:
# scp -r "c:\Users\Muhammad Anas\Desktop\Hybrid_rag\*" root@AI-Law-Firm-ubuntu-4gb-hel1-1:/opt/hybrid-rag/
```

#### 3.2 Backend Setup

```bash
cd /opt/hybrid-rag

# Create Python virtual environment
uv venv
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt
uv pip install -r requirements.db.txt

# Install additional production dependencies
uv pip install gunicorn  # Production WSGI server (optional)
```

#### 3.3 Environment Configuration

```bash
# Create .env file from example
cp .env.db.example .env

# Edit with your actual credentials
nano .env
```

**Required `.env` variables:**
```env
# PostgreSQL
POSTGRES_USER=hybridrag_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=hybrid_rag_db

# JWT Authentication
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_REFRESH_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.tech
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_HOST=your-cluster.qdrant.tech
QDRANT_PORT=6333

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_gemini_api_key

# Collection Names (Qdrant)
COLLECTION_SOPS=docs_sops
COLLECTION_DEVIATIONS=docs_deviations
COLLECTION_CAPAS=docs_capas
COLLECTION_AUDITS=docs_audits
COLLECTION_DECISIONS=docs_decisions

# Webhook Security
WEBHOOK_SECRET=your_webhook_secret_key

# Production Settings
ENVIRONMENT=production
CORS_ORIGINS=http://your-domain.com,https://your-domain.com
```

#### 3.4 Database Migration

```bash
cd /opt/hybrid-rag

# Run Alembic migrations
uv run alembic upgrade head

# Verify tables created
uv run python -c "
import asyncio
from database.config import engine
from database.models import User, ChatSession, ChatMessage
async def check():
    async with engine.begin() as conn:
        result = await conn.run_sync(lambda c: c.dialect.has_table(c, 'users'))
        print(f'Users table exists: {result}')
asyncio.run(check())
"
```

#### 3.5 Frontend Build

```bash
cd /opt/hybrid-rag/frontend

# Install dependencies
npm install

# Update vite.config.js for production
cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/query': 'http://localhost:8000',
      '/webhooks': 'http://localhost:8000',
    }
  }
})
EOF

# Build for production
npm run build

# The built files will be in frontend/dist/
```

---

### Step 4: Production Service Setup

#### 4.1 Backend Systemd Service

Create `/etc/systemd/system/hybridrag-backend.service`:

```ini
[Unit]
Description=Hybrid RAG Backend API
After=network.target postgresql.target

[Service]
Type=notify
User=hybridrag
Group=hybridrag
WorkingDirectory=/opt/hybrid-rag
Environment=PATH=/opt/hybrid-rag/.venv/bin
ExecStart=/opt/hybrid-rag/.venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --loop uvloop \
    --http httptools \
    --log-level info \
    --access-log
Restart=on-failure
RestartSec=10
StandardOutput=append:/opt/hybrid-rag/server.log
StandardError=append:/opt/hybrid-rag/server_err.log

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/hybrid-rag

[Install]
WantedBy=multi-user.target
```

#### 4.2 Enable & Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start backend
sudo systemctl enable hybridrag-backend
sudo systemctl start hybridrag-backend

# Check status
sudo systemctl status hybridrag-backend

# View logs
sudo journalctl -u hybridrag-backend -f
```

---

### Step 5: Nginx Configuration

Create `/etc/nginx/sites-available/hybrid-rag`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Frontend static files
    location / {
        root /opt/hybrid-rag/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API proxy
    location /auth/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for long queries
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    location /chat/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
    
    location /query/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;  # Allow time for AI responses
    }
    
    location /webhooks/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
}
```

Enable the site:

```bash
# Link configuration
sudo ln -s /etc/nginx/sites-available/hybrid-rag /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

### Step 6: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

### Step 7: Firewall Configuration

```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Verify
sudo ufw status
```

---

## 🧪 Testing Deployment

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API directly
curl http://127.0.0.1:8000/health

# Test via Nginx
curl http://your-domain.com/health

# Test frontend
curl http://your-domain.com/

# Test user registration
curl -X POST http://your-domain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test1234!"}'

# Test login
curl -X POST http://your-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
```

---

## 📊 Monitoring & Maintenance

### Log Locations
- Backend logs: `/opt/hybrid-rag/server.log`, `server_err.log`
- Systemd logs: `sudo journalctl -u hybridrag-backend -f`
- Nginx access: `/var/log/nginx/access.log`
- Nginx error: `/var/log/nginx/error.log`

### Common Commands

```bash
# Restart backend
sudo systemctl restart hybridrag-backend

# Check backend status
sudo systemctl status hybridrag-backend

# View real-time logs
sudo journalctl -u hybridrag-backend -f

# Restart Nginx
sudo systemctl restart nginx

# Check disk space
df -h

# Monitor memory
free -h

# Check PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -d hybrid_rag_db -c "\dt"
```

---

## ⚠️ Important Considerations

### Memory Management (4GB RAM)
- **Embedding models** load into RAM (~500MB-1GB)
- **Uvicorn workers**: Limited to 2 workers to conserve memory
- **PostgreSQL**: Configure `shared_buffers = 256MB`
- **Consider**: Swap file (2GB) as safety net

```bash
# Create swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Production Optimizations
1. **Use Qdrant Cloud** instead of self-hosted (saves RAM)
2. **Enable connection pooling** (PgBouncer for high traffic)
3. **Set up monitoring** (Prometheus + Grafana)
4. **Implement backups** (PostgreSQL pg_dump automation)
5. **Use CDN** for frontend assets (Cloudflare)

### Security Checklist
- [ ] Strong JWT_SECRET_KEY (64+ characters)
- [ ] Strong database passwords
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured
- [ ] Regular system updates
- [ ] Backup strategy in place
- [ ] Rate limiting on Nginx (for abuse prevention)
- [ ] WEBHOOK_SECRET configured

---

## 🚨 Troubleshooting

### Backend won't start
```bash
sudo journalctl -u hybridrag-backend -n 50 --no-pager
```

### Database connection issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U hybridrag_user -d hybrid_rag_db -h localhost

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### CORS errors
- Update `CORS_ORIGINS` in `.env`
- Check Nginx proxy headers

### Model loading slow
- First start downloads models (~2GB)
- Subsequent starts use cached models
- Models cached in `~/.cache/huggingface/`

---

## 📝 Deployment Checklist

- [ ] Server provisioned (Ubuntu 22.04/24.04)
- [ ] PostgreSQL installed & database created
- [ ] Python 3.12+ installed
- [ ] Node.js 18+ installed
- [ ] Application code deployed to `/opt/hybrid-rag`
- [ ] Python dependencies installed
- [ ] `.env` file configured with production values
- [ ] Database migrations run
- [ ] Frontend built successfully
- [ ] Systemd service created & enabled
- [ ] Nginx configured & running
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Health endpoint responds
- [ ] Registration/Login works
- [ ] Query endpoint functional
- [ ] Logs monitored
- [ ] Backup strategy implemented

---

## 🎯 Quick Deploy Script (Coming Next)

I'll create automated deployment scripts to streamline this process:
- `setup_server.sh` - Installs all dependencies
- `deploy.sh` - Deploys application
- `deploy_frontend.sh` - Builds & deploys frontend
- `.env.production` - Production environment template

---

**Estimated Deployment Time**: 30-45 minutes (first time), 10 minutes (subsequent)

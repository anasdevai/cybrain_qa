#!/bin/bash
# Run once on the server: bash setup_server.sh
set -e

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Install Docker Compose plugin
apt-get install -y docker-compose-plugin

# Clone repo
mkdir -p /opt/hybrid-rag
cd /opt/hybrid-rag
git clone https://github.com/anasdevai/Hybrid_Rag.git .

# Copy your .env file here manually, then:
# docker compose up -d

echo "Server ready. Copy your .env to /opt/hybrid-rag/.env then run: docker compose up -d"

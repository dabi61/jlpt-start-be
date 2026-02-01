#!/bin/bash

# Configuration
VPS_USER="root"
VPS_IP="103.152.164.250"
VPS_PORT="22"
PROJECT_DIR="/root/jlpt_start"

echo "🔧 Fixing Server Git State..."

ssh -p $VPS_PORT $VPS_USER@$VPS_IP << EOF
    cd $PROJECT_DIR

    echo "1. Backing up SSL Certificates..."
    mkdir -p /tmp/certbot_backup
    cp -r data/certbot/* /tmp/certbot_backup/ 2>/dev/null || true

    echo "2. Hard Resetting Git (Discarding local commits)..."
    git fetch origin
    git reset --hard origin/main

    echo "3. Cleaning untracked files..."
    git clean -fd

    echo "4. Pulling latest code..."
    git pull origin main

    echo "5. Restoring SSL Certificates..."
    mkdir -p data/certbot
    cp -r /tmp/certbot_backup/* data/certbot/
    rm -rf /tmp/certbot_backup

    echo "6. Restarting containers..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d --build

    echo "✅ Server Recovered & Updated!"
EOF

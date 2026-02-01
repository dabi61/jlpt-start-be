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

    echo "2. Check origin..."
    git remote set-url origin https://github.com/dabi61/jlpt-start-be.git

    echo "3. Fetching latest code..."
    git fetch origin main

    echo "4. Hard Resetting (Forcing local to match remote)..."
    git reset --hard origin/main

    echo "5. Cleaning untracked files..."
    git clean -fd

    echo "✅ Code updated to:"
    git log -1 --format="%h - %s (%ci)"

    echo "6. Restoring SSL Certificates..."
    mkdir -p data/certbot
    cp -r /tmp/certbot_backup/* data/certbot/
    rm -rf /tmp/certbot_backup

    echo "7. Restarting containers..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d --build

    echo "🎉 Server Recovered & Updated Successfully!"
EOF

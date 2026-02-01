#!/bin/bash

# Configuration
VPS_USER="root"
VPS_IP="103.152.164.250"
VPS_PORT="22"
PROJECT_DIR="/root/jlpt_start"

echo "🔧 Fixing Server Git State..."

ssh -p $VPS_PORT $VPS_USER@$VPS_IP << EOF
    cd $PROJECT_DIR

    echo "1. Checking out main branch..."
    git checkout main || git checkout -b main

    echo "2. Deleting weird branches if any..."
    git branch -D prod_data_backup.dump 2>/dev/null || true

    echo "3. Removing blocking files..."
    rm -f prod_data_backup.dump
    rm -f *.dump
    rm -f *.sql

    echo "4. Force reseting git..."
    git fetch origin
    git reset --hard origin/main
    git clean -fd

    echo "5. Pulling latest code..."
    git pull origin main

    echo "✅ Server Git is now CLEAN and UP-TO-DATE!"
EOF

#!/bin/bash

# Server Debug Script
VPS_USER="root"
VPS_IP="103.152.164.250"
VPS_PORT="22"
PROJECT_DIR="/root/jlpt_start"

echo "🔍 Checking Server State..."

ssh -p $VPS_PORT $VPS_USER@$VPS_IP << EOF
    cd $PROJECT_DIR
    echo "--- GIT STATUS ---"
    git status

    echo -e "\n--- LAST COMMIT ---"
    git log -1 --format="%h - %s (%ci)"

    echo -e "\n--- URLS.PY CONTENT (First 20 lines) ---"
    head -n 20 apps/learning/urls.py

    echo -e "\n--- DOCKER CONTAINERS ---"
    docker compose ps
EOF

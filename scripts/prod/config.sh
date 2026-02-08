#!/bin/bash

# ==========================================
# 🌍 SERVER CONFIGURATION
# ==========================================

# VPS Connection
VPS_USER="root"
VPS_IP="103.152.164.250"
VPS_PORT="22"

# Paths
PROJECT_DIR="/root/jlpt_start"
COMPOSE_FILE="docker-compose.prod.yml"

# Database
DB_SERVICE="db"
DB_USER="nihongo_user"
DB_NAME="nihongo_db"

# Backup
BACKUP_DIR_REMOTE="/root/backups"
BACKUP_DIR_LOCAL="./backups/prod"

# Colors for Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Helper Function: SSH Command Wrapper
run_remote() {
    ssh -p $VPS_PORT $VPS_USER@$VPS_IP "$1"
}

#!/bin/bash

# Auto Deployment Script
# Targets: Code & Database (Full Overwrite)
# VPS: 103.101.161.229

# Configuration
VPS_USER="root"
VPS_IP="103.152.164.250"
VPS_PORT="22" # <--- Change this if using a custom port (e.g. 2222)
PROJECT_DIR="/root/jlpt_start"
BACKUP_FILE="deploy_full_backup.sql"
COMPOSE_FILE="docker-compose.prod.yml"

# DB Config
DB_USER="nihongo_user"
DB_NAME="nihongo_db"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==========================================${NC}"
echo -e "${YELLOW}🚀 STARTING FULL DEPLOYMENT TO $VPS_IP${NC}"
echo -e "${YELLOW}==========================================${NC}"

# Check git status
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}⚠️  You have uncommitted changes!${NC}"
    echo "Please commit your changes before deploying."
    exit 1
fi

# 1. Git Push
echo -e "\n${YELLOW}[1/4] Pushing code to GitHub...${NC}"
git push origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git push failed. Please check your network or credentials.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Code pushed successfully.${NC}"

# 2. Database Backup
echo -e "\n${YELLOW}[2/4] Creating Local Database Dump...${NC}"
# --clean: Include DROP commands
# --if-exists: Use IF EXISTS for DROP
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME --clean --if-exists > $BACKUP_FILE
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database backup failed. Is Docker running?${NC}"
    rm $BACKUP_FILE 2>/dev/null
    exit 1
fi
echo -e "${GREEN}✅ Database dump created: $BACKUP_FILE${NC}"

# 2.5 Setup Remote Directory (If not exists)
echo -e "\n${YELLOW}[2.5/4] Checking Remote Environment...${NC}"
ssh -p $VPS_PORT $VPS_USER@$VPS_IP << EOF
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "⚠️  Project directory not found. Cloning from Git..."
        git clone https://github.com/dabi61/jlpt-start-be.git $PROJECT_DIR
    else
        echo "✅ Project directory exists."
    fi
EOF

# 3. Upload to VPS
echo -e "\n${YELLOW}[3/4] Uploading Backup to VPS...${NC}"
scp -P $VPS_PORT $BACKUP_FILE $VPS_USER@$VPS_IP:$PROJECT_DIR/$BACKUP_FILE
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ SCP failed. Check your SSH connection.${NC}"
    rm $BACKUP_FILE
    exit 1
fi
echo -e "${GREEN}✅ Upload successful.${NC}"

# 4. Remote Execution
echo -e "\n${YELLOW}[4/4] Executing Remote Deployment...${NC}"
ssh -p $VPS_PORT $VPS_USER@$VPS_IP << EOF
    set -e # Stop on error
    cd $PROJECT_DIR

    echo "   🔹 Pulling latest code..."
    git reset --hard HEAD
    git clean -fd
    git pull origin main

    echo "   🔹 Rebuilding Docker containers..."
    docker compose -f $COMPOSE_FILE down
    docker compose -f $COMPOSE_FILE up -d --build

    echo "   🔹 Waiting for Database (10s)..."
    sleep 10

    echo "   🔹 Restoring Database from backup..."
    cat $BACKUP_FILE | docker compose -f $COMPOSE_FILE exec -T db psql -U $DB_USER $DB_NAME > /dev/null

    echo "   🔹 Cleaning up..."
    rm $BACKUP_FILE

    echo "✅ REMOTE DEPLOYMENT COMPLETE!"
EOF

# Cleanup Local
rm $BACKUP_FILE
echo -e "\n${GREEN}🎉 DEPLOYMENT FINISHED SUCCESSFULLY!${NC}"

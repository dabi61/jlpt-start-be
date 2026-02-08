#!/bin/bash

# Load Config
source $(dirname "$0")/config.sh

echo -e "${BLUE}💾 Starting Remote Database Backup...${NC}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REMOTE_FILE="$BACKUP_DIR_REMOTE/db_backup_$TIMESTAMP.sql"
LOCAL_FILE="$BACKUP_DIR_LOCAL/db_backup_$TIMESTAMP.sql"

# 1. Ensure directories exist
mkdir -p $BACKUP_DIR_LOCAL
run_remote "mkdir -p $BACKUP_DIR_REMOTE"

# 2. Dump Database on Server
echo -e "   🔹 Dumping database on server..."
run_remote "docker compose -f $PROJECT_DIR/$COMPOSE_FILE exec -T $DB_SERVICE pg_dump -U $DB_USER $DB_NAME > $REMOTE_FILE"

# 3. Download to Local
echo -e "   🔹 Downloading to local machine..."
scp -P $VPS_PORT $VPS_USER@$VPS_IP:$REMOTE_FILE $LOCAL_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup saved to: $LOCAL_FILE${NC}"
    # Optional: Clean up remote file to save space
    # run_remote "rm $REMOTE_FILE"
else
    echo -e "${RED}❌ Backup download failed.${NC}"
fi

#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"

mkdir -p $BACKUP_DIR

echo -e "${BLUE}💾 Creating Database Backup...${NC}"

# Check if db container is running
if [ -z "$(docker compose ps -q db)" ]; then
    echo -e "${RED}❌ Database container is not running.${NC}"
    exit 1
fi

# Get DB credentials from env or use defaults
DB_USER=${POSTGRES_USER:-nihongo_user}
DB_NAME=${POSTGRES_DB:-nihongo_db}

docker compose exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup created successfully: ${BACKUP_FILE}${NC}"
    # Keep only last 5 backups
    ls -t $BACKUP_DIR/*.sql | tail -n +6 | xargs rm -f 2>/dev/null
else
    echo -e "${RED}❌ Backup failed.${NC}"
    rm -f $BACKUP_FILE
    exit 1
fi

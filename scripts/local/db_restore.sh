#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="backups"

echo -e "${BLUE}♻️  Database Restore Utility${NC}"

# List recent backups
echo -e "\nAvailable backups:"
ls -lh $BACKUP_DIR/*.sql 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ No backups found in ${BACKUP_DIR}/${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Enter backup filename to restore (e.g., backups/db_backup_20240101.sql):${NC}"
read BACKUP_FILE

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ File not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will overwrite the current database! Are you sure? (y/N)${NC}"
read CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Get DB credentials
DB_USER=${POSTGRES_USER:-nihongo_user}
DB_NAME=${POSTGRES_DB:-nihongo_db}

echo -e "${BLUE}Restoring from ${BACKUP_FILE}...${NC}"
# Drop and recreate schema or just restore (pg_restore might be better for binary format, but we used pg_dump plain text)
# For plain text sql dump:
cat $BACKUP_FILE | docker compose exec -T db psql -U $DB_USER -d $DB_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database restored successfully.${NC}"
else
    echo -e "${RED}❌ Restore failed.${NC}"
    exit 1
fi

#!/bin/bash

# Load Config
source $(dirname "$0")/config.sh

echo -e "${BLUE}🚀 STARTING DEPLOYMENT TO $VPS_IP${NC}"

# 1. Check Git Status
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}⚠️  You have uncommitted changes!${NC}"
    echo "Please commit your changes before deploying."
    exit 1
fi

# 2. Push Code
echo -e "\n${BLUE}[1/4] Pushing code to GitHub...${NC}"
git push origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git push failed.${NC}"
    exit 1
fi

# 3. Create Remote Backup (Safety First)
echo -e "\n${BLUE}[2/4] Taking Database Backup...${NC}"
BACKUP_FILE="${BACKUP_DIR_REMOTE}/pre_deploy_$(date +%Y%m%d_%H%M%S).sql"
run_remote "mkdir -p $BACKUP_DIR_REMOTE && docker compose -f $PROJECT_DIR/$COMPOSE_FILE exec -T $DB_SERVICE pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE"
echo -e "${GREEN}✅ Backup saved to: $BACKUP_FILE${NC}"

# 4. Remote Deployment
echo -e "\n${BLUE}[3/4] Updating Server...${NC}"
run_remote "
    set -e
    cd $PROJECT_DIR

    echo '   🔹 Pulling latest code...'
    git pull origin main

    echo '   🔹 Rebuilding containers...'
    docker compose -f $COMPOSE_FILE down
    docker compose -f $COMPOSE_FILE up -d --build

    echo '   🔹 Running Migrations...'
    docker compose -f $COMPOSE_FILE exec -T web python manage.py migrate

    echo '   🔹 Collecting Static Files...'
    docker compose -f $COMPOSE_FILE exec -T web python manage.py collectstatic --noinput

    echo '   🔹 Pruning unused images...'
    docker image prune -f
"

echo -e "\n${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"

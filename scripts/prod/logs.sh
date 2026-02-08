#!/bin/bash

# Load Config
source $(dirname "$0")/config.sh

SERVICE=${1:-web} # Default to 'web' if no argument provided

echo -e "${BLUE}📡 Connecting to Server Logs ($SERVICE)...${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"

ssh -p $VPS_PORT -t $VPS_USER@$VPS_IP "cd $PROJECT_DIR && docker compose -f $COMPOSE_FILE logs -f --tail=100 $SERVICE"

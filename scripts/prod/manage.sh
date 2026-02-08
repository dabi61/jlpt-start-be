#!/bin/bash

# Load Config
source $(dirname "$0")/config.sh

CMD=$@ # Get all arguments

if [ -z "$CMD" ]; then
    echo -e "${YELLOW}Usage: ./manage.sh <command>${NC}"
    echo -e "Example: ./manage.sh migrate"
    exit 1
fi

echo -e "${BLUE}🛠 Running remote Django command: $CMD${NC}"

ssh -p $VPS_PORT -t $VPS_USER@$VPS_IP "cd $PROJECT_DIR && docker compose -f $COMPOSE_FILE exec web python manage.py $CMD"

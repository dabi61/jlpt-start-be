#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Running Tests...${NC}"

# Check if container is running
if [ -z "$(docker compose ps -q web)" ]; then
    echo -e "${RED}❌ Web container is not running. Please start the server first.${NC}"
    exit 1
fi

docker compose exec web python manage.py test

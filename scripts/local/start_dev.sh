#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Development Server...${NC}"
docker compose up -d

echo -e "\n${GREEN}✅ Server running!${NC}"
echo -e "Web: http://localhost:8000"
echo -e "Admin: http://localhost:8000/admin/"
echo -e "API Docs: http://localhost:8000/api/docs/"

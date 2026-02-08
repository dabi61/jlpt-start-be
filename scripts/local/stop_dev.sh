#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Development Server...${NC}"
docker compose down

echo -e "${GREEN}✅ Server stopped.${NC}"

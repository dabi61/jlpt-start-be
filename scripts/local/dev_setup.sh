#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Development Setup...${NC}"

# 1. Check Prerequisites
echo -e "\n${BLUE}[1/5] Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed.${NC}"
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Prerequisites met.${NC}"

# 2. Environment Setup
echo -e "\n${BLUE}[2/5] Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env from .env.example${NC}"
    echo -e "${YELLOW}⚠️  Please update .env with your specific configuration if needed.${NC}"
else
    echo -e "${GREEN}✅ .env already exists.${NC}"
fi

# 3. Build Docker Containers
echo -e "\n${BLUE}[3/5] Building Docker containers...${NC}"
docker compose build
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker build successful.${NC}"

# 4. Starting Services
echo -e "\n${BLUE}[4/5] Starting services...${NC}"
docker compose up -d
echo -e "${GREEN}✅ Services started.${NC}"

# 5. Migrations & Static Files
echo -e "\n${BLUE}[5/5] Running migrations and collecting static files...${NC}"
echo "Waiting for database to be ready..."
sleep 5
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput

echo -e "\n${GREEN}🎉 Development environment setup complete!${NC}"
echo -e "Access the site at: http://localhost:8000"
echo -e "API Documentation: http://localhost:8000/api/docs/"

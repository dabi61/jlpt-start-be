#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📦 Importing Data...${NC}"

# Check if container is running
if [ -z "$(docker compose ps -q web)" ]; then
    echo -e "${RED}❌ Web container is not running. Please start the server first.${NC}"
    exit 1
fi

# 1. Import Vocabulary
echo -e "\n${BLUE}[1/4] Importing Vocabulary...${NC}"
docker compose exec web python manage.py import_vocabulary
# Or specific levels if needed: docker compose exec web python manage.py import_vocabulary --level N5

# 2. Import Kanji
echo -e "\n${BLUE}[2/4] Importing Kanji...${NC}"
docker compose exec web python manage.py import_kanji

# 3. Import Grammar (Assuming command exists or similar)
# echo -e "\n${BLUE}[3/4] Importing Grammar...${NC}"
# docker compose exec web python manage.py import_grammar

# 4. Create Lessons Structure
echo -e "\n${BLUE}[4/4] Creating Lessons Structure...${NC}"
docker compose exec web python manage.py create_jlpt_lessons

echo -e "\n${GREEN}✅ Data import complete!${NC}"

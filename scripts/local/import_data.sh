#!/bin/bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📦 Importing Data...${NC}"

# Check if container is running
if [ -z "$(docker compose ps -q web)" ]; then
    echo -e "${RED}❌ Web container is not running. Please start the server first.${NC}"
    exit 1
fi

run_if_exists() {
    local file_path="$1"
    shift
    if [ -f "$file_path" ]; then
        "$@"
    else
        echo -e "${YELLOW}⚠️  Skip (missing file): $file_path${NC}"
    fi
}

# 1. Import Vocabulary
echo -e "\n${BLUE}[1/5] Importing Vocabulary...${NC}"
run_if_exists "data/javi.json" docker compose exec web python manage.py import_javi --json-file data/javi.json

# 2. Import Kanji
echo -e "\n${BLUE}[2/5] Importing Kanji...${NC}"
run_if_exists "data/kanji.json" docker compose exec web python manage.py import_kanji data/kanji.json --update

# 3. Import Grammar
echo -e "\n${BLUE}[3/5] Importing Grammar...${NC}"
run_if_exists "data/grammar.json" docker compose exec web python manage.py import_grammar data/grammar.json --update --clean-html

# 4. Import Examples
echo -e "\n${BLUE}[4/5] Importing Examples...${NC}"
run_if_exists "data/example.json" docker compose exec web python manage.py import_examples data/example.json --update --preserve-ids

# 5. Create Lessons Structure
echo -e "\n${BLUE}[5/5] Creating Lessons Structure...${NC}"
docker compose exec web python manage.py create_jlpt_lessons

echo -e "\n${GREEN}✅ Data import complete!${NC}"

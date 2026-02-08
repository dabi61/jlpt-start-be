#!/bin/bash

# Load Config
source $(dirname "$0")/config.sh

echo -e "${BLUE}🏗 Initializing Server Setup...${NC}"

run_remote "
    # 1. Update System
    echo '🔹 Updating system packages...'
    apt-get update && apt-get upgrade -y
    apt-get install -y curl git ufw

    # 2. Install Docker
    if ! command -v docker &> /dev/null; then
        echo '🔹 Installing Docker...'
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
    else
        echo '✅ Docker already installed.'
    fi

    # 3. Setup Project Directory
    if [ ! -d \"$PROJECT_DIR\" ]; then
        echo '🔹 Cloning project...'
        git clone https://github.com/dabi61/jlpt-start-be.git $PROJECT_DIR
    else
        echo '✅ Project directory exists.'
    fi

    # 4. Create .env file (Placeholder)
    if [ ! -f \"$PROJECT_DIR/.env\" ]; then
        echo '⚠️  Creating empty .env file. Please populate it manually!'
        touch $PROJECT_DIR/.env
    fi

    # 5. Create Backup Directory
    mkdir -p $BACKUP_DIR_REMOTE

    echo '✅ Server Setup Complete!'
    echo 'Next steps:'
    echo '1. SSH into server and edit .env file'
    echo '2. Run ./scripts/prod/deploy.sh'
"

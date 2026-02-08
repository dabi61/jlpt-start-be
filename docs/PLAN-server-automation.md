# Server Automation & Deployment Plan (Revised)

> **Mục tiêu:** Xây dựng bộ script automation chuyên nghiệp cho cả Local (Dev) và Production (Server), được tách biệt rõ ràng.

---

## Folder Structure

```
scripts/
├── local/              # Scripts cho môi trường Dev chạy trên máy cá nhân
│   ├── dev_setup.sh
│   ├── start_dev.sh
│   ├── stop_dev.sh
│   ├── run_tests.sh
│   ├── import_data.sh
│   ├── db_backup.sh    (Local backup)
│   └── db_restore.sh   (Local restore)
│
└── prod/               # Scripts cho môi trường Production (VPS)
    ├── config.sh       # Shared config (IP, User, Path...)
    ├── server_setup.sh # Run once to install Docker/Nginx/Certbot
    ├── deploy.sh       # Auto deploy (Zero-downtime attempt)
    ├── logs.sh         # View server logs from local
    ├── manage.sh       # Run remote management commands
    └── backup.sh       # Backup remote database to local
```

---

## Production Scripts Detail (`scripts/prod/`)

### 1. Configuration (`scripts/prod/config.sh`)
Centralized configuration to avoid hardcoding in every script.
```bash
VPS_USER="root"
VPS_IP="103.152.164.250"
VPS_PORT="22"
PROJECT_DIR="/root/jlpt_start"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR_REMOTE="/root/backups"
BACKUP_DIR_LOCAL="./backups/prod"
```

### 2. Server Provisioning (`scripts/prod/server_setup.sh`)
Automates the initial server setup.
- Updates system
- Installs Docker & Docker Compose
- Installs Nginx & Certbot
- Configures Firewall (UFW) allowing 22, 80, 443
- Sets up project directory structure

### 3. Deployment (`scripts/prod/deploy.sh`)
The workhorse script for updates.
- **Step 1:** Push local changes to Git
- **Step 2:** SSH to server
- **Step 3:** Pull changes
- **Step 4:** Build & Restart
  ```bash
  docker compose -f docker-compose.prod.yml down
  docker compose -f docker-compose.prod.yml up -d --build
  ```
- **Step 5:** Prune unused Docker images

### 4. Remote Logs (`scripts/prod/logs.sh`)
View logs without manually SSH-ing.
```bash
./scripts/prod/logs.sh web
./scripts/prod/logs.sh db
```

### 5. Remote Management (`scripts/prod/manage.sh`)
Run Django commands on the remote server.
```bash
./scripts/prod/manage.sh migrate
./scripts/prod/manage.sh createsuperuser
```

### 6. Remote Backup (`scripts/prod/backup.sh`)
Backup production database and download to local machine.
- Pg_dump on server -> Save to remote backup dir
- Scp to local `backups/prod/` folder

---

## Verification Plan

### Local Scripts
- Verify files moved correctly to `scripts/local/`
- Run `./scripts/local/start_dev.sh` to ensure they still work (paths might need adjustment if they reference files relatively)

### Production Scripts (Dry Run)
- Check syntax of all `.sh` files
- Review variable expansion in SSH commands
- Create a `scripts/README.md` to document usage

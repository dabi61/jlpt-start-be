# JLPT Start Backend 🚀

Backend API cho ứng dụng học tiếng Nhật JLPT Start, xây dựng trên Django REST Framework.

## 🌟 Features
- **Authentication**: JWT, Social Login (Google, Facebook).
- **Learning Materials**: Vocabulary, Kanji, Grammar, Listenings (N5-N1).
- **Progress Tracking**: User lesson/unit progress.
- **Infrastructure**: Dockerized, Nginx, Redis, Celery, PostgreSQL.

---

## 📂 Project Structure
```
jlpt-start-be/
├── apps/               # Django Apps (users, vocabulary, etc.)
├── core/               # Settings
├── data/               # Raw JSON data
├── scripts/
│   ├── local/          # 🛠 DEVELOPMENT SCRIPTS
│   │   ├── start_dev.sh
│   │   ├── stop_dev.sh
│   │   ├── run_tests.sh
│   │   └── import_data.sh
│   └── prod/           # 🚀 PRODUCTION SCRIPTS
│       ├── config.sh       # Server Config
│       ├── deploy.sh       # Auto Deploy
│       ├── logs.sh         # View Logs
│       ├── manage.sh       # Remote Command
│       └── backup.sh       # Backup DB
└── docker-compose.yml
```

---

## 🛠 Development (Local)

### Quick Start
```bash
# 1. Setup Environment
./scripts/local/start_dev.sh

# 2. Stop Environment
./scripts/local/stop_dev.sh
```

### Common Tasks
- **Run Tests**: `./scripts/local/run_tests.sh`
- **Import Sample Data**: `./scripts/local/import_data.sh`

---

## 🚀 Deployment (Production)

To manage the production server without SSH-ing manually.

### 1. Configuration
Check `scripts/prod/config.sh` to correct IP/User/Path.

### 2. Deployment
Deploy latest code from GitHub `main` branch:
```bash
./scripts/prod/deploy.sh
```

### 2.1 Auto Deploy With GitHub Actions

Repository now includes workflow:
- `.github/workflows/deploy-production.yml`

It runs on:
- push to `main`
- manual trigger (`workflow_dispatch`)

Required GitHub Repository Secrets:
- `VPS_HOST`
- `VPS_PORT`
- `VPS_USER`
- `VPS_SSH_KEY` (private key for SSH)
- `VPS_PROJECT_DIR` (optional, default: `/root/jlpt_start`)
- `VPS_COMPOSE_FILE` (optional, default: `docker-compose.prod.yml`)

Deploy steps executed on server:
- `git fetch` + `git reset --hard origin/main`
- `docker compose up -d --build`
- `python manage.py migrate`
- `python manage.py collectstatic --noinput`
- `docker image prune -f`

### 3. Server Management
- **View Logs**:
  ```bash
  ./scripts/prod/logs.sh web
  ./scripts/prod/logs.sh nginx
  ```
- **Run Django Commands**:
  ```bash
  ./scripts/prod/manage.sh migrate
  ./scripts/prod/manage.sh createsuperuser
  ```
- **Backup Database**:
  ```bash
  ./scripts/prod/backup.sh
  ```
  *(Backups are saved to `backups/prod/` locally)*

### 4. Initial Setup (Fresh Server)
Only for new servers:
```bash
./scripts/prod/server_setup.sh
```

---

## 🔧 API Documentation
- **Swagger**: `/api/docs/`
- **Redoc**: `/api/redoc/`

## 📝 License
MIT License.

# README & Automation Scripts Plan

> **Mục tiêu:** Tạo README tổng quan và các script automation còn thiếu cho dự án JLPT Learning Backend.

---

## Project Analysis Summary

### Tech Stack
- **Framework:** Django 5.0 + Django REST Framework
- **Database:** PostgreSQL 16
- **Cache/Queue:** Redis 7 + Celery
- **Server:** Gunicorn + Nginx
- **Container:** Docker + Docker Compose
- **Auth:** JWT (dj-rest-auth + allauth)
- **API Docs:** drf-spectacular (Swagger/ReDoc)
- **Admin:** django-jazzmin

### Django Apps (7 apps)
| App | Description | Key Models |
|-----|-------------|------------|
| `users` | User authentication & profiles | `User` (custom, email-based) |
| `vocabulary` | Japanese vocabulary | `Word` (JLPT N1-N6) |
| `kanjis` | Kanji characters | `Kanji` |
| `grammar` | Grammar points | `Grammar` |
| `learning` | Lessons & progress | `Lesson`, `Unit`, `UserUnitProgress` |
| `courses` | Course management | - |
| `examples` | Example sentences | `Example` |

### Existing Scripts
| Script | Purpose |
|--------|---------|
| `deploy_full.sh` | Full deployment to VPS (code + DB sync) |
| `debug_server.sh` | Check server state via SSH |
| `entrypoint.sh` | Docker entrypoint (migrations + static) |
| `init-letsencrypt.sh` | SSL certificate setup |
| `fix_server.sh` | Server troubleshooting |

### Management Commands
| Command | App | Purpose |
|---------|-----|---------|
| `import_vocabulary` | vocabulary | Import vocab from JSON |
| `import_javi_content` | vocabulary | Import Javi content |
| `fetch_jlpt_levels` | vocabulary | Fetch JLPT data from API |
| `import_kanji` | kanjis | Import kanji from JSON |
| `fetch_kanji_levels` | kanjis | Fetch kanji from API |
| `create_jlpt_lessons` | learning | Create lessons structure |
| `import_learning_data` | learning | Import learning data |
| `import_book_sets` | learning | Import book sets |

---

## Proposed Changes

### 1. README.md Update

#### [MODIFY] [README.md](file:///Users/macbook/Documents/Workspace/startjlpt_be/README.md)

Comprehensive README with:
- Project description & features
- Tech stack overview
- Project structure diagram
- Quick start guide (Docker & local)
- Environment variables
- API endpoints reference
- Management commands
- Development workflow
- Deployment guide

---

### 2. New Automation Scripts

#### [NEW] [scripts/dev_setup.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/dev_setup.sh)

One-command development environment setup:
```bash
#!/bin/bash
# 1. Check prerequisites (Docker, Python)
# 2. Copy .env.example to .env
# 3. Build Docker containers
# 4. Run migrations
# 5. Create superuser (optional)
```

#### [NEW] [scripts/start_dev.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/start_dev.sh)

Start development server:
```bash
#!/bin/bash
# Start Docker containers in development mode
docker compose up -d
```

#### [NEW] [scripts/stop_dev.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/stop_dev.sh)

Stop development server:
```bash
#!/bin/bash
# Stop Docker containers
docker compose down
```

#### [NEW] [scripts/db_backup.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/db_backup.sh)

Database backup utility:
```bash
#!/bin/bash
# 1. Create timestamped backup
# 2. Save to backups/ folder
# 3. Keep last N backups
```

#### [NEW] [scripts/db_restore.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/db_restore.sh)

Database restore utility:
```bash
#!/bin/bash
# 1. List available backups
# 2. Restore selected backup
```

#### [NEW] [scripts/import_all_data.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/import_all_data.sh)

Import all data from JSON files:
```bash
#!/bin/bash
# 1. Import vocabulary
# 2. Import kanji
# 3. Import grammar
# 4. Create lessons
```

#### [NEW] [scripts/run_tests.sh](file:///Users/macbook/Documents/Workspace/startjlpt_be/scripts/run_tests.sh)

Run test suite:
```bash
#!/bin/bash
# Run Django tests
docker compose exec web python manage.py test
```

---

## Verification Plan

### Manual Verification
1. **README Review:**
   - Open README.md and verify all sections are complete
   - Check all commands work as documented

2. **Script Testing:**
   - Run each script and verify it works
   - Test on fresh environment if possible

### Script Tests
```bash
# Test dev setup (requires fresh environment)
./scripts/dev_setup.sh

# Test start/stop
./scripts/start_dev.sh
./scripts/stop_dev.sh

# Test backup
./scripts/db_backup.sh
ls backups/

# Test restore
./scripts/db_restore.sh <backup_file>
```

---

## Notes

- All scripts will be executable (`chmod +x`)
- Scripts will have error handling and colored output
- README will be bilingual (Vietnamese/English) where appropriate

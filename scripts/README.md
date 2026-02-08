# Automation Scripts Guide

This directory contains automation scripts to streamline development and deployment tasks.

## 📂 Structure

- **`local/`**: Scripts for local development environment (your machine).
- **`prod/`**: Scripts for production environment (VPS server).

---

## 🛠 Local Scripts (`local/`)

Used for running the project on your machine with Docker.

| Script | Command | Description |
|--------|---------|-------------|
| **Start Dev** | `./local/start_dev.sh` | Starts Docker containers in background. |
| **Stop Dev** | `./local/stop_dev.sh` | Stops all containers. |
| **Setup** | `./local/dev_setup.sh` | Full setup (Build, Migrate, CollectStatic). |
| **Run Tests** | `./local/run_tests.sh` | Runs Django unit tests. |
| **Import Data** | `./local/import_data.sh` | Imports sample data (Vocab, Kanji...). |

---

## 🚀 Production Scripts (`prod/`)

Used to manage the remote VPS server from your local machine.

**Configuration**: Edit `prod/config.sh` to set IP, User, and Paths.

| Script | Command | Description |
|--------|---------|-------------|
| **Deploy** | `./prod/deploy.sh` | Git Push -> SSH -> Git Pull -> Build -> Restart. |
| **Logs** | `./prod/logs.sh <service>` | View real-time logs (e.g., `./prod/logs.sh web`). |
| **Manage** | `./prod/manage.sh <cmd>` | Run management command (e.g., `./prod/manage.sh migrate`). |
| **Backup** | `./prod/backup.sh` | Backup remote DB & download to `backups/prod/`. |
| **Setup** | `./prod/server_setup.sh` | Initial server setup (Docker, Nginx). Run once. |

---

## ⚠️ Important Notes

1. **Permissions**: Ensure scripts are executable:
   ```bash
   chmod +x local/*.sh prod/*.sh
   ```

2. **SSH Keys**: Production scripts require SSH access to the VPS. Ensure your public key is added to the server's `~/.ssh/authorized_keys`.

3. **Data Import**: Data import scripts in `local/` are destructive/additive. Use with caution.

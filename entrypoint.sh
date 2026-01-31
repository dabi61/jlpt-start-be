#!/bin/sh

# Wait for postgres
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Exec the container's main process (what's set as CMD in Dockerfile)
exec "$@"

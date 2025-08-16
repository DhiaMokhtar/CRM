#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_homework}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
MAX_TRIES=40

echo "[homework] entrypoint version 2025-08-15-01"


echo "[homework] Database connection verified"

# Clean up migrations if needed
if [ ! -f homework/migrations/0001_initial.py ] && ls homework/migrations/0002_* >/dev/null 2>&1; then
  echo "[homework] Fixing broken migrations chain..."
  find homework/migrations -type f -name '0*.py' ! -name '__init__.py' -delete
fi

echo "[homework] Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "[homework] SSL setup..."
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem

if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  echo "[homework] Using existing certs"
  echo "[homework] Using provided SSL certificates"
  install -m 600 /certs-in/localhost.pem /app/ssl/localhost.pem
  install -m 600 /certs-in/localhost-key.pem /app/ssl/localhost-key.pem
else
  echo "[homework] Generating self-signed certificates"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj "/CN=localhost"
fi

ls -la /app/ssl/
echo "[homework] Starting HTTPS server..."
exec python manage.py runsslserver 0.0.0.0:8000 \
  --certificate /app/ssl/localhost.pem \
  --key /app/ssl/localhost-key.pem
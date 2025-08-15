#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_courses}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
MAX_TRIES=40



echo "[courses] Migrations"
python manage.py makemigrations
python manage.py migrate

echo "[courses] Collect static"
python manage.py collectstatic --noinput

echo "[courses] SSL setup"
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  install -m 600 /certs-in/localhost.pem /app/ssl/localhost.pem
  install -m 600 /certs-in/localhost-key.pem /app/ssl/localhost-key.pem
else
  echo "[courses] Generating self-signed cert"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj "/CN=localhost"
fi
ls -l /app/ssl
echo "[courses] Starting HTTPS server"
exec python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
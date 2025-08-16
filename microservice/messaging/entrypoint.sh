#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_messaging}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
MAX_TRIES=60

echo "$(date +'%F %T') | [messaging] entrypoint version 2025-08-15-02"
echo "$(date +'%F %T') | [messaging] Waiting for MySQL at $DB_HOST user=$DB_USER"
echo "$(date +'%F %T') | [messaging] DNS: $(getent hosts "$DB_HOST" || echo 'NOT FOUND')"



echo "[messaging] Database connection verified"
echo "[messaging] Migrations"
python manage.py makemigrations
python manage.py migrate

echo "[messaging] SSL setup"
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  echo "[messaging] Using existing certs"
  echo "[messaging] Using provided SSL certificates"
  install -m 600 /certs-in/localhost.pem /app/ssl/localhost.pem
  install -m 600 /certs-in/localhost-key.pem /app/ssl/localhost-key.pem
else
  echo "[messaging] Generating self-signed cert"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj "/CN=localhost"
fi

ls -la /app/ssl/
echo "[messaging] Starting HTTPS server..."
exec python manage.py runsslserver 0.0.0.0:8000 \
  --certificate /app/ssl/localhost.pem \
  --key /app/ssl/localhost-key.pem
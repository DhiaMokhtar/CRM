#!/usr/bin/env bash
set -e

echo "[entrypoint] Starting users_service"

DB_HOST="${DB_HOST:-mysql_users}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-crm_password}"
MAX_TRIES=40

echo "[entrypoint] Waiting for MySQL at $DB_HOST ..."
for i in $(seq 1 $MAX_TRIES); do
  if mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent; then
    echo "[entrypoint] MySQL is alive"
    break
  fi
  echo "[entrypoint] Attempt $i/$MAX_TRIES: MySQL not ready"
  sleep 2
done

if ! mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent; then
  echo "[entrypoint] ERROR: MySQL never became ready"
  exit 1
fi

echo "[entrypoint] Running migrations"
python manage.py makemigrations
python manage.py migrate

echo "[entrypoint] Preparing SSL certs"
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  install -m 600 /certs-in/localhost.pem /app/ssl/localhost.pem
  install -m 600 /certs-in/localhost-key.pem /app/ssl/localhost-key.pem
else
  echo "[entrypoint] Mounted certs missing -> generating self-signed cert"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj "/CN=localhost"
fi
ls -la /app/ssl

echo "[entrypoint] Launching Django HTTPS server"
exec python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
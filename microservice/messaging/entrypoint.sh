#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_messaging}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
MAX_TRIES=40

echo "[messaging] Waiting for MySQL at $DB_HOST..."
for i in $(seq 1 $MAX_TRIES); do
  if mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent; then
    echo "[messaging] MySQL ready"; break
  fi
  echo "[messaging] Attempt $i/$MAX_TRIES"; sleep 2
done
mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent || { echo "[messaging] DB not reachable"; exit 1; }

echo "[messaging] Migrations"
python manage.py makemigrations
python manage.py migrate

echo "[messaging] SSL setup"
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  install -m 600 /certs-in/localhost.pem /app/ssl/localhost.pem
  install -m 600 /certs-in/localhost-key.pem /app/ssl/localhost-key.pem
else
  echo "[messaging] Generating self-signed cert"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj "/CN=localhost"
fi
ls -l /app/ssl
echo "[messaging] Starting HTTPS server"
exec python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
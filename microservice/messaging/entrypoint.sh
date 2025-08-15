#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_messaging}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
MAX_TRIES=60

echo "$(date +'%F %T') | [messaging] entrypoint version 2025-08-15-02"
echo "$(date +'%F %T') | [messaging] Waiting for MySQL at $DB_HOST user=$DB_USER"
echo "$(date +'%F %T') | [messaging] DNS: $(getent hosts "$DB_HOST" || echo 'NOT FOUND')"

for i in $(seq 1 $MAX_TRIES); do
  # Test network connectivity first
  if ! (echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1; then
    if (( i % 5 == 0 )); then
      echo "$(date +'%F %T') | [messaging] Network connectivity failed (attempt $i/$MAX_TRIES)"
    fi
    sleep 2
    continue
  fi
  
  # Test MySQL connection
  if mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
    echo "$(date +'%F %T') | [messaging] MySQL ready after $i attempt(s)"
    break
  fi
  
  if (( i % 5 == 0 )); then
    echo "$(date +'%F %T') | [messaging] MySQL ping failed (attempt $i/$MAX_TRIES)"
    echo "$(date +'%F %T') | [messaging] Port 3306 open"
  fi
  sleep 2
done

if ! mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
  echo "[messaging] ERROR: DB not reachable with user=$DB_USER"
  echo "[messaging] Final diagnostics:"
  echo "[messaging] Network test: $((echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1 && echo 'OK' || echo 'FAILED')"
  echo "[messaging] DNS test: $(getent hosts "$DB_HOST" 2>/dev/null || echo 'FAILED')"
  exit 1
fi

echo "[messaging] Database connection verified"
echo "[messaging] Migrations"
python manage.py makemigrations
python manage.py migrate

echo "[messaging] SSL setup"
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
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
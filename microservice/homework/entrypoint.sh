#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_homework}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
MAX_TRIES=40

echo "[homework] entrypoint version 2025-08-15-01"
echo "[homework] Waiting for MySQL at $DB_HOST user=$DB_USER..."

# Network diagnostics
echo "[homework] Network diagnostics:"
echo "[homework] DNS lookup: $(getent hosts "$DB_HOST" 2>/dev/null || echo 'FAILED')"

for i in $(seq 1 $MAX_TRIES); do
  # Test network connectivity first
  if ! (echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1; then
    if (( i % 5 == 0 )); then
      echo "[homework] Network connectivity failed (attempt $i/$MAX_TRIES)"
    fi
    sleep 3
    continue
  fi
  
  # Test MySQL connection
  if mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
    echo "[homework] MySQL ready after $i attempts"
    break
  fi
  
  if (( i % 5 == 0 )); then
    echo "[homework] MySQL ping failed (attempt $i/$MAX_TRIES)"
  fi
  
  sleep 3
done

# Final verification
if ! mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
  echo "[homework] FATAL: Cannot connect to MySQL after $MAX_TRIES attempts"
  echo "[homework] Network test: $((echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1 && echo 'OK' || echo 'FAILED')"
  echo "[homework] DNS test: $(getent hosts "$DB_HOST" 2>/dev/null || echo 'FAILED')"
  exit 1
fi

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
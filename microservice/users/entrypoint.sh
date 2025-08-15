#!/usr/bin/env bash
set -euo pipefail

echo "$(date +'%F %T') | [users] entrypoint version 2025-08-12-06"

DB_HOST="${DB_HOST:-mysql_users}"
DB_USER="${DB_USER:-crm_user}"
DB_PASSWORD="${DB_PASSWORD:-crm_password}"
DB_NAME="${DB_NAME:-users_db}"
ROOT_PW="${ROOT_PASSWORD:-crm_password}"
MAX_TRIES="${MAX_TRIES:-60}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"

# Set MySQL password environment
export MYSQL_PWD="$DB_PASSWORD"

SSL_ARGS="--ssl-mode=DISABLED"
echo "[users] Using SSL args: $SSL_ARGS"

echo "[users] Network check:"
(getent hosts "$DB_HOST" || true) | awk '{print $1,$2}'

echo "$(date +'%F %T') | [users] Waiting for MySQL at $DB_HOST user=$DB_USER db=$DB_NAME"

attempt=0
while (( attempt < MAX_TRIES )); do
  if mysqladmin ping $SSL_ARGS --protocol=TCP -h "$DB_HOST" -u "$DB_USER" --silent 2>/dev/null; then
    echo "[users] MySQL ready after $((attempt+1)) attempt(s)"
    break
  fi
  ((attempt++))
  if (( attempt % 5 == 0 )); then
    echo "[users] Attempt $attempt/$MAX_TRIES still failing"
    echo "  Port check: $((echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1 && echo YES || echo NO)"
    mysqladmin ping $SSL_ARGS --protocol=TCP -h "$DB_HOST" -u "$DB_USER" 2>&1 || true
  fi
  if (( attempt == MAX_TRIES )); then
    echo "[users] FATAL: Could not reach MySQL"
    exit 1
  fi
  sleep 2
done

echo "[users] Testing simple query..."
mysql $SSL_ARGS -h "$DB_HOST" -u "$DB_USER" -e "SELECT 1;" || {
  echo "[users] ERROR: Query test failed"
  exit 1
}

echo "[users] Ensuring database exists..."
MYSQL_PWD="$ROOT_PW" mysql $SSL_ARGS -h "$DB_HOST" -u root -e \
  "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`; GRANT ALL ON \`$DB_NAME\`.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD'; FLUSH PRIVILEGES;" || \
  echo "[users] DB setup skipped"

if [[ "$RUN_MIGRATIONS" == "true" ]]; then
  echo "[users] Running migrations..."
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput --clear || true
fi

echo "[users] SSL certificate setup..."
mkdir -p /app/ssl
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  echo "[users] Using provided SSL certificates"
  install -m 600 /certs-in/localhost.pem /app/ssl/
  install -m 600 /certs-in/localhost-key.pem /app/ssl/
else
  echo "[users] Generating self-signed SSL certificate..."
  openssl req -x509 -nodes -newkey rsa:2048 -days 7 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj '/CN=localhost' 2>/dev/null || echo "[users] SSL generation failed"
  chmod 600 /app/ssl/localhost*.pem 2>/dev/null || true
fi

echo "[users] Starting Django server..."
# Check if django-sslserver is available
if python -c "import sslserver" 2>/dev/null; then
  echo "[users] Using SSL server"
  if [ $# -eq 0 ]; then
    exec python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
  else
    exec "$@"
  fi
else
  echo "[users] Using development server"
  if [ $# -eq 0 ]; then
    exec python manage.py runserver 0.0.0.0:8000
  else
    exec "$@"
  fi
fi
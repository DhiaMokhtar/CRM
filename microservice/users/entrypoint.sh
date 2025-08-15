#!/usr/bin/env bash
set -euo pipefail

echo "$(date +'%F %T') | [users] entrypoint version 2025-08-12-04"

DB_HOST="${DB_HOST:-mysql_users}"
DB_USER="${DB_USER:-crm_user}"
DB_PASSWORD="${DB_PASSWORD:-crm_password}"
DB_NAME="${DB_NAME:-users_db}"
ROOT_PW="${ROOT_PASSWORD:-crm_password}"
MAX_TRIES="${MAX_TRIES:-60}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"

# Avoid showing password in command args (mysql / mysqladmin honor MYSQL_PWD)
export MYSQL_PWD="$DB_PASSWORD"
export MYSQL_PWD_ROOT="$ROOT_PW"

MYSQL_SSL_MODE="${MYSQL_SSL_MODE:-DISABLED}"
MYSQL_SSL_CA="${MYSQL_SSL_CA:-}"
SSL_ARGS=""
case "$MYSQL_SSL_MODE" in
  DISABLED)         SSL_ARGS="--ssl-mode=DISABLED" ;;
  PREFERRED)        SSL_ARGS="--ssl-mode=PREFERRED" ;;
  REQUIRED)         SSL_ARGS="--ssl-mode=REQUIRED" ;;
  VERIFY_CA)        SSL_ARGS="--ssl-mode=VERIFY_CA ${MYSQL_SSL_CA:+--ssl-ca=$MYSQL_SSL_CA}" ;;
  VERIFY_IDENTITY)  SSL_ARGS="--ssl-mode=VERIFY_IDENTITY ${MYSQL_SSL_CA:+--ssl-ca=$MYSQL_SSL_CA}" ;;
  *) echo "[users] Unknown MYSQL_SSL_MODE=$MYSQL_SSL_MODE; defaulting to DISABLED"; SSL_ARGS="--ssl-mode=DISABLED" ;;
esac
echo "[users] Using SSL args: $SSL_ARGS"

echo "[users] Network check:"
(getent hosts "$DB_HOST" || true) | awk '{print $1,$2}'

echo "$(date +'%F %T') | [users] Waiting for MySQL at $DB_HOST user=$DB_USER db=$DB_NAME"

attempt=0
while (( attempt < MAX_TRIES )); do
  if mysqladmin ping $SSL_ARGS --protocol=TCP -h "$DB_HOST" -u "$DB_USER" --silent 2>/dev/null; then
    echo "[users] MySQL ready after $((attempt+1)) attempt(s) (as $DB_USER)"
    break
  fi
  ((attempt++))
  if (( attempt % 5 == 0 )); then
    echo "[users] Attempt $attempt/$MAX_TRIES still failing – diagnostics:"
    echo "  Port 3306 reachable: $((echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1 && echo YES || echo NO)"
    echo "  mysqladmin (user=$DB_USER):"
    mysqladmin ping $SSL_ARGS --protocol=TCP -h "$DB_HOST" -u "$DB_USER" 2>&1 || true
    echo "  root fallback:"
    MYSQL_PWD="$ROOT_PW" mysqladmin ping $SSL_ARGS --protocol=TCP -h "$DB_HOST" -u root 2>&1 || true
  fi
  if (( attempt == MAX_TRIES )); then
    echo "[users] FATAL: Could not reach MySQL"
    exit 1
  fi
  sleep 2
done

echo "[users] Verifying simple query..."
mysql $SSL_ARGS -h "$DB_HOST" -u "$DB_USER" -e "SELECT 1;" || {
  echo "[users] ERROR: Connectivity test failed"
  exit 1
}

echo "[users] Ensuring database $DB_NAME exists"
MYSQL_PWD="$ROOT_PW" mysql $SSL_ARGS -h "$DB_HOST" -u root -e \
  "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`; GRANT ALL ON \`$DB_NAME\`.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD'; FLUSH PRIVILEGES;" || \
  echo "[users] DB init step skipped"

if [[ "$RUN_MIGRATIONS" == "true" ]]; then
  echo "[users] Running migrations"
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput || true
else
  echo "[users] Skipping migrations (RUN_MIGRATIONS=$RUN_MIGRATIONS)"
fi

echo "[users] Starting application"
exec "$@"
// ...existing code...
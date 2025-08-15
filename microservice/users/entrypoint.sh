#!/usr/bin/env bash
set -e
echo "$(date +'%F %T') | [users] entrypoint version 2025-08-12-02"

DB_HOST="${DB_HOST:-mysql_users}"
DB_USER="${DB_USER:-crm_user}"
DB_PASSWORD="${DB_PASSWORD:-crm_password}"
DB_NAME="${DB_NAME:-users_db}"
ROOT_PW="${ROOT_PASSWORD:-crm_password}"
MAX_TRIES=60

echo "[users] Network check:"
getent hosts "$DB_HOST" || echo "[users] DNS lookup FAILED for $DB_HOST"

echo "$(date +'%F %T') | [users] Waiting for MySQL at $DB_HOST user=$DB_USER db=$DB_NAME"
for i in $(seq 1 $MAX_TRIES); do
  if mysqladmin ping --protocol=TCP -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
    echo "[users] MySQL ready after $i attempt(s) (as $DB_USER)"
    break
  fi

  # Every 5 attempts show detailed diagnostics
  if (( i % 5 == 0 )); then
    echo "[users] Attempt $i/$MAX_TRIES still failing – detailed diagnostics:"
    echo "  DNS: $(getent hosts "$DB_HOST" | awk '{print $1}' | xargs echo || echo 'N/A')"
    echo "  Port 3306 reachable: $((echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1 && echo YES || echo NO)"
    echo "  mysqladmin (user=$DB_USER) output:"
    mysqladmin ping --protocol=TCP -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" 2>&1 || true
    echo "  Trying root fallback:"
    mysqladmin ping --protocol=TCP -h "$DB_HOST" -u root -p"$ROOT_PW" 2>&1 || true
  fi

  if (( i == MAX_TRIES )); then
    echo "[users] FATAL: Could not reach MySQL with provided credentials"
    exit 1
  fi
  sleep 2
done

# Secondary verification (will show error if auth problem)
echo "[users] Verifying simple query..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" || {
  echo "[users] ERROR: Simple query failed"
  exit 1
}

echo "[users] Ensuring database $DB_NAME exists"
mysql -h "$DB_HOST" -u root -p"$ROOT_PW" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`; GRANT ALL ON \`$DB_NAME\`.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD'; FLUSH PRIVILEGES;" || echo "[users] DB init step skipped"

echo "[users] Running migrations"
python manage.py makemigrations
python manage.py migrate
# ...existing code...
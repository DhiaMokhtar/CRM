#!/usr/bin/env bash
set -e
DB_HOST="${DB_HOST:-mysql_courses}"
DB_USER="${DB_USER:-crm_user}"
DB_PASSWORD="${DB_PASSWORD:-crm_password}"
MAX_TRIES=60

echo "$(date +'%F %T') | [courses] Waiting for MySQL at $DB_HOST user=$DB_USER"
echo "$(date +'%F %T') | [courses] DNS: $(getent hosts "$DB_HOST" || echo 'NOT FOUND')"

for i in $(seq 1 $MAX_TRIES); do
  if mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
    echo "$(date +'%F %T') | [courses] MySQL ready after $i attempt(s)"
    break
  fi
  if (( i % 5 == 0 )); then
    echo "$(date +'%F %T') | [courses] Debug attempt $i: trying simple TCP check"
    (echo > /dev/tcp/"$DB_HOST"/3306) >/dev/null 2>&1 && echo "$(date +'%F %T') | [courses] Port 3306 open"
  fi
  sleep 2
done

if ! mysqladmin ping -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; then
  echo "$(date +'%F %T') | [courses] ERROR: DB not reachable with provided credentials"
  echo "$(date +'%F %T') | [courses] Trying root as fallback"
  if mysqladmin ping -h "$DB_HOST" -u root -p"${DB_PASSWORD}" --silent 2>/dev/null; then
    echo "[courses] Root works -> credential mismatch for $DB_USER"
  fi
  exit 1
fi

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
exec python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
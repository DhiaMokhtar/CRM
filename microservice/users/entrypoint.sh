#!/usr/bin/env bash
set -e
echo "$(date +'%F %T') | [users] entrypoint version 2025-08-12-02"

DB_HOST="${DB_HOST:-mysql_users}"
DB_USER="${DB_USER:-crm_user}"
DB_PASSWORD="${DB_PASSWORD:-crm_password}"
DB_NAME="${DB_NAME:-users_db}"
ROOT_PW="${ROOT_PASSWORD:-crm_password}"
MAX_TRIES=60


echo "[users] Ensuring database $DB_NAME exists"
mysql -h "$DB_HOST" -u root -p"$ROOT_PW" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`; GRANT ALL ON \`$DB_NAME\`.* TO '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD'; FLUSH PRIVILEGES;" || echo "[users] DB init step skipped"

echo "[users] Running migrations"
python manage.py makemigrations
python manage.py migrate

echo "[users] Creating default admin user"
python manage.py shell -c "
from users.models import Administrator
if not Administrator.objects.filter(username='root').exists():
    Administrator.objects.create(username='root', password='root', email='root@admin.com')
    print('Created admin user: root/root')
else:
    print('Admin user root already exists')
"

echo "[users] Creating default classroom"
python manage.py shell -c "
from users.models import ClassRoom
if not ClassRoom.objects.filter(name='physics class').exists():
    ClassRoom.objects.create(name='physics class')
    print('Created default classroom: physics class')
else:
    print('Classroom physics class already exists')
"

echo "[users] Collect static (if any)"
python manage.py collectstatic --noinput || true

echo "[users] SSL setup"
mkdir -p /app/ssl
rm -f /app/ssl/localhost.pem /app/ssl/localhost-key.pem
if [[ -f /certs-in/localhost.pem && -f /certs-in/localhost-key.pem ]]; then
  install -m 600 /certs-in/localhost.pem /app/ssl/localhost.pem
  install -m 600 /certs-in/localhost-key.pem /app/ssl/localhost-key.pem
else
  echo "[users] Generating self-signed cert"
  openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /app/ssl/localhost-key.pem \
    -out /app/ssl/localhost.pem \
    -subj "/CN=localhost"
fi

echo "[users] Starting HTTPS server"
exec python manage.py runsslserver 0.0.0.0:8000 --certificate /app/ssl/localhost.pem --key /app/ssl/localhost-key.pem
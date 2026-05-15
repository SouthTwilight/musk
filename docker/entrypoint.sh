#!/bin/bash
set -e

echo "=== Musk Platform Startup ==="

cd /app/backend

# 运行数据库迁移
echo "[1/3] Running migrations..."
python manage.py migrate --noinput

# 为已注册的模块运行迁移
echo "[2/3] Running module migrations..."
python -c "
import django
django.setup()
from module_layer.registry import registry
from django.core.management import call_command
for info in registry.all():
    try:
        call_command('migrate', info.app_label, database=info.db_alias, verbosity=0)
        echo_ok = print(f'  Migrated module: {info.name}')
    except Exception as e:
        print(f'  Warning: module {info.name} migration failed: {e}')
"

# 收集静态文件
echo "[3/3] Collecting static files..."
python manage.py collectstatic --noinput --verbosity 0 2>/dev/null || true

echo "=== Starting services ==="

# 启动 Gunicorn（后台）和 Nginx（前台）
gunicorn musk.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --daemon

exec nginx -g 'daemon off;'

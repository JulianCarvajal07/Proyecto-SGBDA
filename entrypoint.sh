#!/bin/sh

set -e

echo "Aplicando migraciones..."
python manage.py migrate

echo "Recolectando estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."

exec gunicorn PROYECTO_SGBDA.wsgi:application \
    --bind 0.0.0.0:8000 \
    --timeout 600 \
    --workers 2 \
    --threads 4
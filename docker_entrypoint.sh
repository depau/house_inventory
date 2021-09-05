#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Collecting static files"
[ -d /data/static ] && rm -Rf /data/static
python manage.py collectstatic

echo "Performing migrations"
python manage.py migrate

echo "Starting gunicorn"
exec gunicorn "${@}"

#!/bin/sh
python manage.py migrate;
python manage.py collectstatic --noinput;
python manage.py loaddata dump.json;
cp -r /app/backend_static/. /backend_static/static/;
gunicorn -b 0:9000 foodgram.wsgi

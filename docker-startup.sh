#!/bin/bash

if [ ! -d "./db" ]; then
    mkdir -p ./db/flask_session
    flask db init --directory ./db/migrations

elif [ ! -d "./db/migrations" ]; then
    flask db init --directory ./db/migrations
    if [ ! -d "./db/flask_session" ]; then
        mkdir -p ./db/flask_session
    fi
fi

flask db migrate --directory ./db/migrations -m "auto-migration"
flask db upgrade --directory ./db/migrations

exec gunicorn -b :3110 --access-logfile - --error-logfile - sage:flaskApp
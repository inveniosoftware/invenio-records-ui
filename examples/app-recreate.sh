#!/bin/sh

pip install -r requirements.txt
[ -e "app.db" ] && rm app.db
export FLASK_APP=app.py
flask db init
flask db create
flask fixtures records
flask run --debugger -h 0.0.0.0 -p 5000

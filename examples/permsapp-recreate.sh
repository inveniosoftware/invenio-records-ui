#!/bin/sh

pip install -r requirements.txt
[ -e "permsapp.db" ] && rm permsapp.db
export FLASK_APP=permsapp.py
flask db init
flask db create
flask fixtures records
flask run --debugger -h 0.0.0.0 -p 5000

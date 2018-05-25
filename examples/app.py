# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Minimal Flask application example for development.

SPHINX-START

Run the Redis server.

Run example development server:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ export FLASK_APP=app.py
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Run example development server:

.. code-block:: console

    $ flask run --debugger -p 5000

View some records in your browser::

   http://localhost:5000/records/1
   http://localhost:5000/records/2
   http://localhost:5000/records/3
   http://localhost:5000/records/4
   http://localhost:5000/records/5
   http://localhost:5000/records/6
   http://localhost:5000/records/7
   http://localhost:5000/records/8

To be able to uninstall the example app:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB, db
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords

from invenio_records_ui import InvenioRecordsUI
from invenio_records_ui.views import create_blueprint_from_app

# create application's instance directory. Needed for this example only.
current_dir = os.path.dirname(os.path.realpath(__file__))
instance_dir = os.path.join(current_dir, 'app')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# Create Flask application
app = Flask(__name__, instance_path=instance_dir)
app.config.update(dict(
    CELERY_ALWAYS_EAGER=True,
    CELERY_RESULT_BACKEND='cache',
    CELERY_CACHE_BACKEND='memory',
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                           'sqlite:///app.db'),
    # Disable access control
    RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None
))

FlaskCeleryExt(app)
Babel(app)
InvenioDB(app)
InvenioPIDStore(app)
InvenioRecords(app)
InvenioRecordsUI(app)
app.register_blueprint(create_blueprint_from_app(app))


rec1_uuid = 'deadbeef-1234-5678-ba11-b100dc0ffee5'
"""First record's UUID. It will be given PID 1."""

rec2_uuid = 'deadbeef-1234-5678-ba11-b100dc0ffee6'
"""First record's UUID. It will be given PID 2."""


@app.cli.group()
def fixtures():
    """Command for working with test data."""


@fixtures.command()
def records():
    """Load test data fixture."""
    import uuid
    from invenio_records.api import Record
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus

    # Record 1 - Live record
    with db.session.begin_nested():
        pid1 = PersistentIdentifier.create(
            'recid', '1', object_type='rec', object_uuid=rec1_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({
            'title': 'Registered ',
            'authors': [
                {'name': 'Ellis Jonathan'},
                {'name': 'Higgs Peter'},
            ],
            'access': 'open',
            'keywords': ['CERN', 'higgs'],
        }, id_=rec1_uuid)

        PersistentIdentifier.create(
            'recid', '2', object_type='rec', object_uuid=rec2_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({
            'title': 'Registered ',
            'authors': [
                {'name': 'Ellis Jonathan'},
                {'name': 'Higgs Peter'},
            ],
            'access': 'closed',
            'keywords': ['CERN', 'higgs'],
        }, id_=rec2_uuid)

        # Record 3 - Deleted PID with record
        rec3_uuid = uuid.uuid4()
        pid = PersistentIdentifier.create(
            'recid', '3', object_type='rec', object_uuid=rec3_uuid,
            status=PIDStatus.REGISTERED)
        pid.delete()
        Record.create({'title': 'Live '}, id_=rec3_uuid)

        # Record 4 - Deleted PID without a record
        PersistentIdentifier.create(
            'recid', '4', status=PIDStatus.DELETED)

        # Record 5 - Registered PID without a record
        PersistentIdentifier.create(
            'recid', '5', status=PIDStatus.REGISTERED)

        # Record 6 - Redirected PID
        pid = PersistentIdentifier.create(
            'recid', '6', status=PIDStatus.REGISTERED)
        pid.redirect(pid1)

        # Record 7 - Redirected non existing endpoint
        doi = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.REGISTERED)
        pid = PersistentIdentifier.create(
            'recid', '7', status=PIDStatus.REGISTERED)
        pid.redirect(doi)

        # Record 8 - Unregistered PID
        PersistentIdentifier.create(
            'recid', '8', status=PIDStatus.RESERVED)

    db.session.commit()

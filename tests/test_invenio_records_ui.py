# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask, request
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record, before_record_insert

from invenio_records_ui import InvenioRecordsUI
from invenio_records_ui.signals import record_viewed


def setup_record_fixture(app):
    """Setup a record fixture."""
    records = []

    def _create_pid(record):
        pid = PersistentIdentifier.create(
            'recid', record['recid'], pid_provider='recid')
        pid.assign('rec', record['recid'])
        pid.register()

    with before_record_insert.connected_to(_create_pid):
        with app.app_context():
            records.append(Record.create(
                {'title': 'Test record 1', 'recid': 1},
                identifier_key='recid'
            ))
            records.append(Record.create(
                {'title': 'Test record 2', 'recid': 2},
                identifier_key='recid'
            ))
            pid = PersistentIdentifier.create('recid', 3, pid_provider='recid')
            db.session.add(pid)
            db.session.commit()

            pid = PersistentIdentifier.get('recid', 2, pid_provider='recid')
            pid.delete()
            db.session.commit()

    return records


def test_version():
    """Test version import."""
    from invenio_records_ui import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioRecordsUI(app)
    assert 'invenio-records-ui' in app.extensions

    app = Flask('testapp')
    ext = InvenioRecordsUI()
    assert 'invenio-records-ui' not in app.extensions
    ext.init_app(app)
    assert 'invenio-records-ui' in app.extensions


def test_view(app):
    """Test view."""
    InvenioRecordsUI(app)
    setup_record_fixture(app)

    with app.test_client() as client:
        res = client.get("/records/1")
        assert res.status_code == 200

        # Deleted PID
        res = client.get("/records/2")
        assert res.status_code == 410

        # Missing object
        res = client.get("/records/3")
        assert res.status_code == 404

        # No pid, no record
        res = client.get("/records/4")
        assert res.status_code == 404


def test_signal(app):
    """Test view."""
    InvenioRecordsUI(app)
    setup_record_fixture(app)

    called = {'record-viewed': False}

    def _signal_sent(app, record=None, pid=None):
        assert request.path
        assert record
        assert pid
        called['record-viewed'] = record['recid']

    with app.test_client() as client:
        with record_viewed.connected_to(_signal_sent):
            res = client.get("/records/1")
            assert res.status_code == 200
            assert called['record-viewed'] == 1


def test_changed_views(app):
    """Test view."""
    app.config.update(dict(
        PIDSTORE_DATACITE_DOI_PREFIX="10.4321",
        RECORDS_UI_ENDPOINTS=dict(
            records=dict(
                pid_type='recid',
                pid_provider='recid',
                route='/records/<pid_value>',
            ),
            references=dict(
                pid_type='recid',
                pid_provider='recid',
                route='/records/<pid_value>/references',
            ),
            dois=dict(
                pid_type='doi',
                pid_provider='doi',
                route='/doi/<path:pid_value>',
            )
        )
    ))
    InvenioRecordsUI(app)
    setup_record_fixture(app)

    with app.app_context():
        pid = PersistentIdentifier.create(
            'doi', '10.1234/foo.bar', pid_provider='doi')
        pid.assign('rec', '1')
        pid.register()
        db.session.commit()

    with app.test_client() as client:
        res = client.get("/records/1")
        assert res.status_code == 200

        res = client.get("/records/1/references")
        assert res.status_code == 200

        res = client.get("/doi/10.1234/foo.bar")
        assert res.status_code == 200

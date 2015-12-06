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

import uuid

from flask import Flask, request, url_for
from flask_menu import Menu
from flask_security.utils import encrypt_password
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_records.permissions import records_read_all

from invenio_records_ui import InvenioRecordsUI
from invenio_records_ui.signals import record_viewed


def setup_record_fixture(app):
    """Setup a record fixture."""
    with app.app_context():
        # Record 1 - Live record
        rec_uuid = uuid.uuid4()
        pid1 = PersistentIdentifier.create(
            'recid', '1', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        Record.create({'title': 'Registered', 'recid': 1}, id_=rec_uuid)

        # Record 2 - Deleted PID with record
        rec_uuid = uuid.uuid4()
        pid = PersistentIdentifier.create(
            'recid', '2', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        pid.delete()
        Record.create({'title': 'Live '}, id_=rec_uuid)

        # Record 3 - Deleted PID without a record
        PersistentIdentifier.create(
            'recid', '3', status=PIDStatus.DELETED)

        # Record 4 - Registered PID without a record
        PersistentIdentifier.create(
            'recid', '4', status=PIDStatus.REGISTERED)

        # Record 5 - Redirected PID
        pid = PersistentIdentifier.create(
            'recid', '5', status=PIDStatus.REGISTERED)
        pid.redirect(pid1)

        # Record 6 - Redirected non existing endpoint
        rec_uuid = uuid.uuid4()
        Record.create({'title': 'DOI', }, id_=rec_uuid)
        doi = PersistentIdentifier.create(
            'doi', '10.1234/foo', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=rec_uuid)
        pid = PersistentIdentifier.create(
            'recid', '6', status=PIDStatus.REGISTERED)
        pid.redirect(doi)

        # Record 7 - Unregistered PID
        PersistentIdentifier.create(
            'recid', '7', status=PIDStatus.RESERVED)
        db.session.commit()


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

        res = client.get("/records/3")
        assert res.status_code == 410

        # Missing object
        res = client.get("/records/4")
        assert res.status_code == 500

        # Redirected PID
        res = client.get("/records/5")
        assert res.status_code == 302

        # Non existing endpoint
        res = client.get("/records/6")
        assert res.status_code == 500

        # Unregistered PID
        res = client.get("/records/7")
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
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
            ),
            references=dict(
                pid_type='recid',
                route='/records/<pid_value>/references',
            ),
            doi=dict(
                pid_type='doi',
                route='/doi/<path:pid_value>',
            )
        )
    ))
    InvenioRecordsUI(app)
    setup_record_fixture(app)

    with app.test_client() as client:
        res = client.get("/records/1")
        assert res.status_code == 200

        res = client.get("/records/1/references")
        assert res.status_code == 200

        res = client.get("/doi/10.1234/foo")
        assert res.status_code == 200


def test_permission(app):
    """Test permission control to records."""
    app.config.update(
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='CHANGEME',
        SECURITY_PASSWORD_SALT='CHANGEME',
        # conftest switches off permission checking, so re-enable it for this
        # app.
        RECORDS_UI_DEFAULT_PERMISSION_FACTORY='invenio_records.permissions'
                                              ':read_permission_factory'
    )
    Menu(app)
    InvenioRecordsUI(app)
    accounts = InvenioAccounts(app)
    app.register_blueprint(accounts_blueprint)
    InvenioAccess(app)
    setup_record_fixture(app)

    # Create admin
    with app.app_context():
        admin = accounts.datastore.create_user(
            email='admin@invenio-software.org',
            password=encrypt_password('123456'),
            active=True,
        )
        reader = accounts.datastore.create_user(
            email='reader@invenio-software.org',
            password=encrypt_password('123456'),
            active=True,
        )

        # Get record 1
        r = Resolver(pid_type='recid', object_type='rec',
                     getter=Record.get_record)
        dummy_pid, record = r.resolve('1')

        # Setup permissions for record 1 (grant 'admin', deny 'reader')
        db.session.add(ActionUsers(
            action=records_read_all.value, argument=str(record.id),
            user=admin))
        db.session.add(ActionUsers(
            action=records_read_all.value, argument=str(record.id),
            user=reader, exclude=True))
        db.session.commit()

    with app.test_request_context():
        login_url = url_for('security.login')
        record_url = url_for('invenio_records_ui.recid', pid_value='1')

    # Access record 1 as admin
    with app.test_client() as client:
        res = client.get(record_url)
        assert res.status_code == 302
        res = client.post(login_url, data={
            'email': 'admin@invenio-software.org', 'password': '123456'})
        assert res.status_code == 302
        res = client.get(record_url)
        res.status_code == 200

    # Access record 1 as reader
    with app.test_client() as client:
        res = client.post(login_url, data={
            'email': 'reader@invenio-software.org', 'password': '123456'})
        assert res.status_code == 302
        res = client.get(record_url)
        res.status_code == 403

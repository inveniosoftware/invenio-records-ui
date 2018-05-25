# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import uuid

from flask import Flask, request, url_for
from flask_menu import Menu
from flask_security.utils import encrypt_password
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record

from invenio_records_ui import InvenioRecordsUI
from invenio_records_ui.signals import record_viewed
from invenio_records_ui.views import create_blueprint_from_app


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
    app.register_blueprint(create_blueprint_from_app(app))
    assert 'invenio-records-ui' in app.extensions

    app = Flask('testapp')
    ext = InvenioRecordsUI()
    assert 'invenio-records-ui' not in app.extensions
    ext.init_app(app)
    app.register_blueprint(create_blueprint_from_app(app))
    assert 'invenio-records-ui' in app.extensions


def test_view(app):
    """Test view."""
    InvenioRecordsUI(app)
    app.register_blueprint(create_blueprint_from_app(app))
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
    app.register_blueprint(create_blueprint_from_app(app))
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
    app.register_blueprint(create_blueprint_from_app(app))
    setup_record_fixture(app)

    with app.test_client() as client:
        res = client.get("/records/1")
        assert res.status_code == 200

        res = client.get("/records/1/references")
        assert res.status_code == 200

        res = client.get("/doi/10.1234/foo")
        assert res.status_code == 200


def custom_view(pid, record, template=None, **kwargs):
    """Custom view function for testing."""
    return 'TEST:{0}:{1}'.format(pid.pid_value, kwargs.get('filename'))


def custom_get_and_post(pid, record, template=None):
    """Custom view function for testing GET/POST."""
    return 'TEST:{0}:{1}'.format(pid.pid_value, request.method)


def test_custom_view_method(app):
    """Test view."""
    app.config.update(dict(
        PIDSTORE_DATACITE_DOI_PREFIX='10.4321',
        RECORDS_UI_ENDPOINTS=dict(
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
            ),
            record_with_param=dict(
                pid_type='recid',
                route='/records/<pid_value>/export/<format>',
            ),
            recid_custom=dict(
                pid_type='recid',
                route='/records/<pid_value>/custom/<filename>',
                view_imp='test_invenio_records_ui:custom_view',
            ),
            recid_get_post=dict(
                pid_type='recid',
                route='/records/<pid_value>/custom_get_and_post',
                view_imp='test_invenio_records_ui:custom_get_and_post',
                methods=['GET', 'POST'],
            ),
        )
    ))
    InvenioRecordsUI(app)
    app.register_blueprint(create_blueprint_from_app(app))
    setup_record_fixture(app)

    with app.test_client() as client:
        res = client.get('/records/1')
        assert res.status_code == 200

        # Test that filename parameter is passed to custom view function
        res = client.get('/records/1/custom/afilename')
        assert res.status_code == 200
        assert res.get_data(as_text=True) == 'TEST:1:afilename'

        # Test that default view function can deal with multiple parameters.
        res = client.get('/records/1/export/bibtex')
        assert res.status_code == 200

        # Test GET/POST
        res = client.get('/records/1/custom_get_and_post')
        assert res.status_code == 200
        assert res.get_data(as_text=True) == 'TEST:1:GET'
        res = client.post('/records/1/custom_get_and_post')
        assert res.status_code == 200
        assert res.get_data(as_text=True) == 'TEST:1:POST'


def test_permission(app):
    """Test permission control to records."""
    app.config.update(
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='CHANGEME',
        SECURITY_PASSWORD_SALT='CHANGEME',
        # conftest switches off permission checking, so re-enable it for this
        # app.
        RECORDS_UI_DEFAULT_PERMISSION_FACTORY='helpers:'
                                              'only_authenticated_users',
    )
    Menu(app)
    InvenioRecordsUI(app)
    app.register_blueprint(create_blueprint_from_app(app))
    accounts = InvenioAccounts(app)
    app.register_blueprint(accounts_blueprint)
    InvenioAccess(app)
    setup_record_fixture(app)

    # Create admin
    with app.app_context():
        accounts.datastore.create_user(
            email='admin@inveniosoftware.org',
            password=encrypt_password('123456'),
            active=True,
        )

        # Get record 1
        r = Resolver(pid_type='recid', object_type='rec',
                     getter=Record.get_record)
        dummy_pid, record = r.resolve('1')

        db.session.commit()

    with app.test_request_context():
        login_url = url_for('security.login')
        record_url = url_for('invenio_records_ui.recid', pid_value='1')

    # Access record 1 as admin
    with app.test_client() as client:
        res = client.get(record_url)
        assert res.status_code == 302
        res = client.post(login_url, data={
            'email': 'admin@inveniosoftware.org', 'password': '123456'})
        assert res.status_code == 302
        res = client.get(record_url)
        res.status_code == 200

    # Access record 1 as anonymous
    with app.test_client() as client:
        res = client.get(record_url)
        res.status_code == 403


def test_record_export(app, json_v1):
    """Test record export formats."""
    app.config.update(dict(
        RECORDS_UI_EXPORT_FORMATS=dict(
            recid=dict(
                json=dict(
                    title='JSON',
                    serializer=json_v1,
                    order=1,
                )
            )
        )
    ))

    InvenioRecordsUI(app)
    app.register_blueprint(create_blueprint_from_app(app))
    setup_record_fixture(app)

    with app.test_client() as client:
        res = client.get('/records/1/export/json')
        assert res.status_code == 200
        res = client.get('/records/1/export/None')
        assert res.status_code == 404


def test_default_export_format(app, json_v1):
    """Test default configuration for record export format"""
    from invenio_records_ui.ext import _RecordUIState

    app.config.update(dict(
        RECORDS_UI_EXPORT_FORMATS=dict(
            recid=dict(
                json=dict(
                    title='JSON',
                    serializer='fictitious_json_serializer',
                    order=1,
                )
            )
        )
    ))

    record_ui_state = _RecordUIState(app)
    default_format = [('json', {'title': 'JSON',
                                'serializer': 'fictitious_json_serializer',
                                'order': 1})]
    assert default_format == record_ui_state.export_formats('recid')

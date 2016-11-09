# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Records-UI custom view func tests."""

from __future__ import absolute_import, print_function

import shutil
import tempfile
import uuid

import pytest
from flask import url_for
from invenio_db import db
from invenio_files_rest.models import Bucket, Location, MultipartObject, \
    ObjectVersion, Part
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import InvenioRecords
from invenio_records_files.api import Record, RecordsBuckets
from six import BytesIO

from invenio_records_ui import InvenioRecordsUI


@pytest.yield_fixture()
def app_ctx(app):
    """Yield application context."""
    with app.app_context():
        yield app


@pytest.yield_fixture()
def dummy_location(app_ctx):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(
        name='testloc',
        uri=tmppath,
        default=True
    )
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def bucket(app_ctx, dummy_location):
    """File system location."""
    b1 = Bucket.create()
    db.session.commit()
    return b1


@pytest.yield_fixture()
def objects(app_ctx, bucket):
    """File system location."""
    # Create older versions first
    for key, content in [
            ('LICENSE', b'old license'),
            ('README.rst', b'old readme')]:
        ObjectVersion.create(
            bucket, key, stream=BytesIO(content), size=len(content)
        )

    # Create new versions
    objs = []
    for key, content in [
            ('LICENSE', b'license file'),
            ('README.rst', b'readme file')]:
        objs.append(
            ObjectVersion.create(
                bucket, key, stream=BytesIO(content), size=len(content)
            )
        )
    db.session.commit()

    yield objs


def test_file_download_ui(app, objects):
    """Test get buckets."""
    app.config.update(dict(
        FILES_REST_PERMISSION_FACTORY=lambda *a, **kw: type(
            'Allow', (object, ), {'can': lambda self: True}
        )(),
        RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None,  # No permission checking
        RECORDS_UI_ENDPOINTS=dict(
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
            ),
            recid_files=dict(
                pid_type='recid',
                route='/records/<pid_value>/files/<filename>',
                view_imp='invenio_records_files.utils:file_download_ui',
                record_class='invenio_records_files.api:Record',
            ),
        )
    ))
    InvenioRecordsUI(app)

    obj1 = objects[0]

    with app.test_request_context():
        # Record 1 - Live record
        rec_uuid = uuid.uuid4()
        PersistentIdentifier.create(
            'recid', '1', object_type='rec', object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED)
        record = Record.create({
            'title': 'Registered',
            'recid': 1,
            '_files': [
                {'key': obj1.key, 'bucket': str(obj1.bucket_id),
                 'checksum': 'invalid'},
            ]
        }, id_=rec_uuid)
        RecordsBuckets.create(record=record.model, bucket=obj1.bucket)
        db.session.commit()

        main_url = url_for('invenio_records_ui.recid', pid_value='1')
        file_url = url_for(
            'invenio_records_ui.recid_files', pid_value='1', filename=obj1.key)
        no_file_url = url_for(
            'invenio_records_ui.recid_files', pid_value='1', filename='')
        invalid_file_url = url_for(
            'invenio_records_ui.recid_files', pid_value='1', filename='no')

    with app.test_client() as client:
        res = client.get(main_url)
        assert res.status_code == 200
        res = client.get(file_url)
        assert res.status_code == 200
        res = client.get(no_file_url)
        assert res.status_code == 404
        res = client.get(invalid_file_url)
        assert res.status_code == 404

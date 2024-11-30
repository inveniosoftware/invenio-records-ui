# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import json
import os

import pytest
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB, db
from invenio_i18n import Babel
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords


class DefaultJSONSerializer(object):
    """Simple JSON serializer for testing."""

    def serialize(self, pid, record):
        """Serialize object to JSON.

        :param pid: Persistent Identifier.
        :param record: The :class:`invenio_records.api.Record` instance.
        """
        return json.dumps(record, sort_keys=True, indent=2, separators=(",", ": "))


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    app = Flask("testapp")
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite://"),
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND="cache",
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None,  # No permission checking
        APP_THEME=["semantic-ui"],
        THEME_ICONS={
            "semantic-ui": {
                "key": "key icon",
                "link": "linkify icon",
                "shield": "shield alternate icon",
                "user": "user icon",
                "codepen": "codepen icon",
                "cogs": "cogs icon",
                # Special catch all:
                "*": "{} icon",
            }
        },
    )
    FlaskCeleryExt(app)
    Babel(app)
    InvenioDB(app)
    InvenioPIDStore(app)
    InvenioRecords(app)

    with app.app_context():
        db.create_all()

    def finalize():
        with app.app_context():
            db.drop_all()

    request.addfinalizer(finalize)
    return app


@pytest.fixture()
def json_v1():
    """JSON serializer fixture."""
    return DefaultJSONSerializer()

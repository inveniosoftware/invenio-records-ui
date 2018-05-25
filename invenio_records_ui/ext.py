# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask extension for Invenio-Records-UI."""

from __future__ import absolute_import, print_function

from . import config
from .utils import obj_or_import_string


class _RecordUIState(object):
    """Record UI state."""

    def __init__(self, app):
        """Initialize state.

        :param app: The Flask application.
        """
        self.app = app
        self._permission_factory = None
        self._export_formats = {}

    def export_formats(self, pid_type):
        """List of export formats."""
        if pid_type not in self._export_formats:
            fmts = self.app.config.get('RECORDS_UI_EXPORT_FORMATS', {}).get(
                pid_type, {})
            self._export_formats[pid_type] = sorted(
                [(k, v) for k, v in fmts.items() if v],
                key=lambda x: x[1]['order'],
            )
        return self._export_formats[pid_type]

    @property
    def permission_factory(self):
        """Load default permission factory."""
        if self._permission_factory is None:
            imp = self.app.config['RECORDS_UI_DEFAULT_PERMISSION_FACTORY']
            self._permission_factory = obj_or_import_string(imp)
        return self._permission_factory


class InvenioRecordsUI(object):
    """Invenio-Records-UI extension.

    The extension takes care of setting default configuration and registering
    a blueprint with URL routes for the endpoints.
    """

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        :param app: The Flask application.
        """
        self.init_config(app)
        app.extensions['invenio-records-ui'] = _RecordUIState(app)

    def init_config(self, app):
        """Initialize configuration on application.

        :param app: The Flask application.
        """
        app.config.setdefault(
            'RECORDS_UI_BASE_TEMPLATE',
            app.config.get('BASE_TEMPLATE', 'invenio_records_ui/base.html')
        )

        for k in dir(config):
            if k.startswith('RECORDS_UI_'):
                app.config.setdefault(k, getattr(config, k))

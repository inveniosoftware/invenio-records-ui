# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Flask extension for Invenio-Records-UI."""

from __future__ import absolute_import, print_function

from . import config
from .utils import obj_or_import_string
from .views import create_blueprint


class _RecordUIState(object):
    """Record UI state."""

    def __init__(self, app):
        """Initialize state.

        :param app: The Flask application.
        """
        self.app = app
        self._permission_factory = None

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

        # Register records blueprints
        app.register_blueprint(
            create_blueprint(app.config['RECORDS_UI_ENDPOINTS']))

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

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

"""Flask extension for Invenio-Records-UI."""

from __future__ import absolute_import, print_function

RECORDS_UI_TOMBSTONE_TEMPLATE = "invenio_records_ui/tombstone.html"
"""Configure the tombstone template."""

RECORDS_UI_DEFAULT_PERMISSION_FACTORY = None
"""Configure the default permission factory."""

RECORDS_UI_LOGIN_ENDPOINT = "security.login"
"""Endpoint where redirect the user if login is required."""

RECORDS_UI_ENDPOINTS = {
    "recid": {
        "pid_type": "recid",
        "route": "/records/<pid_value>",
        "template": "invenio_records_ui/detail.html",
    }
}
"""Default UI endpoints loaded.

This option can be overwritten to describe the endpoints of the different
record types.

Each element on the dictionary represent a independent endpoint.

The structure of the dictionary is as follows:

.. code-block:: python

    def my_view(pid, record, template=None):
        return render_template(template, pid=pid, record=record)


    def my_permission_factory(record, *args, **kwargs):
        def can(self):
            rec = Record.get_record(record.id)
            return rec.get('access', '') == 'open'
        return type('MyPermissionChecker', (), {'can': can})()


    RECORDS_UI_ENDPOINTS = {
        "<endpoint-name>": {
            "pid_type": "<record-pid-type>",
            "route": "/records/<pid_value>",
            "template": "invenio_records_ui/detail.html",
            "permission_factory_imp": "my_permission_factory",
            "view_imp": my_view,
            "record_class": "invenio_records.api:Record",
            "methods": ["GET", "POST", "PUT", "DELETE"],
        },
        ...
    }

:param pid_type: Persistent identifier type for endpoint. Required.

:param route: URL route (must include ``<pid_value>`` pattern). Required.

:param template: Template to render.
    (Default: ``invenio_records_ui/detail.html``)

:param permission_factory_imp: Import path to factory that creates a
        permission object for a given record. If the value is ``None``, then
        no access control is done. (Default: ``None``)

:param view_imp: Import path to view function. (Default: ``None``)

:param record_class: Import path of record class.
    (Default: ``invenio_records.api:Record``)

:param methods: List of methods supported. (Default: ``['GET']``)
"""

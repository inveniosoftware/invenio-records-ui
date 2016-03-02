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


"""Views module tests."""

from __future__ import absolute_import, print_function

from datetime import datetime

from flask import render_template_string

from invenio_records_ui import InvenioRecordsUI


def test_view_macro_file_list(app):
    """Test file list macro."""
    app.config.update(
        RECORDS_UI_ENDPOINTS=dict(
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                template='invenio_records_ui/detail.html',
            ),
        )
    )
    InvenioRecordsUI(app)

    with app.test_request_context():
        files = [
            {
                'uri': 'http://domain/test1.txt',
                'key': 'test1.txt',
                'size': 10,
                'date': datetime(2016, 7, 10).strftime("%d/%m/%y"),
            },
            {
                'uri': 'http://otherdomain/test2.txt',
                'key': 'test2.txt',
                'size': 12,
                'date': datetime(2016, 7, 12).strftime("%d/%m/%y"),
            },
        ]
        result = render_template_string("""
            {%- from "invenio_records_ui/_macros.html" import file_list %}
            {{ file_list(files) }}
            """, files=files)

        assert '<a class="forcewrap" href="http://domain/test1.txt"' in result
        assert '<td class="nowrap">10/07/16</td>' in result
        assert '<td class="nowrap">10</td>' in result
        assert 'href="http://otherdomain/test2.txt"' in result
        assert '<td class="nowrap">12/07/16</td>' in result
        assert '<td class="nowrap">12</td>' in result

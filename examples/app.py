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


"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ cd examples
   $ flask -a app.py db init
   $ flask -a app.py db create
   $ flask -a app.py --debug run
"""

from __future__ import absolute_import, print_function

from flask import Flask
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords

from invenio_records_ui import InvenioRecordsUI

# Create Flask application
app = Flask(__name__)
app.config.update(dict(
    CELERY_ALWAYS_EAGER=True,
    CELERY_RESULT_BACKEND="cache",
    CELERY_CACHE_BACKEND="memory",
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
))
FlaskCeleryExt(app)
FlaskCLI(app)
Babel(app)
InvenioDB(app)
InvenioPIDStore(app)
InvenioRecords(app)
InvenioRecordsUI(app)

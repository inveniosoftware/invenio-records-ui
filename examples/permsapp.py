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


"""Flask application example for development with support for permissions.

Run example development server:

.. code-block:: console

   $ cd examples
   $ flask -a permsapp.py db init
   $ flask -a permsapp.py db create
   $ flask -a permsapp.py fixtures records
   $ flask -a permsapp.py fixtures access
   $ flask -a permsapp.py --debug run

Try to view record 1::

   http://localhost:5000/records/1

Login as admin@invenio-software.org (password 123456) and view record 1 again:

   http://localhost:5000/login
   http://localhost:5000/records/1

Logout and login as reader@invenio-software.org (password 123456) and view
record 1 again:

   http://localhost:5000/logout
   http://localhost:5000/login
   http://localhost:5000/records/1
"""

from __future__ import absolute_import, print_function

from app import app, fixtures, rec1_uuid
from flask_security.utils import encrypt_password
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint
from invenio_db import db
from invenio_records.permissions import records_read_all


# Install Principal and Login extensions
app.config.update(
    ACCOUNTS_USE_CELERY=False,
    SECRET_KEY='CHANGE_ME',
    SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
    # conftest switches off permission checking, so re-enable it for this
    # app.
    RECORDS_UI_DEFAULT_PERMISSION_FACTORY='invenio_records.permissions:read_permission_factory'  # noqa
)


accounts = InvenioAccounts(app)
app.register_blueprint(blueprint)

InvenioAccess(app)


@fixtures.command()
def access():
    """Load access fixtures."""
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

    # Give access to record 1 to user 'admin'
    db.session.add(ActionUsers(
        action=records_read_all.value, argument=rec1_uuid,
        user=admin))
    # Exclude access to record 1 from user 'reader'
    db.session.add(ActionUsers(
        action=records_read_all.value, argument=rec1_uuid,
        user=reader, exclude=True))
    db.session.commit()

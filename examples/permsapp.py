# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Flask application example for development with support for permissions.

SPHINX-START

Run the Redis server.

Run the the example development server:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ export FLASK_APP=permsapp.py
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Run example development server:

.. code-block:: console

    $ flask run --debugger -p 5000

Try to view record 1::

   http://localhost:5000/records/1

Open the record 1:

   http://localhost:5000/records/1

Try now to open the record 2:

   http://localhost:5000/records/2

As you can see, for this user the action is forbidden.

To be able to uninstall the example app:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

from __future__ import absolute_import, print_function

import os

from app import app
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint
from invenio_records.api import Record


def my_permission_factory(record, *args, **kwargs):
    """My permission factory."""
    def can(self):
        rec = Record.get_record(record.id)
        return rec.get('access', '') == 'open'
    return type('MyPermissionChecker', (), {'can': can})()


# Install Principal and Login extensions
app.config.update(
    ACCOUNTS_USE_CELERY=False,
    SECRET_KEY='CHANGE_ME',
    SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
    SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                           'sqlite:///permsapp.db'),
    # conftest switches off permission checking, so re-enable it for this
    # app.
    RECORDS_UI_DEFAULT_PERMISSION_FACTORY=my_permission_factory
)


accounts = InvenioAccounts(app)
app.register_blueprint(blueprint)

Menu(app)

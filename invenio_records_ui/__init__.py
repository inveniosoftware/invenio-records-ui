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

r"""Module for displaying records.

Invenio-Records-UI is a core component of Invenio which provides
configurable views for display records. It uses Invenio-PIDStore to resolve
an external persistent identifier into an internal record object. It also has
support for displaying tombstones for deleted records, as well as redirecting
an external persistent identifier to another in case e.g. records are merged.

In simple terms, Records-UI works by creating one or more **endpoints** for
displaing records. You can e.g. have one endpoint (``/records/``) for
displaying bibliographic records and another endpoint (``/authors/``) for
displaying author records.

One **endpoint** is bound to one and only one specific persistent identifier
type. For instance, ``/records/`` could be bound to integer record identifiers,
while ``/authors/`` could be bound to ORCID identifiers.

Initialization
--------------
First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> from flask_cli import FlaskCLI
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> ext_cli = FlaskCLI(app)

You initialize Records-UI like a normal Flask extension, however
Invenio-Records-UI is dependent on Invenio-Records, Invenio-PIDStore and
Invenio-DB so you need to initialize these extensions first:

>>> from invenio_db import InvenioDB
>>> from invenio_records import InvenioRecords
>>> from invenio_pidstore import InvenioPIDStore
>>> from invenio_records_ui import InvenioRecordsUI
>>> ext_db = InvenioDB(app)
>>> ext_pidstore = InvenioPIDStore(app)
>>> ext_records = InvenioRecords(app)

Configuration
~~~~~~~~~~~~~
Before we initialize the InvenioRecordsUI extension, we need to configure which
endpoints we want to expose. Let's start with one endpoint ``/records/`` which
resolves integer record identifiers to internal record objects.

>>> app.config["RECORDS_UI_ENDPOINTS"] = dict(
...     recid=dict(
...         pid_type='recid',
...         route='/records/<pid_value>',
...         template='invenio_records_ui/detail.html',
...     ),
... )

Here we create a single endpoint named ``recid`` (note, the naming of endpoints
are important - see the section on redirection for details). The endpoint
resolves ``recid`` persistent identifiers (see ``pid_type`` key), on the URL
route ``/records/<pid_value>``.

You are free to choose any URL route as long as it includes the ``<pid_value>``
URL pattern in the route.

The created endpoint will render the template
``invenio_records_ui/detail.html`` which will be passed the following two
variables in the template context:

- ``pid`` - A PersistentIdentier object.
- ``record`` - An internal record object.

Installing endpoints
~~~~~~~~~~~~~~~~~~~~
We have now configured which endpoint we want, so we can go ahead and install
the extension (note, in this example we switch off the permission checking
capabilities by setting ``RECORDS_UI_DEFAULT_PERMISSION_FACTORY`` to ``None``):

>>> app.config['RECORDS_UI_DEFAULT_PERMISSION_FACTORY'] = None
>>> ext_records_ui = InvenioRecordsUI(app)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and tables (note,
in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Displaying a record
-------------------
Before we can display a record, we need a persistent identifier and a record,
so let's create them:

>>> from uuid import uuid4
>>> from invenio_db import db
>>> from invenio_records.api import Record
>>> from invenio_pidstore.providers.recordid import RecordIdProvider
>>> rec_uuid = uuid4()
>>> rec = Record.create({'tite': 'My title'}, id_=rec_uuid)
>>> provider = RecordIdProvider.create(object_type='rec', object_uuid=rec_uuid)
>>> db.session.commit()

In above example we use the ``RecordIdProvider`` to create a ``recid``
persistent identifier type:

>>> print(provider.pid.pid_type)
recid
>>> print(provider.pid.pid_value)
1

We can now access the record:

>>> with app.test_client() as client:
...     res = client.get('/records/1')
>>> res.status_code
200

If you try to access a non-existing record, you will naturally receive a not
found page:

>>> with app.test_client() as client:
...     res = client.get('/records/2')
>>> res.status_code
404

It is important to note that only persistent identifiers in `registered` state
will resolve. If you have a persistent identifier in `new` state, it will
return a ``404`` error code.

Tombstones
----------
If you need to delete a record for some reason, it's possible to display a
tombstone for the record, so that any external links to the record may still
see a landing page with information on why a given record was removed.

First, let's create a persistent identifier and delete it:

>>> provider = RecordIdProvider.create()
>>> print(provider.pid.pid_value)
2
>>> provider.pid.delete()
True
>>> db.session.commit()

If we now try to access the same record as before, we will receive a ``410``
error code:

>>> with app.test_client() as client:
...     res = client.get('/records/2')
>>> res.status_code
410

The template being rendered is ``invenio_records_ui/tombstone.html``, which you
can change using the ``RECORDS_UI_TOMBSTONE_TEMPLATE`` configuration variable:

>>> app.config['RECORDS_UI_TOMBSTONE_TEMPLATE']
'invenio_records_ui/tombstone.html'

The template will receive two variables in the template context:

- ``pid`` - the persistent identifier
- ``record`` - the internal record object or an empty dict in case no record
  was assigned to the persistent identifier.

Redirection
-----------
You can redirect one persistent identifier to another persistent identifier.
This can be useful in cases where you need to e.g. merge two records.

Let's create a persistent identifier and redirect it:

>>> from invenio_pidstore.models import PersistentIdentifier, \
...     PIDStatus
>>> provider = RecordIdProvider.create(
...     status=PIDStatus.REGISTERED)
>>> provider.pid.redirect(
...     PersistentIdentifier.get('recid', '1'))
True
>>> db.session.commit()

If you now try to access the redirected persistent identifier, you will be
redirected:

>>> with app.test_client() as client:
...     res = client.get('/records/3')
>>> res.status_code
302
>>> print(res.location)
http://localhost/records/1

Naming of endpoints
~~~~~~~~~~~~~~~~~~~
For redirection to work for a given persistent identifier type, you must
provide exactly one endpoint with the name of the type. For instance, in the
redirection above, we redirected a ``recid`` persistent identifier type to
another ``recid`` persistent identifier type. This redirect works because
we named the endpoint ``recid``:

>>> app.config['RECORDS_UI_ENDPOINTS']
{'recid': ...}

Had we instead named the endpoint e.g. ``records``, the redirect would not have
worked.

Signals
-------
Every time a record is viewed a signal is sent. This allows you to e.g.
track viewing events. In this example, let's just create a signal receiver
which prints the persistent identifier which was viewed:

>>> from invenio_records_ui.signals import record_viewed
>>> def receiver(sender, record=None, pid=None):
...     print("Viewed record {0}".format(pid.pid_value))

If we now try to access the record

>>> with record_viewed.connected_to(receiver):
...     with app.test_client() as client:
...         res = client.get('/records/1')
Viewed record 1
>>> res.status_code
200

Access control
--------------
Invenio-Records-UI is integrated with Flask-Principal to provide access control
to records. To protect access to a record you must provide a
*permission factory*. A permission factory is a simple method which takes a
record and returns an permission instance:

>>> from flask_principal import Permission, RoleNeed
>>> def perm_factory(record):
...     return Permission(RoleNeed('admin'))

This allows the permission factory to make use of any information inside and
outside of the record in order to create a permission to protect it. This
allows very fine-grained control with who can access which record and how you
protect it.

The permission factory you can apply globally to all endpoints by
setting ``RECORDS_UI_DEFAULT_PERMISSION_FACTORY`` to the import path of the
permission factory:

>>> app.config['RECORDS_UI_DEFAULT_PERMISSION_FACTORY'] = \
...     'invenio_records.permissions:permission_factory'

Alternatively you can also apply a permission factory to only a specific
endpoint by passing the ``permission_factory_imp`` argument:

>>> app.config["RECORDS_UI_ENDPOINTS"] = dict(
...     recid=dict(
...         pid_type='recid',
...         route='/records/<pid_value>',
...         template='invenio_records_ui/detail.html',
...         permission_factory_imp=
...         'invenio_records.permissions:permission_factory'
...     ),
... )
"""

from __future__ import absolute_import, print_function

from .ext import InvenioRecordsUI
from .version import __version__

__all__ = ('__version__', 'InvenioRecordsUI')

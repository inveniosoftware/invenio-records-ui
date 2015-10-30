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

"""Record module signals."""

from blinker import Namespace

_signals = Namespace()


record_viewed = _signals.signal('record-viewed')
"""Signal is sent when a detailed view of record is displayed.

Parameters:
    sender - current Flask application object.
    pid - persistent identifier instance
    record - record instance


Example subscriber:

.. code-block:: python
     from flask import request

     def subscriber(sender, record=None, pid=None):
         ...

Note, the signal is always sent in a request context, thus it is safe to
access the current request and/or current user objects.
"""

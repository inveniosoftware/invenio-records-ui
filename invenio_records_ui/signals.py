# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record module signals."""

from __future__ import absolute_import, print_function

from blinker import Namespace

_signals = Namespace()


record_viewed = _signals.signal('record-viewed')
"""Signal sent when a record is viewed on any endpoint.

Parameters:

- ``sender`` - a Flask application object.
- ``pid`` - a persistent identifier instance.
- ``record`` - a record instance.


Example receiver:

.. code-block:: python

   def receiver(sender, record=None, pid=None):
       # ...

Note, the signal is always sent in a request context, thus it is safe to
access the current request and/or current user objects inside the receiver.
"""

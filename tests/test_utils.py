# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

from invenio_records_ui.utils import obj_or_import_string


def myfunc():
    """Example function."""
    pass


def test_obj_or_import_string(app):
    """Test obj_or_import_string."""
    assert not obj_or_import_string(value=None)
    assert myfunc == obj_or_import_string(value=myfunc)

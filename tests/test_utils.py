# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT


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

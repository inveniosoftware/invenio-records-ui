# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helpers."""

from __future__ import absolute_import, print_function

from flask_security import current_user


def only_authenticated_users(record, *args, **kwargs):
    """Allow access for authenticated users."""
    def can(self):
        return current_user.is_authenticated
    return type('OnlyAuthenticatedUsers', (), {'can': can})()

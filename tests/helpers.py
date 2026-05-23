# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Helpers."""

from __future__ import absolute_import, print_function

from flask_security import current_user


def only_authenticated_users(record, *args, **kwargs):
    """Allow access for authenticated users."""

    def can(self):
        return current_user.is_authenticated

    return type("OnlyAuthenticatedUsers", (), {"can": can})()

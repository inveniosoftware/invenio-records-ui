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

"""User interface for Invenio-Records."""

from __future__ import absolute_import, print_function

from functools import partial

from flask import Blueprint, abort, current_app, render_template
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record

from .signals import record_viewed


def create_blueprint(endpoints, with_tombstone=True):
    """Create Invenio-Records-UI blueprint.

    :param blueprint: Name of blueprint (important for url_for).
    :param url_prefix: URL prefix for blueprint.
    :param pid_type: Persistent identifier type to create blueprint for.
    :param routing: Dictionary describing routing for views.
    """
    blueprint = Blueprint(
        'invenio_records_ui',
        __name__,
        url_prefix='',
        template_folder='templates',
        static_folder='static',
    )

    for endpoint, options in (endpoints or {}).items():
        blueprint.add_url_rule(**create_url_rule(endpoint, **options))

    return blueprint


def create_url_rule(endpoint, route=None, pid_type=None, pid_provider=None,
                    template=None):
    """Create Werkzeug URL rule."""
    assert route
    assert pid_type

    return dict(
        endpoint=endpoint,
        rule=route,
        view_func=partial(
            record_view,
            resolver=Resolver(pid_type=pid_type, pid_provider=pid_provider,
                              obj_type='rec', getter=Record.get_record),
            template=template or 'invenio_records_ui/detail.html'),
    )


def record_view(pid_value=None, resolver=None, template=None, **kwargs):
    """Display record for a given persistent identifier value.

    .. warning::

       The two parameters ``resolver`` and ``template`` should not be included
       in the URL rule, but set by defaults to the view.


    :param pid_value: Persistent identifier.
    :param resolver: An instance of a persistent identifier resolver. A
        persistent identifier resolver takes care of resolving persistent
        identifiers into internal objects.
    :param template: Template to render.
    """
    try:
        pid, record = resolver.resolve(pid_value)
    except PIDDeletedError:
        abort(410)
    except (PIDDoesNotExistError, PIDMissingObjectError):
        abort(404)
    # except PIDMergedError as e:
    #     return redirect(url_for(
    #         request.endpoint, pid_value=e.new_pid_value, **kwargs))

    record_viewed.send(
        current_app._get_current_object(),
        pid=record,
        record=record,
    )
    return render_template(
        template,
        pid=pid,
        record=record,
    )

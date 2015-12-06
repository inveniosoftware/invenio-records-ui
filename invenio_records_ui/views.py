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

"""Factory for creating a blueprint for Invenio-Records-UI."""

from __future__ import absolute_import, print_function

from functools import partial

from flask import Blueprint, abort, current_app, redirect, render_template, \
    request, url_for
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError, PIDRedirectedError, PIDUnregistered
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from werkzeug.local import LocalProxy
from werkzeug.routing import BuildError
from werkzeug.utils import import_string

from .signals import record_viewed

current_permission_factory = LocalProxy(
    lambda: current_app.extensions['invenio-records-ui'].permission_factory)


def create_blueprint(endpoints):
    """Factory for Invenio-Records-UI blueprint creation.

    The factory installs one URL route per endpoint defined, and adds an
    error handler for rendering tombstones.

    :param endpoints: Dictionary of endpoints to be installed. See usage
        documentation for further details.
    """
    blueprint = Blueprint(
        'invenio_records_ui',
        __name__,
        url_prefix='',
        template_folder='templates',
        static_folder='static',
    )

    @blueprint.errorhandler(PIDDeletedError)
    def tombstone_errorhandler(error):
        return render_template(
            current_app.config['RECORDS_UI_TOMBSTONE_TEMPLATE'],
            pid=error.pid,
            record=error.record or {},
        ), 410

    for endpoint, options in (endpoints or {}).items():
        blueprint.add_url_rule(**create_url_rule(endpoint, **options))

    return blueprint


def create_url_rule(endpoint, route=None, pid_type=None, template=None,
                    permission_factory_imp=None):
    """Create Werkzeug URL rule for a specific endpoint.

    The method takes care of creating a persistent identifier resolver
    for the given persistent identifier type.

    :param endpoint: Name of endpoint.
    :param route: URL route (must include ``<pid_value>`` pattern). Required.
    :param pid_type: Persistent identifier type for endpoint. Required.
    :param template: Template to render. Defaults to
        ``invenio_records_ui/detail.html``.
    :param permission_factory: Import path to factory that creates a permission
        object for a given record.
    :returns: a dictionary that can be passed as keywords arguments to
        ``Blueprint.add_url_rule``.
    """
    assert route
    assert pid_type

    permission_factory = import_string(permission_factory_imp) if \
        permission_factory_imp else None

    view_func = partial(
        record_view,
        resolver=Resolver(pid_type=pid_type, object_type='rec',
                          getter=Record.get_record),
        template=template or 'invenio_records_ui/detail.html',
        permission_factory=permission_factory)
    # Make view well-behaved for Flask-DebugToolbar
    view_func.__module__ = record_view.__module__
    view_func.__name__ = record_view.__name__

    return dict(
        endpoint=endpoint,
        rule=route,
        view_func=view_func,
    )


def record_view(pid_value=None, resolver=None, template=None,
                permission_factory=None, **kwargs):
    """Generic view for displaying a record.

    The two parameters ``resolver`` and ``template`` should not be included
    in the URL rule, but instead set by creating a partially evaluated function
    of the view.

    The template being rendered is passed two variables in the template
    context:

    - ``pid``
    - ``record``.

    :param pid_value: Persistent identifier value.
    :param resolver: An instance of a persistent identifier resolver. A
        persistent identifier resolver takes care of resolving persistent
        identifiers into internal objects.
    :param template: Template to render.
    """
    try:
        pid, record = resolver.resolve(pid_value)
    except (PIDDoesNotExistError, PIDUnregistered):
        abort(404)
    except PIDMissingObjectError as e:
        current_app.logger.exception(
            "No object assigned to {0}.".format(e.pid),
            extra={'pid': e.pid})
        abort(500)
    except PIDRedirectedError as e:
        try:
            return redirect(url_for(
                'invenio_records_ui.{0}'.format(e.destination_pid.pid_type),
                pid_value=e.destination_pid.pid_value))
        except BuildError:
            current_app.logger.exception(
                "Invalid redirect - pid_type '{0}' endpoint missing.".format(
                    e.destination_pid.pid_type),
                extra={
                    'pid': e.pid,
                    'destination_pid': e.destination_pid,
                })
            abort(500)

    # Check permissions
    permission_factory = permission_factory or current_permission_factory
    if permission_factory:
        # Note, cannot be done in one line due overloading of boolean
        # operations permission object.
        if not permission_factory(record).can():
            from flask_login import current_user
            if not current_user.is_authenticated:
                return redirect(url_for(
                    current_app.config['RECORDS_UI_LOGIN_ENDPOINT'],
                    next=request.url))
            abort(403)

    record_viewed.send(
        current_app._get_current_object(),
        pid=pid,
        record=record,
    )
    return render_template(
        template,
        pid=pid,
        record=record,
    )

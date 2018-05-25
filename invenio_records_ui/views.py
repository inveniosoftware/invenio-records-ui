# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Factory for creating a blueprint for Invenio-Records-UI."""

from __future__ import absolute_import, print_function

from functools import partial

import six
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
from .utils import obj_or_import_string

current_permission_factory = LocalProxy(
    lambda: current_app.extensions['invenio-records-ui'].permission_factory)


def create_blueprint_from_app(app):
    """Create Invenio-Records-UI blueprint from a Flask application.

    .. note::

        This function assumes that the application has loaded all extensions
        that want to register REST endpoints via the ``RECORDS_UI_ENDPOINTS``
        configuration variable.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    return create_blueprint(app.config.get('RECORDS_UI_ENDPOINTS'))


def create_blueprint(endpoints):
    """Create Invenio-Records-UI blueprint.

    The factory installs one URL route per endpoint defined, and adds an
    error handler for rendering tombstones.

    :param endpoints: Dictionary of endpoints to be installed. See usage
        documentation for further details.
    :returns: The initialized blueprint.
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

    @blueprint.context_processor
    def inject_export_formats():
        return dict(
            export_formats=(
                current_app.extensions['invenio-records-ui'].export_formats)
            )

    for endpoint, options in (endpoints or {}).items():
        blueprint.add_url_rule(**create_url_rule(endpoint, **options))

    return blueprint


def create_url_rule(endpoint, route=None, pid_type=None, template=None,
                    permission_factory_imp=None, view_imp=None,
                    record_class=None, methods=None):
    """Create Werkzeug URL rule for a specific endpoint.

    The method takes care of creating a persistent identifier resolver
    for the given persistent identifier type.

    :param endpoint: Name of endpoint.
    :param route: URL route (must include ``<pid_value>`` pattern). Required.
    :param pid_type: Persistent identifier type for endpoint. Required.
    :param template: Template to render.
        (Default: ``invenio_records_ui/detail.html``)
    :param permission_factory_imp: Import path to factory that creates a
        permission object for a given record.
    :param view_imp: Import path to view function. (Default: ``None``)
    :param record_class: Name of the record API class.
    :param methods: Method allowed for the endpoint.
    :returns: A dictionary that can be passed as keywords arguments to
        ``Blueprint.add_url_rule``.
    """
    assert route
    assert pid_type

    permission_factory = import_string(permission_factory_imp) if \
        permission_factory_imp else None
    view_method = import_string(view_imp) if view_imp else default_view_method
    record_class = import_string(record_class) if record_class else Record
    methods = methods or ['GET']

    view_func = partial(
        record_view,
        resolver=Resolver(pid_type=pid_type, object_type='rec',
                          getter=record_class.get_record),
        template=template or 'invenio_records_ui/detail.html',
        permission_factory=permission_factory,
        view_method=view_method)
    # Make view well-behaved for Flask-DebugToolbar
    view_func.__module__ = record_view.__module__
    view_func.__name__ = record_view.__name__

    return dict(
        endpoint=endpoint,
        rule=route,
        view_func=view_func,
        methods=methods,
    )


def record_view(pid_value=None, resolver=None, template=None,
                permission_factory=None, view_method=None, **kwargs):
    """Display record view.

    The two parameters ``resolver`` and ``template`` should not be included
    in the URL rule, but instead set by creating a partially evaluated function
    of the view.

    The template being rendered is passed two variables in the template
    context:

    - ``pid``
    - ``record``.

    Procedure followed:

    #. PID and record are resolved.

    #. Permission are checked.

    #. ``view_method`` is called.

    :param pid_value: Persistent identifier value.
    :param resolver: An instance of a persistent identifier resolver. A
        persistent identifier resolver takes care of resolving persistent
        identifiers into internal objects.
    :param template: Template to render.
    :param permission_factory: Permission factory called to check if user has
        enough power to execute the action.
    :param view_method: Function that is called.
    :returns: Tuple (pid object, record object).
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
                '.{0}'.format(e.destination_pid.pid_type),
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
        # Note, cannot be done in one line due to overloading of boolean
        # operations in permission object.
        if not permission_factory(record).can():
            from flask_login import current_user
            if not current_user.is_authenticated:
                return redirect(url_for(
                    current_app.config['RECORDS_UI_LOGIN_ENDPOINT'],
                    next=request.url))
            abort(403)

    return view_method(pid, record, template=template, **kwargs)


def default_view_method(pid, record, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
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


def export(pid, record, template=None, **kwargs):
    r"""Record serialization view.

    Serializes record with given format and renders record export template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
    """
    formats = current_app.config.get('RECORDS_UI_EXPORT_FORMATS', {}).get(
        pid.pid_type)
    fmt = formats.get(request.view_args.get('format'))

    if fmt is False:
        # If value is set to False, it means it was deprecated.
        abort(410)
    elif fmt is None:
        abort(404)
    else:
        serializer = obj_or_import_string(fmt['serializer'])
        data = serializer.serialize(pid, record)
        if isinstance(data, six.binary_type):
            data = data.decode('utf8')

        return render_template(
            template, pid=pid, record=record, data=data,
            format_title=fmt['title'],
        )

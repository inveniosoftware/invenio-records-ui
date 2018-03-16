# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test example app."""

import os
import signal
import subprocess
import time

import pytest


def _create_example_app(app_name):
    """Example app fixture."""
    current_dir = os.getcwd()
    # go to example directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)
    # setup example
    cmd = 'FLASK_APP={0} ./app-setup.sh'.format(app_name)
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # Starting example web app
    cmd = 'FLASK_APP={0} flask run --debugger -p 5000'.format(app_name)
    webapp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              preexec_fn=os.setsid, shell=True)
    time.sleep(10)
    # return webapp
    yield webapp
    # stop server
    os.killpg(webapp.pid, signal.SIGTERM)
    # tear down example app
    cmd = 'FLASK_APP={0} ./app-teardown.sh'.format(app_name)
    subprocess.call(cmd, shell=True)
    # return to the original directory
    os.chdir(current_dir)


@pytest.yield_fixture
def example_app():
    for i in _create_example_app('app.py'):
        yield i


@pytest.yield_fixture
def perms_app():
    for i in _create_example_app('permsapp.py'):
        yield i


def test_example_app(example_app):
    """Test example app."""
    # load fixtures
    cmd = 'FLASK_APP={0} ./app-fixtures.sh'.format('app.py')
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # open page
    cmd = 'curl http://localhost:5000/records/1'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'Ellis Jonathan' in output
    cmd = 'curl http://localhost:5000/records/2'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'Ellis Jonathan' in output


def test_example_permsapp(perms_app):
    """Test example permsapp."""
    # load fixtures
    cmd = 'FLASK_APP={0} ./app-fixtures.sh'.format('permsapp.py')
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # open page
    cmd = 'curl http://localhost:5000/records/1'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'Ellis Jonathan' in output
    cmd = 'curl http://localhost:5000/records/2'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    assert 'Redirect' in output

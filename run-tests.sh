#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

pydocstyle invenio_records_ui tests docs
isort invenio_records_ui tests --check-only --diff
check-manifest --ignore ".*-requirements.txt"
sphinx-build -qnNW docs docs/_build/html
docker-services-cli up ${DB}
python setup.py test
tests_exit_code=$?
docker-services-cli down
exit "$tests_exit_code"

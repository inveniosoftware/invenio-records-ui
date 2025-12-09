..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.
    Copyright (C) 2024 Graz University of Technology.
    Copyright (C) 2025 KTH Royal Institute of Technology.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v2.1.2 (released 2025-12-09)

- i18n: pulled translations

Version v2.1.1 (released 2025-10-22)

- i18n: pulled translations 

Version v2.1.0 (released 2025-07-17)

- i18n: force pull languages
- i18n: run py extract msgs
- i18n: update Transifex host and config
- feat: add i18n workflows for pulling and pushing translations
- fix: setuptools require underscores instead of dashes
- doctest: including invenio-i18n to doctest
- i18n: translate export & tombstone templates

Version 2.0.0 (release 2024-12-06)

- setup: bump major dependencies

Version 1.2.2 (release 2024-12-01)

- fix: tests by changed api
- tests: migrate flask_babelex to invenio_i18n
- global: remove examples
- fix: SphinxWarning
- setup: change to reusable workflows
- setup: pin dependencies

Version 1.2.1 (released 2024-08-07)

- views: add `__qualname__` to fix views due to flask-limiter

Version 1.2.0 (released 2020-12-02)

- Integrates Semantic-UI templates
- Migrates CI from Travis to GitHub Actions

Version 1.2.0a1 (released 2020-05-15)

- Integrates Semantic-UI templates

Version 1.0.1 (released 2020-03-12)

- Adds centralised management of flask dependency through invenio-base
- drops support for Python 2.7


Version 1.0.1 (released 2018-05-25)

- Changes dynamic blueprint registration to after the extension
  initialization phase (entry point works only with Invenio-Base v1.0.1+).

Version 1.0.0 (released 2018-03-23)

- Initial public release.

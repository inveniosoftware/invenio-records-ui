Installation
============

Invenio-Records-UI is on PyPI so all you need is:

.. code-block:: console

   $ pip install invenio-records-ui

Invenio-Records-UI depends on Invenio-Records, Invenio-PIDStore and Invenio-DB.

Configuration
-------------

=============================== ===============================================
`RECORDS_UI_BASE_TEMPLATE`      Base template for other templates in this
                                module.
                                Default: ``invenio_records_ui/base.html``.

`RECORDS_UI_TOMBSTONE_TEMPLATE` Template to render for tombstones.
                                Default: ``invenio_records_ui/tombstone.html``.

`RECORDS_UI_ENDPOINTS`          Dictionary of endpoints to install. See
                                :ref:`usage` for details.
=============================== ===============================================

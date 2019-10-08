Blockstore
===================================================

Blockstore is a system for authoring, discovering, and reusing educational content for Open edX.
It is meant to be a lower-level service than the modulestore, and is designed around the concept of storing small, reusable pieces of content, rather than large, fixed content structures such as courses.
For Open edX, Blockstore is designed to facilitate a much greater level of content re-use than is currently possible, enable new adaptive learning features, and enable delivery of learning content in new ways (not just large traditional courses).

See DESIGN_ for more details.

Blockstore has been developed by Harvard's LabXchange_ and the `Amgen Foundation`_, with significant in-kind contributions from edX_.

.. _DESIGN: https://openedx.atlassian.net/wiki/spaces/AC/pages/737149430/Blockstore+Design

.. _LabXchange: https://about.labxchange.org

.. _`Amgen Foundation`: https://www.amgen.com/responsibility/amgen-foundation/

.. _edX: https://www.edx.org

.. Documentation
.. -------------
.. .. |ReadtheDocs| image:: https://readthedocs.org/projects/blockstore/badge/?version=latest
.. .. _ReadtheDocs: http://blockstore.readthedocs.io/en/latest/
..
.. `Documentation <https://blockstore.readthedocs.io/en/latest/>`_ is hosted on Read the Docs. The source is hosted in this repo's `docs <https://github.com/edx/blockstore/tree/master/docs>`_ directory. To contribute, please open a PR against this repo.

Using with Docker Devstack
--------------------------

Prerequisite: Have your Open edX `Devstack <https://github.com/edx/devstack>`_ properly installed.

#. Clone this repo and ``cd`` into it.

#. To start the django development server inside a docker container, run this on
   your host machine:

   .. code::

       make easyserver

   Then you'll be able to access Blockstore at http://localhost:18250/

#. Run ``make`` to get a list of other available commands.

#. To log in to Blockstore, you'll need to configure SSO with your devstack.

   #. Go to http://localhost:18000/admin/oauth2_provider/application/ and add a new application
   #. Set "Client id" to ``blockstore-sso-key``
   #. Set "Redirect uris" to ``http://localhost:18250/complete/edx-oauth2/``
   #. Set "Client type" to "Confidential"
   #. Set "Authorization grant type" to "Authorization code"
   #. Set "Name" to ``blockstore-sso``
   #. Check "Skip authorization"
   #. Press "Save and continue editing"
   #. Go to http://localhost:18000/admin/oauth_dispatch/applicationaccess/
   #. Click "Add Application Access +", choose Application: ``blockstore-sso`` and set Scopes to ``user_id``, then hit "Save"
   #. Copy ``blockstore/settings/private.py.example`` to ``blockstore/settings/private.py``
   #. In ``private.py``, set ``SOCIAL_AUTH_EDX_OAUTH2_SECRET`` to the random "Client secret" value.
   #. Now you can login at http://localhost:18250/login/

Get Help
--------

Ask questions and discuss this project on `Slack <https://openedx.slack.com/messages/general/>`_ or in the `edx-code Google Group <https://groups.google.com/forum/#!forum/edx-code>`_.

License
-------

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. Please see the LICENSE_ file for details.

.. _LICENSE: https://github.com/edx/blockstore/blob/master/LICENSE

How To Contribute
-----------------

Contributions are welcome. Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details. Even though it was written with ``edx-platform`` in mind, these guidelines should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

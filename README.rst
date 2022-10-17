==========
Blockstore
==========

|status-badge| |license-badge| |ci-badge|

-------
Purpose
-------

Blockstore is a system for storing versioned, reusable educational content for Open edX.

It is designed as a replacement for `modulestore <https://github.com/openedx/edx-platform/tree/master/xmodule/modulestore>`_. It is meant to be a lower-level service than the modulestore, and is designed around the concept of storing small, reusable pieces of content, rather than large, fixed content structures such as courses. For Open edX, Blockstore is designed to facilitate a much greater level of content re-use than is currently possible, enable new adaptive learning features, and enable delivery of learning content in new ways (not just large traditional courses).

.. list-table:: Comparison
   :widths: 20 40 40
   :header-rows: 1

   * - System
     - Modulestore
     - Blockstore
   * - Goal
     - Designed to store courses consisting of a hierarchy of XModules (and later, XBlocks)
     - Designed around the concept of storing small, reusable pieces of content which are simply files. Can be used for content libraries, courses, or any other purpose.
   * - Stores data in
     - MongoDB
     - S3 (or similar)
   * - Stores XBlock data as
     - JSON field data, with "settings" and "content" fields separated in different documents
     - `OLX <https://edx.readthedocs.io/projects/edx-open-learning-xml/en/latest/what-is-olx.html>`_
   * - Content re-use
     - Very limited support
     - Built in support
   * - Focus
     - Includes deeply integrated XModule runtime, increasing complexity
     - Not aware of XBlocks; XBlock runtime is implemented `separately <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/xblock/runtime/blockstore_runtime.py>`_
   * - Associated XBlock runtime (LMS)
     -  `LmsModuleSystem <https://github.com/openedx/edx-platform/blob/db32ff2cdf678fa8edd12c9da76a76eef0478614/lms/djangoapps/lms_xblock/runtime.py#L137>`_
     -  `BlockstoreXBlockRuntime <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/runtime/blockstore_runtime.py#L28>`_
   * - Image/PDF/other asset files used for each XBlock are stored
     - In MongoDB at the course level (contentstore/GridFS)
     - Alongside each XBlock's OLX file. Associated with the individual XBlock, not the course.

Blockstore was originally developed by Harvard's  `LabXchange <https://www.labxchange.org/>`_ and the `Amgen Foundation <https://www.amgen.com/responsibility/amgen-foundation/>`_, along with `edX <https://www.edx.org>`_.

--------------
Current Status
--------------

As of **April 2022** ("master" version of Open edX) or the **Nutmeg** named release of Open edX, Blockstore is included as a django app within Open edX platform. See `moving blockstore into edx-platform <decisions/0002-app-not-service.rst>`_ for an explanation of this. Prior to those versions, Blockstore was only available as an independent application, and was not included in any Open edX installations by default.

Blockstore is used to power the **Content Libraries v2** feature of Open edX. It is *not* directly used for course functionality, nor for the "v1" Content Libraries feature.

--------------
Design Details
--------------

See `DESIGN <DESIGN.rst>`_ for an overview of Blockstore's design as it exists today. See `"Blockstore Design" <https://openedx.atlassian.net/wiki/spaces/AC/pages/737149430/Blockstore+Design>`_ on the wiki for historical context.

---------------
Getting Started
---------------

The easiest way to try out the "Content Libraries v2" feature along with Blockstore is to use the Tutor devstack and
`the library-authoring MFE Tutor plugin <https://github.com/openedx/frontend-app-library-authoring/tree/master/tutor-contrib-library-authoring-mfe#readme>`_. See that plugin's README for details.

-------------------------
Running Integration Tests
-------------------------

Open edX includes some integration tests for Blockstore, which run by default as part of the test suite. To run them manually, from a Studio/CMS shell, run these commands:

.. code::

   python -Wd -m pytest --ds=cms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/
   python -Wd -m pytest --ds=lms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/

To run these integration tests while using Elasticsearch, add ``EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1`` to the beginning of the above commands. To run these integration tests while using a specific container's version of Elasticsearch, also add ``EDXAPP_TEST_ELASTICSEARCH_HOST`` with a specific container name on the above commands:

.. code::

   EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1 EDXAPP_TEST_ELASTICSEARCH_HOST=edx.devstack.elasticsearch710 python -Wd -m pytest ...

-------------------
Using in Production
-------------------

By default, blockstore is run as an app inside of Open edX. Enable it using the waffle switch `blockstore.use_blockstore_app_api <https://edx.readthedocs.io/projects/edx-platform-technical/en/latest/featuretoggles.html#featuretoggle-blockstore.use_blockstore_app_api>`_.

If you need to run blockstore as a separate service (e.g. for scalability or performance reasons), you can deploy blockstore in production using `the blockstore ansible role <https://github.com/openedx/configuration/tree/master/playbooks/roles/blockstore>`_.

-------------------------------------------------------
Running and testing as a separate service (development)
-------------------------------------------------------

Blockstore was initially developed as an independently deployed application, which runs in a separate container/proccess from the LMS. It is still possible to run blockstore that way, both in production and development.

To run it as an independent application in development:

#. Prerequisite: Have an Open edX `Devstack <https://github.com/openedx/devstack>`_ properly installed and working. Your devstack must use the Nutmeg release of Open edX (or newer) or be tracking the ``master`` branch of ``edx-platform``.

#. Clone this repo and ``cd`` into it.

#. To start the django development server inside a docker container, run this on
   your host machine:

   .. code::

      make easyserver

   Blockstore is now running at http://localhost:18250/ . Now we need to configure Studio/LMS to work with it.

#. Run these commands on your host computer:

   .. code::

      # Create a service user for the edx-platform to use when authenticating and making API calls
      docker exec -t edx.devstack.blockstore bash -c "source ~/.bashrc && echo \"from django.contrib.auth import get_user_model; from rest_framework.authtoken.models import Token; User = get_user_model(); edxapp_user, _ = User.objects.get_or_create(username='edxapp'); Token.objects.get_or_create(user=edxapp_user, key='edxapp-insecure-devstack-key')\" | ./manage.py shell"
      # Configure the LMS and Studio to use the key
      docker exec -t edx.devstack.lms bash -c "grep BLOCKSTORE_API_AUTH_TOKEN /edx/app/edxapp/edx-platform/lms/envs/private.py || echo BLOCKSTORE_API_AUTH_TOKEN = \'edxapp-insecure-devstack-key\' >> /edx/app/edxapp/edx-platform/lms/envs/private.py"
      docker exec -t edx.devstack.studio bash -c "grep BLOCKSTORE_API_AUTH_TOKEN /edx/app/edxapp/edx-platform/cms/envs/private.py || echo BLOCKSTORE_API_AUTH_TOKEN = \'edxapp-insecure-devstack-key\' >> /edx/app/edxapp/edx-platform/cms/envs/private.py"
      # Create a "Collection" that new content libraries / xblocks can be created within:
      docker exec -t edx.devstack.blockstore bash -c "source ~/.bashrc && echo \"from blockstore.apps.bundles.models import Collection; coll, _ = Collection.objects.get_or_create(title='Devstack Content Collection', uuid='11111111-2111-4111-8111-111111111111')\" | ./manage.py shell"
      # Create an "Organization":
      docker exec -t edx.devstack.lms bash -c "source /edx/app/edxapp/edxapp_env && echo \"from organizations.models import Organization; Organization.objects.get_or_create(short_name='DeveloperInc', defaults={'name': 'DeveloperInc', 'active': True})\" | python /edx/app/edxapp/edx-platform/manage.py lms shell"

   Then restart Studio and the LMS (``make dev.restart-devserver.lms dev.restart-devserver.studio``).

#. Now you should be able to use Blockstore in Studio.

   To edit Blockstore content libraries in Studio, you'll need to install either `the Content Libraries v2 Frontend <https://github.com/openedx/frontend-app-library-authoring/>`_ or `Ramshackle <https://github.com/open-craft/ramshackle/>`_. Alternatively, you can use the `Content Libraries v2 REST API <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/content_libraries/urls.py>`_ to create content programmatically.

   To use Blockstore library content in a course, open your course in Studio. In its advanced settings, add ``library_sourced`` to the list of "advanced block types". In the "Unit Edit View" in Studio, find the green "Add New Component" buttons. Click Advanced > Library Sourced Content. Edit the new Library Sourced Content XBlock to enter the XBlock ID of the library content that you'd like to use. It should be similar to ``lb:DeveloperInc:MyLibrary:1`` (note: ``lb:`` is short for "Library Block" and should not be confused with the ``lib:`` prefix used to identify a library).

#. Optional: To log in to Blockstore in your web browser directly, you'll need to configure SSO with your devstack. Most people won't need to do this, but it's helpful for debugging or development.

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

#. Optional: If running an Open edX devstack under a project name different
   than the default (support for which was introduced
   [here](https://github.com/openedx/devstack/pull/532)), simply export
   ``OPENEDX_PROJECT_NAME`` and substitute the container names in the commands
   above accordingly.

#. Optional: to run the unit tests in this mode:

   #. Get into the blockstore container: ``make blockstore-shell``
   #. And then run ``make test``

#. Optional: to run the integration tests in this mode:

   Open edX includes some integration tests for Blockstore. To run them with a separate blockstore instance, first start an isolated test version of blockstore by running ``make testserver`` from the ``blockstore`` repo root directory on your host computer. Then, from ``make dev.shell.studio``, run these commands:

   #. ``EDXAPP_RUN_BLOCKSTORE_TESTS=1 python -Wd -m pytest --ds=cms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/``
   #. ``EDXAPP_RUN_BLOCKSTORE_TESTS=1 python -Wd -m pytest --ds=lms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/``

------------
Getting Help
------------

Ask questions and discuss this project on `Slack <https://openedx.slack.com/messages/general/>`_ or the `Open edX Community Discussion Forum <https://discuss.openedx.org/>`_.

------------
Contributing
------------

Contributions are welcome. Please read `How To Contribute <https://github.com/openedx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details. Even though it was written with ``edx-platform`` in mind, these guidelines should be followed for Open edX code in general.

----------------------------
The Open edX Code of Conduct
----------------------------

All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

------
People
------

The assigned maintainers for this component and other project details may be
found in `Backstage`_. Backstage pulls this data from the ``catalog-info.yaml``
file in this repo.

.. _Backstage: https://backstage.openedx.org/catalog/default/component/blockstore


-------------------------
Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.


.. |ci-badge| image:: https://github.com/openedx/blockstore/workflows/CI/badge.svg?branch=master
    :target: https://github.com/openedx/blockstore/actions
    :alt: Test suite status

.. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
    :alt: Maintained

.. |license-badge| image:: https://img.shields.io/github/license/openedx/blockstore.svg
    :target: https://github.com/openedx/blockstore/blob/master/LICENSE
    :alt: License

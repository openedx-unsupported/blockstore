==========
Blockstore
==========

Blockstore is a system for storing versioned, reusable educational content for Open edX.

It is designed as a replacement for `modulestore <https://github.com/openedx/edx-platform/tree/master/common/lib/xmodule/xmodule/modulestore>`_. It is meant to be a lower-level service than the modulestore, and is designed around the concept of storing small, reusable pieces of content, rather than large, fixed content structures such as courses. For Open edX, Blockstore is designed to facilitate a much greater level of content re-use than is currently possible, enable new adaptive learning features, and enable delivery of learning content in new ways (not just large traditional courses).

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

Blockstore is currently implemented as an independently deployed application (IDA), and is used to power `Content Libraries v2 <https://github.com/openedx/frontend-app-library-authoring#readme>`_ as well as `LabXchange <https://www.labxchange.org/>`_.

Blockstore is **not** included by default in a standard installation of Open edX or Open edX devstack. However, we are currently (April 2022) `moving blockstore into edx-platform <decisions/0002-app-not-service.rst>`_ - see https://github.com/openedx/edx-platform/pull/29779 for the current status of that work.

--------------
Design Details
--------------

See `DESIGN <DESIGN.rst>`_ for an overview of Blockstore's design as it exists today. See `"Blockstore Design" <https://openedx.atlassian.net/wiki/spaces/AC/pages/737149430/Blockstore+Design>`_ on the wiki for historical context.


--------------------------
Using with Docker Devstack
--------------------------

Prerequisite: Have your Open edX `Devstack <https://github.com/openedx/devstack>`_ properly installed and working. Your devstack must be tracking the ``master`` branch of ``edx-platform``; using Blockstore on an older devstack release is not supported.

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

-------------
Running Tests
-------------

Unit Tests
----------

To run the unit tests, get into the blockstore container:

.. code::

  make blockstore-shell


And then run:

.. code::

  make test

To save on overhead while running individual tests, from within the container, you can do:


.. code::

  DJANGO_SETTINGS_MODULE=blockstore.settings.test ./manage.py test dotted.path.To.test


Running Integration Tests
-------------------------

Open edX includes some integration tests for Blockstore, but they don't run by default. To run them, first start an isolated test version of blockstore by running ``make testserver`` from the ``blockstore`` repo root directory on your host computer. Then, from ``make dev.shell.studio``, run these commands:

.. code::

   EDXAPP_RUN_BLOCKSTORE_TESTS=1 python -Wd -m pytest --ds=cms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/
   EDXAPP_RUN_BLOCKSTORE_TESTS=1 python -Wd -m pytest --ds=lms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/

To run these integration tests while using Elasticsearch, add ``EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1`` on the above commands:

.. code::

   EDXAPP_RUN_BLOCKSTORE_TESTS=1 EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1 python -Wd -m pytest --ds=cms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/
   EDXAPP_RUN_BLOCKSTORE_TESTS=1 EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1 python -Wd -m pytest --ds=lms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/

To run these integration tests while using a specific container's version of Elasticsearch, add ``EDXAPP_TEST_ELASTICSEARCH_HOST`` with a specific container name on the above commands:

.. code::

   EDXAPP_RUN_BLOCKSTORE_TESTS=1 EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1 EDXAPP_TEST_ELASTICSEARCH_HOST=edx.devstack.elasticsearch710 python -Wd -m pytest --ds=cms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/
   EDXAPP_RUN_BLOCKSTORE_TESTS=1 EDXAPP_ENABLE_ELASTICSEARCH_FOR_TESTS=1 EDXAPP_TEST_ELASTICSEARCH_HOST=edx.devstack.elasticsearch710 python -Wd -m pytest --ds=lms.envs.test openedx/core/lib/blockstore_api/ openedx/core/djangolib/tests/test_blockstore_cache.py openedx/core/djangoapps/content_libraries/tests/

-------------------
Using in Production
-------------------

You can deploy blockstore in production using the `blockstore ansible role <https://github.com/openedx/configuration/tree/master/playbooks/roles/blockstore>`_.

Here is an example of setting the ansible variables to deploy Blockstore, assuming you are using the ``openedx_native.yml`` playbook. You will need to create the S3 bucket first (or comment out that part), and of course change all the variables and secret values to reflect your Open edX deployment details. Whatever value you put for ``BLOCKSTORE_API_AUTH_TOKEN`` must also be entered into the Blockstore django admin at e.g. https://blockstore.openedx-example.com/admin/authtoken/token/

.. code::

   # Run blockstore, and expose it publicly at 'blockstore.openedx-example.com'
   SANDBOX_ENABLE_BLOCKSTORE: true
   BLOCKSTORE_NGINX_HOSTNAME: 'blockstore.*'
   BLOCKSTORE_NGINX_PORT: 80
   BLOCKSTORE_SSL_NGINX_PORT: 443
   BLOCKSTORE_SECRET_KEY: secretvalue2here
   BLOCKSTORE_DATABASE_HOST: mysql.openedx-example.com
   BLOCKSTORE_DATABASE_USER: blockstore_user
   BLOCKSTORE_DATABASE_PASSWORD: secretvalue3here
   BLOCKSTORE_DEFAULT_DB_NAME: my_openedx_blockstore

   # Use S3 for blockstore data (optional but recommended):
   BLOCKSTORE_SERVICE_CONFIG_OVERRIDES:
       DEFAULT_FILE_STORAGE: storages.backends.s3boto3.S3Boto3Storage
       AWS_ACCESS_KEY_ID: AKIAWABCDEFGHIJKLMNOPQRS
       AWS_SECRET_ACCESS_KEY: secretvalue4here
       AWS_STORAGE_BUCKET_NAME: blockstore-bucket

   # Configure LMS/Studio to access Blockstore:
   EDXAPP_BLOCKSTORE_API_URL: http://localhost:8250/api/v1/
   EDXAPP_LMS_ENV_EXTRA:
       BLOCKSTORE_API_AUTH_TOKEN: secretvalue1here
   EDXAPP_CMS_ENV_EXTRA:
       BLOCKSTORE_API_AUTH_TOKEN: secretvalue1here

--------
Get Help
--------

Ask questions and discuss this project on `Slack <https://openedx.slack.com/messages/general/>`_ or the `Open edX Community Discussion Forum <https://discuss.openedx.org/>`_.

-------
License
-------

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. Please see the LICENSE_ file for details.

.. _LICENSE: https://github.com/openedx/blockstore/blob/master/LICENSE

-----------------
How To Contribute
-----------------

Contributions are welcome. Please read `How To Contribute <https://github.com/openedx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details. Even though it was written with ``edx-platform`` in mind, these guidelines should be followed for Open edX code in general.

-------------------------
Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

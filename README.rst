==========
Blockstore
==========

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

------------------------------------------------
Using with Content Libraries on a Tutor Devstack
------------------------------------------------

The easiest way to try out the "Content Libraries v2" feature along with Blockstore is to use the Tutor devstack and
`this library-authoring MFE Tutor plugin <https://github.com/openedx/frontend-app-library-authoring/pull/50>`_. See that plugin's README for details.


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

Change Log
----------

..
   All enhancements and patches to blockstore will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~

*

[1.1.0] - 2021-10-25
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Move apps/api to apps/rest_api.
* Copy edx-platform/openedx/core/lib/blockstore_api to blockstore/apps/api.
  This code has been copied over so it is easier to review the Python API
  implementation in development.
* Make code into an installable package.

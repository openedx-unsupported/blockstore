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

* Removed custom datetime parser in favor of ``datetime.fromisoformat`` which is more robust.

[1.4.0] - 2023-08-07
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_______

* Added support for Django 4.2


[1.3.1] - 2023-03-06
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Changed
_______

* Adds migration file that was missing from v1.3.0.


[1.3.0] - 2023-02-06
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Adds support for installing this package as a wheel (``pip install openedx-blockstore``) rather than having to use editable mode (``pip install -e ./blockstore``).

Changed
_______

* Fixes a bug where a new bundle's collection could not be set via Django admin.
* Various configuration and build tooling fixes. See commit log of 1.2.0...1.3.0 for full details.



[1.2.0] - 2021-01-25
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Adds API unit tests to improve test coverage.

Changed
_______

* Updates the Python API to use the models directly.

[1.1.0] - 2021-10-25
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Move apps/api to apps/rest_api.
* Copy edx-platform/openedx/core/lib/blockstore_api to blockstore/apps/api.
  This code has been copied over so it is easier to review the Python API
  implementation in development.
* Make code into an installable package.


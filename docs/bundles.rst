Bundles
=========================

The Blockstore does not parse or process files other than ``bundle.json``.
However, some conventions should be followed by authoring clients for interoperability:

* Files in a Bundle can be organized freely by authoring clients, including in directories.
* A **bundle.json** file must be added to the root of the Bundle by authoring clients. This file specifies the
  shareable components, bundle dependencies, assets and other metadata. See below for details.
* OLX files must use the **.olx** extension. Files with a different extension may be ignored or not treated as
  OLX by plugins and other clients. Files of any other type should not use this extension.

File URIs
-------------------------

Files can be referenced with Absolute URI as specified in section 4.3 of
`RFC 3986 <http://www.ietf.org/rfc/rfc3986.txt>`_. The scheme for file URIs is **bundle**.

XBlock Runtimes are expected to provide a service which allows reading a file given a URI or for converting a URI into
an internet accessible URL that can be passed to client applications.

.. code-block::

  file = blockstore_service.open(path_of_file_1)

  url_1 = blockstore_service.url_for_path(path_of_directory_1)
  url_2 = blockstore_service.url_for_path(path_of_file_2)

For directories or files in the same Bundle as the XBlock, the URI must be of the form:

.. code-block::

  scheme ":" <path from root of Bundle>

Examples:

.. code-block::

  bundle:/bundle.json
  bundle:/mcqs/mcq1.olx
  bundle:/b/c/icon.png
  bundle:/d/README
  bundle:/e/f/

For directories or files in other Bundles, the URI must be of the form:

.. code-block::

  scheme ":" "//" <Bundle alias> <path from root of Bundle>

Examples:

.. code-block::

  bundle://problems/description.olx
  bundle://problems/mcqs/mcq1.olx
  bundle://problems/images/
  bundle://problems/resources/intro.pdf
  bundle://videos_lectures/vid/lecture1.olx

If relative-path references are used in files, XBlocks will be responsible for prepending the URI of the relevant
base directory when necessary.

bundle.json
-------------------------
The bundle.json file contains metadata about the Bundle. Authoring clients must add and update this themselves.
It can contain the following fields:

schema
~~~~~~~~~~~~~~~~~~~~~~

The **schema** field is required and specifies the document format version.

.. code-block::

  "schema": 0.1

type
~~~~~~~~~~~~~~~~~~~~~~

The **type** field is required and should specify the type of content in the Bundle. Its value must be one of:

- olx/collection
- olx/course
- olx/sequence
- olx/unit
- static

.. code-block::

    "type": "olx/collection"

components
~~~~~~~~~~~~~~~~~~~~~~

The optional **components** field is an array of absolute paths to OLX files for XBlocks in the Bundle the author wants
available for use independently. These may be shown in previews of the Bundle so that authors can select them
for use.

.. code-block::

    "components": [
      "/description.olx",
      "/mcqs/mcq1.olx",
      "/mcqs/mcq2.olx",
      "/mcqs/mcq3.olx"
    ]

It is valid to not specify **components**. This may be useful in cases like having a shared Bundle with
branding assets only.

assets
~~~~~~~~~~~~~~~~~~~~~~

The optional **assets** field is an array of absolute paths to directories and files in the Bundle which
should be internet accessible from client applications via URLs.

.. code-block::

  "assets": [
    "/images",
    "/resources/intro.pdf"
  ]

dependencies
~~~~~~~~~~~~~~~~~~~~~~

The optional **dependencies** field is a map of aliases to bundle version info objects. The later must have
two fields: **bundle_uuid** and **version_num**.

If a file from another Bundle is to be referenced, a version of that Bundle must be specified in this field.
URIs to directories or files in other Bundles use the alias as the authority.

.. code-block::

  "dependencies": {
    "problems": {
      "bundle_uuid": "159f55e4-8cb0-46b1-a866-e967e632c5af",
      "version_num": 8,
    },
    "videos_lectures": {
      "bundle_uuid": "53766bd7-0fc1-400b-911b-85cd98b271a4",
      "version_num": 12
    }
  }

Bundles
=========================

The Blockstore does not parse or process files other than ``bundle.json``.
However, some conventions should be followed by authoring clients for interoperability:

* Files in a Bundle can be organized freely by authoring clients, including in directories.
* OLX files must use the **.olx** extension. Files with a different extension may be ignored or not treated as
  OLX by plugins and other clients. Files of any other type should not use this extension.
* The path to an OLX file may be used as a component of the XBlock ID. Therefore moving an OLX file or changing its
  name will be equivalent to deleting the XBlock and creating a new one.
* A **bundle.json** file must be added to the root of the Bundle by authoring clients. This file specifies the
  shareable components, bundle dependencies, assets and other metadata. See below for details.

Paths
-------------------------

Files can be referenced with paths which are relative references as specified in section 4.2 of
`RFC 3986 <http://www.ietf.org/rfc/rfc3986.txt>`_.

XBlock Runtimes are expected to provide a service which allows reading a file given a URI or for converting a URI into
an internet accessible URL that can be passed to client applications.

.. code-block::

  file = blockstore_service.open(path_of_file_1)

  url_1 = blockstore_service.url_for_path(path_of_directory_1)
  url_2 = blockstore_service.url_for_path(path_of_file_2)

For directories or files in the same Bundle as the XBlock, the URI must be an absolute-path reference
which consists of a single slash character followed by the full path of the directory or file from the root
of the Bundle.

.. code-block::

  /bundle.json
  /mcqs/mcq1.olx
  /b/c/icon.png
  /d/README
  /e/f/

For files in other Bundles, the URI must be a network-path reference which begins with two slash characters followed
by the alias of the relevant Bundle version as specified in ``bundle.json`` followed by a single slash character
and full path of the directory or file from the root of that Bundle.

.. code-block::

  //problems/description.olx
  //problems/mcqs/mcq1.olx
  //problems/images/
  //problems/resources/intro.pdf
  //videos_lectures/vid/lecture1.olx

If relative-path references are used in files, XBlocks will be responsible for prepending the URI of the relevant
base directory when necessary.

bundle.json
-------------------------
The bundle.json file contains metadata about the Bundle. Authoring clients must add and update this themselves.
It can contain the following fields:

meta
~~~~~~~~~~~~~~~~~~~~~~

The **meta** field is required and specifies the document format version.

.. code-block::

  "meta": {
    "version": 1
  },

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

  "assets": {
    "/images",
    "/resources/intro.pdf"
  }

dependencies
~~~~~~~~~~~~~~~~~~~~~~

The optional **dependencies** field is a map of aliases to bundle version info objects. The later must have
two fields: **bundle_uuid** and **version_num**.

If a file from another Bundle is to be referenced, a version of that Bundle must be specified in this field
because cross-Bundle URIs use the alias as the authority.

.. code-block::

  "dependencies": {
    "problems": {
      "bundle_uuid": "21d45e735e134c41ae3b24fde26d4369",
      "version_num": 8,
    },
    "videos_lectures": {
      "bundle_uuid": "b97c9907ecd54f4eb5f4c7eb51dd58e3",
      "version_num": 12
    }
  }

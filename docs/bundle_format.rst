Bundle Format
================

The Blockstore does not parse or validate most files itself. However, some conventions must be followed by clients
to allow interoperability between environments:

* There are no constraints on how the files in a Bundle can be organized.
* OLX files must use the **.olx** extension. Files with a different extension may be ignored or not treated as
  OLX by plugins and clients.
* A bundle.json file must be added by authoring clients which specifies the shareable components, bundle
  dependencies and assets. See below for details.
* Every XBlock element in an OLX file must have an **id** attribute. The value of this attribute will be used
  to construct the **block_key**. In a single Bundle, all ids must be unique. Blockstore will not validate ids however.
* Nested XBlocks in separate OLX files can be referenced by adding a **path** attribute to the element which points
  to the relevant OLX file. Blockstore does not parse or validate any paths itself. However plugins may do so.
* XBlock Runtimes should provide a service which can be used to read a file given a **path** or to get a
  public URL for it (if it is specified in assets field). XBlocks will be responsible for replacing paths
  in any assets and resources they are using with URLs.

Paths
-------------------------

Paths are URIs of the form **[//bundle_version_alias]path**.

bundle.json
-------------------------
The bundle.json file contains metadata about the Bundle. Authoring clients must add and update this themselves.
It contains the following fields:

meta
~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

  "meta": {
    "version": 1
  },


main_component
~~~~~~~~~~~~~~~~~~~~~~

The optional **main_component** field can be used to specify the file path to an XBlock which is the primary XBlock
of the Bundle that authors should use.

.. code-block::

    "main_component": "/unit1.olx"

components
~~~~~~~~~~~~~~~~~~~~~~

The optional **components** field can be used to specify file paths for XBlocks in the Bundle the author wants
available for use independently. They may be shown in previews of the Bundle so that authors can select them but
will have lower priority than the XBlock specified in **main_component**.

.. code-block::

    "components": {
      "/video_teaser.olx",
      "/mcqs/mcq1.olx",
      "/mcqs/mcq2.olx",
      "/mcqs/mcq3.olx"
    }

It is valid to not specify **main_component** and **components**. This may be useful in some cases like having a
shared Bundle with branding assets only.

dependencies
~~~~~~~~~~~~~~~~~~~~~~

The optional **dependencies** field is a dictionary of **bundle_version_alias: bundle_version** pairs. If a file from
another Bundle is to be referenced, a version of that Bundle must be specified in this field.

.. code-block::

  "dependencies": {
    "a": 21d45e735e134c41ae3b24fde26d4369@8,
    "b": b97c9907ecd54f4eb5f4c7eb51dd58e3@2
  }

The XBlock Runtime will provide a service which allows reading files from Bundles.

.. code-block::

  file = blockstore_service.open(path_of_file)

assets
~~~~~~~~~~~~~~~~~~~~~~

The optional **assets** field is an array of paths to directories and files in the Bundle which should be accessible
from client applications via URLs.

.. code-block::

  "assets": {
    "/images",
    "/resources/intro.pdf"
  }

The XBlock Runtime will provide a service which allows converting paths into absolute URLs that can be passed to
client applications. Paths can also be to assets contained in any of the **dependencies**.

.. code-block::

  url = blockstore_service.url_for_path(path_of_file)

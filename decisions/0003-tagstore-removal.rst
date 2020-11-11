Status
======

Accepted


Context
=======

During the initial development of Blockstore for the LabXchange project, a tagging service called tagstore was developed to allow tagging XBlock content stored in Blockstore.

However, the current approach of having XBlock content in bundles and tags in the database has at least two limitations:

1. Changes to tags are applied immediately and do not support the draft-publish workflow.
2. For course export-import workflows, a mechanism will need to be developed to include the tags data in the bundle anyway.

For architectural simplicitiy and to meet rapidly evolving product needs a custom tagging system was added to the LabXchange backend instead of trying to make tagstore cover a wide range of use cases.

Decision
========

Tagstore code will be removed from the blockstore repo. If Studio or other services need the ability to tag XBlock or other content a tagging system appropriate for the product needs can be developed.


Consequences
============

Since the tagstore is not being used there are no changes needed anywhere else.

Background
==========

* `Open edX Tagging Service Proposal <https://openedx.atlassian.net/wiki/spaces/AC/pages/791937307/Open+edX+Tagging+Service+Proposal>`_

==============
Design Details
==============

This section will describe the Blockstore design as it actually exists today. See `Blockstore Design <https://openedx.atlassian.net/wiki/spaces/AC/pages/737149430/Blockstore+Design>`_ on the wiki for historical context.

----------
Motivation
----------

Modulestore doesn't support dynamic content
-------------------------------------------

At its heart, edx-platform's current modulestore works with large, static course structures. Various dynamic courseware features such as A/B tests, cohorts, and randomized problem banks work around this by including every piece of content that might be displayed to any user and then selectively showing a subset of that using permission access checks. When you use a randomized problem bank in a sequence, the system is in fact copying the entire content library into that sequence.

This poses a number of problems:

* It creates very large data structures, degrading courseware performance. Many common courseware interactions noticeably slow down as the amount of content in a course increases.
* The underlying structure is static, so the ordering of elements is fixed, making adaptive learning sequences extremely cumbersome to implement. Course teams have heroically worked around this using LTI hacks, using Open edX as both an LTI provider and consumer in chained LTI launches (sequences with one unit that acts as an LTI consumer to an adaptive engine interface that then becomes an LTI consumer for individual problems in the original course).
* Course content is largely duplicated for every run, making it cumbersome to manage across multiple runs, especially if those runs are on different instances of Open edX as is the case with some partners.
* Trying to work around these limitations and maintain performance has significantly complicated the codebase and slowed feature development. Content Libraries (v1) are far less powerful than they were intended to be because of the large infrastructure changes that would have been required to execute the original vision.

Modulestore is highly coupled
-----------------------------

The modulestore codebase has evolved over time and is highly coupled to the "XModule runtime", and also still contains a lot of code related to distinguishing between "descriptors" and "modules", even though the newer XBlock API doesn't use those concepts at all. As a result of this coupling, it is difficult to modify the modulestore code to implement any new functionality.


---------------
Responsbilities
---------------

In scope:
---------

Blockstore is responsible for storing **learning objects** (like XBlocks), their associated **asset files** (images, PDFs, videos).

Blockstore learning objects are **versioned** and Blockstore includes a **draft-publish** workflow for making changes to a given object and/or its asset files.

Out of scope:
-------------

Blockstore is very much a low-level learning object store, and it doesn't actually understand OLX, XBlocks, or nuances of any of the files that it stores. They're just versioned files that it makes available to the LMS or other API consumers.

Blockstore does not:

* Know about courses, libraries, or other "learning contexts"
* Understand OLX or XBlocks
* Contain an XBlock runtime
* Enforce detailed permissions (Instead, the application consuming the Blockstore API, i.e. the LMS, should define its own access control rules and can give out signed links that allow only authorized users to download content files directly from Blockstore)
* Store learner "state" like what answer was selected or a learner's grade.

Implications
------------

Because of what's in scope and out of scope for Blockstore as described above, Blockstore itself is generally not used directly by end users. Instead, applications like the LMS or Studio interact with Blockstore and use it much like a database or object storage layer. Those applications are responsble for things like authentication, validation, implementing specific types of content (how is an XBlock represented in Blockstore? how is a content library represented in Blockstore?), etc.


--------------------
Content Libraries v2
--------------------

So far, the only major feature in Open edX that has been implemented using Blockstore is **Content Libraries v2** (also called "Complex Libraries").

Trying out Content Libraries v2
-------------------------------

To use or test Content Libraries v2, you need to set up Blockstore, and you'll also want to use the `Library Authoring micro-frontend <frontend-app-library-authoring>`_, which provides an optional user interface for creating content libraries and XBlocks in Blockstore. Follow the instructions in the Library Authoring micro-frontend README for details.

Keys and Identifiers
--------------------

Every Content Library (v2) is uniquely identified by a `LibraryLocatorV2 <https://github.com/openedx/opaque-keys/blob/5d730556ccdb6e9d7263a94399b9a0897755ac58/opaque_keys/edx/locator.py#L1495>`_ identifier. As a string (e.g. when used in URLs), these identifiers look like ``lib:MITx:reallyhardproblems`` where ``MITx`` is the organization that created the library, and ``reallyhardproblems`` is unique name for that particular content library.

Every XBlock in a Content Library (v2) is uniquely identified by a `LibraryUsageLocatorV2 <https://github.com/openedx/opaque-keys/blob/5d730556ccdb6e9d7263a94399b9a0897755ac58/opaque_keys/edx/locator.py#L1561>`_. As a string (e.g. when used in URLs), these identifiers look like ``lb:MITx:reallyhardproblems:problem:problem1`` where "lb" stands for "library block", the first two parts are the same as the corresponding parts of the library identifier, the third part (``problem``) specifies the type of the XBlock, and the fourth part is a unique name/identifier for that particular XBlock in that library.

Learner Interaction with XBlocks in Content Libraries v2
--------------------------------------------------------

There are two ways for users to see and interact with an XBlock that's in a content library (v2). First of all, the XBlock can be copied into a course using `LibrarySourcedBlock <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/common/lib/xmodule/xmodule/library_sourced_block.py#L28-L38>`_. In that case, once the copying is done, the XBlock is stored in modulestore, and works just like any other XBlock in a course. However, there are also two ways in which users can interact with XBlocks "directly" in the library:

* When authors are creating/editing XBlocks in a content library (v2), they can see and interact with the XBlocks.
* Each Content Library `can be configured to allow "public learning" <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/content_libraries/models.py#L104-L114>`_. When enabled, learners can then see XBlocks in the library and learn from them "directly", without any course involved. Such direct learning will remember the learner's answers (the XBlock state) and even issue a grade for each individual piece of content. However, the platform has no UI nor features to facilitate this type of direct learning. It is mostly used to build advanced use cases with custom user interfaces, such as LabXchange.

Learning Context Plugin
-----------------------

We define a "Learning Context" as "a course, a library, a program, or some other collection of content where learning happens." So each content library (v1 or v2) is a learning context.

For Blockstore-based learning contexts, there is `a plugin API to provide a learning context <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/learning_context/learning_context.py#L7-L16>`_. So naturally, Content Libraries v2 `implements this API to register Content Libraries (v2) as a Learning Context <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/content_libraries/library_context.py#L21-L27>`_.

Because of this learning context plugin, the generic XBlock APIs in `openedx/core/djangoapps/xblock/api.py <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/xblock/api.py>`_ and `openedx/core/djangoapps/xblock/rest_api/ <https://github.com/openedx/edx-platform/tree/master/openedx/core/djangoapps/xblock/rest_api>`_ will work correctly with content libraries and can be used to load and render XBlocks from content libraries.

For example, to display the HTML for an XBlock that's in a content library, you could write some code like this using the generic XBlock APIs::

    from opaque_keys.edx.keys import UsageKey
    from openedx.core.djangoapps.xblock.api import load_block

    block_id = UsageKey.from_string("lb:org:lib:problem:prob23")
    block = load_block(block_id)

    return block.render("student_view")    

What happens is:

* `Based on the usage key specified <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/learning_context/manager.py#L38-L39>`_, the platform will get the learning context key, ``lib:org:lib``.
* The ``LearningContextPluginManager`` will search for a registered learning context plugin that is associated with the ``lib`` key namespace.
* In edx-platform's ``setup.py``, `openedx.core.djangoapps.content_libraries.library_context:LibraryContextImpl is registered as the learning context plugin for that namespace <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/setup.py#L135>`_.
* Then the Content Library v2 plugin's `can_view_block <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/content_libraries/library_context.py#L54-L75>`_ function `will be called <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/api.py#L81-L86>`_ to check if the XBlock exists and if the user is allowed to view that XBlock.
* Next, an instance of `BlockstoreXBlockRuntime <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/runtime/blockstore_runtime.py#L28>`_ is `instantiated for the current user <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/api.py#L93>`_.
* In order to load the XBlock, ``BlockstoreXBlockRuntime`` needs to convert the given "usage key" to a "definition key". In general, the OLX data that represents one specific XBlock is the "definition", and everywhere that same XBlock is used (perhaps in several courses and libraries) is a "usage". Or you can think of each usage key like a hard link on a filesystem, and the definition key as the inode that points to the underlying data. So the runtime `will call <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/runtime/blockstore_runtime.py#L45>`_ the Content Library v2 plugin's `definition_for_usage <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/content_libraries/library_context.py#L77-L96>`_ function to convert the "usage key" into a ``BundleDefinitionLocator``.

  - ``BundleDefinitionLocator`` is a low level data structure that specified how to load the XBlock from Blockstore. Specifically, it contains the UUID of a Blockstore bundle that holds the OLX data as well as the path to the OLX file within the bundle (see "Bundle Conventions" below).
* Finally, now that the runtime has the exact bundle UUID and OLX file path from the learning context, it can `load and parse the OLX for that XBlock <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/runtime/blockstore_runtime.py#L58-L80>`_ and instantiate the XBlock in memory.

  - `BlockstoreFieldData <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/xblock/runtime/blockstore_field_data.py#L76-L88>`_ is responsible for implementing the "XBlock field API" so that the XBlock code can access the data that was parsed from its OLX file, via the usual XBlock APIs.
* The XBlock's ``render()`` method works in exactly the same way as for any XBlock in any runtime, by reading field data and returning an HTML fragment.

Bundle Conventions
------------------

Blockstore groups files into versioned "bundles", which are identified only by their UUID.

So every content library is associated with one Blockstore "bundle". The `ContentLibrary <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/content_libraries/models.py#L81>`_ django model / database table is used to track the association between content library IDs (e.g. `lib:Hogwarts:potions-problems`) and bundle UUIDs.

Within a content library bundle, every XBlock is represented as an OLX file with the file path::

    {block_type}/{usage_id}/definition.xml

This is `defined in definition_for_usage() <https://github.com/openedx/edx-platform/blob/7dc60db1d9832ae9382e08d2a686626995010338/openedx/core/djangoapps/content_libraries/library_bundle.py#L127>`_ in ``library_bundle.py``.

For example, the usage key ``lb:MITx:reallyhardproblems:problem:problem1`` would be part of the library ``lib:MITx:reallyhardproblems`` and within that library's Blockstore bundle could be found at ``problem/problem1/definition.xml``.

Each XBlock can have other data files associated with it, for example images. Any other files in the same "folder" (e.g. ``problem/problem1``) are considered to be "owned" by that XBlock. The Library Authoring micro-frontend will allow authors to see all the files "owned" by a particular XBlock, and in the OLX, references such as ``/static/img.png`` will be loaded from Blockstore as ``problem/problem1/img.png``. (The convention from modulestore of using ``/static/`` as a prefix to identify static assets belonging to the same course has been re-used to identify assets belonging to an XBlock.)

Draft Publish
-------------

Blockstore supports a draft-publish workflow. In general the Content Libraries APIs and XBlock APIs in the platform will behave differently whether used in the LMS or in Studio. In Studio, they will load from the draft version of the library/bundle by default, and in the LMS they will load from the published version by default.

That means that if you create an XBlock in a content library using Studio APIs, but do not publish the library's changes, you will get a 404 error when trying to use the LMS APIs to view the XBlock. You need to publish the library changes first, and then it will work.

XBlock Includes
---------------

For OLX in Blockstore specifically, a new mechanism has been introduced for specifying child XBlocks. Specifically, another XBlock from the same content library can be included using this syntax::

    <xblock-include definition="html/html1" />

Where ``html`` refers to the type of the child XBlock and ``html1`` is the ID. This corresponds to an OLX file in the bundle at ``html/html1/definition.xml``.

XBlocks in other bundles can be referenced if a Blockstore "link" is created to the other bundle. This is an advanced use case and currently has limited support. Once the link has been created, the OLX syntax for including a child XBlock from the linked bundle is::

    <xblock-include source="linked_bundle" definition="unit/unit1" usage="alias1" />

In the cae of including a child XBlock from another bundle, it is necessary to specify a usage ID for the included XBlock, as its definition ID may not be unique in the new bundle where it is being used.

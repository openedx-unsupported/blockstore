==================
Bundle Granularity
==================

-------
Context
-------

Blockstore provides Bundles, which can be treated as file directories with
versioned content. This provides a lot of flexibility, but we still need to
determine what sets of conventions (and what extra functionality) we require to
model our courses with OLX data.

One late change to our overall philosophical outlook was to radically separate
the human readable format used in import/export from the machine-readable format
that provides organization and reuse capability in Blockstore itself. This
implies shifting more of the higher level OLX -> Blockstore mapping knowledge
to be outside of Blockstore itself, and gives us opportunities to make some
simplifications.

---------------------------------------------------
Proposal: OLX Bundles with Flat Directory Structure
---------------------------------------------------

In this proposal, a Bundle for any chunk of OLX content has top-level folders
for every definition in the Bundle, including both leaf and container nodes. A
problem in a problem bank may have just one such directory for the problem
itself, or a few directories representing a Unit and multiple leaf nodes. A
course may potentially have thousands of directories.

The major focus of this approach is operational simplicity at scale. It is
generally less featureful than other proposals and shifts more of the work to
OLX-aware clients.

An important mental shift is that this walks back from some of the file system
analogies of the original proposal. We still have files in Bundles, and XBlock
content is still stored in directories with their associated static assets. But
when we make data references across XBlocks, it's by identifiers and conventions
and not by relative file paths. It's the job of clients to transform that into
a more friendly file-path based format for the human readable format.

XBlock Directories
==================

XBlock Directories are a client convention and not a core Blockstore primitive.
Each directory represents a single XBlock and its associated assets. The naming
scheme is::

    /{block-type}/{definition-id}/
                                  definition.xml
                                  static/

The ``static`` directory is optional. For a concrete example::

    /problem/blockstore_granularity/
                                    definition.xml
                                    static/
                                           diagram.png

Meanwhile, a container looks like::

    /unit/blockstore_big_questions/definition.xml

When containers reference their children, it's done via a new tag. So a
particular ``unit.xml`` might look like::

    <unit display_name="">
        <!-- Normal usage -->
        <xblock-include definition="unit/blockstore_big_questions" />

        <!-- If we want to include the same content with a modifier to the usage
             key so that we can include it multiple times with different state
             storage. -->
        <xblock-include definition="unit/blockstore_big_questions" usage="alternate" />

        <!-- XBlock that exists in a Linked Bundle aliased to "arch_hangout_videos" -->
        <xblock-include source="arch_hangout_videos" definition="video/blockstore_overview" />
    </unit>

When referencing an XBlock definition from a linked bundle, the linked bundle
must follow the OLX Bundle conventions, but may be any type of OLX bundle:
course, library, or other future types.

The ``usage="..."`` attribute on an ``<xblock-include />`` directive in an
XBlock definition file is considered a hint that will be used by the learning
context (the course, library, web page, etc.) to build a "usage key" for the
XBlock against which user state is stored. Exactly how the ``usage="..."`` hint
is ultimately used to construct the key depends on the learning context. For
example, an HTML block included with ``<xblock-include ... usage="bob" />`` in a
library might have a usage key like ``lb:lib1:html:bob`` when accessed directly
in the library, but may have a usage key like
``block:SchoolX+course1+run:html:parent3-bob6734`` when included in a course.
This helps with separation of concerns (bundles store definitions, which are
OLX files; learning contexts deal with usages which are specific instantiations
of a definition) and preserves flexibility for future learning context types.

In particular, note that a learning context will almost always transform the
usage keys of any children of an included block, in order to ensure they are
unique. Consider this case::

    <unit display_name="Example">
        <!-- A unit in an external problem bank library, containing 3 problems -->
        <xblock-include source="prob_bank5" definition="unit/3problems" usage="first_set" />
        <!-- A second usage of the same problem bank -->
        <xblock-include source="prob_bank5" definition="unit/3problems" usage="second_set" />
    </unit>

In this example, if the included ``3problems`` unit contains child includes
like::

    <xblock-include definition="problem/problem1" usage="p1" />
    ...

Then in the original example, the usage ID ``p1`` would not be unique, because
its parent unit is included twice. So the learning context will have to prefix
the usage hint ``p1`` in this case, producing unique usage keys like
``first_set-p1`` for the first usage and ``second_set-p1`` for the second.

---------------------------------
Proposal: Content Library Bundles
---------------------------------

A content library bundle is an OLX bundle with additional constraints, that is
used to represent the OLX data of a content library.

As with OLX Bundles in general, the conventions defined here are not implemented
nor enforced by Blockstore in any way, however they are documented here for the
sake of having a central reference.

A content library bundle is an OLX bundle that holds a collection of one or more
XBlocks. Each XBlock definition (OLX ``definition.xml`` file) in the content
library is either a "top-level block" or is a child of exactly one other XBlock
definition in the same bundle. A content library bundle does not allow a single
definition to have multiple different usages (multiple <xblock-include />
elements referencing the same definition). However, an XBlock definitions from
any other linked OLX bundle, such as another content library, may be used
multiple times::

    <unit display_name="">
        <!-- Normal usage of a definition in the same library bundle -->
        <xblock-include definition="problem/problem1" />

        <!-- The following is not allowed in a content library because each
        definition in a content library may only be used once:
        <xblock-include definition="problem/problem1" usage="other-usage" />
        -->

        <!-- However, XBlock definitions from linked bundles may be used freely -->
        <xblock-include source="linked_problem_bank" definition="problem/problemB" usage="probB" />
        <xblock-include source="linked_problem_bank" definition="problem/problemB" usage="probB-alt" />
    </unit>

In a content library bundle, the ``usage="..."`` attribute must not be specified
when including an XBlock definition from the same bundle, but must be specified
when including an XBlock definition from a linked bundle. This makes the
implementation of content libraries considerably simpler.

------------------------
Proposal: Course Bundles
------------------------

The format of course bundles has not yet been finalized but will likely be
an OLX bundle that includes some sort of additional "outline" file, such as
``course-outline.json`` which specifies how the various XBlock definitions it
contains or links to are related to each other in a hierarchical course tree.

----------------------------------------
General Blockstore/Bundle Considerations
----------------------------------------

Links
=====

Link information is stored at the Snapshot level. Since the human-readable
format is going to be a transform, we don't have to make symlink analogies to
make the data easier to work with in authoring. Instead, Links are a mapping of
names to Bundle Versions::

    {
        "links": {
            "arch_hangout_videos": {
                "direct": {
                    "bundle_uuid": "3fcf5f61-bc23-41ec-9452-26d12dc3b13c",
                    "version": 20,
                    "snapshot_digest": "617608446daa448c94a09fd7ae70bf67ef4efc94"
                },
                "indirect": []
            }
        }
    }

Since all Snapshots capture their full dependencies, they can do cycle detection
quickly. Since Links are explicitly named, we can keep multiple references to
different versions of the same Bundle, which might be useful for things like
shared code libraries.

The notifications aspect of Bundles would be handled by a M:M mapping of Bundles
(not BundleVersions), with a relationship of ``(lending_bundle, borrowing_bundle,
still_using)``, where ``still_using`` is a boolean flag that is true if the most
recent version of the borrowing Bundle still has a link to any version of the
lending bundle.

Changeset-Level Metadata
========================

Data about who changed what and why are stored at the BundleVersion level of
granularity. This does mean that a Changelog for a Course would cover many
different blocks, and that finding when a particular block changed would be
more difficult. However, it gives a good high level view of the history of the
work as a whole (the Course) in a simple way. In the Content Library case, each
problem would be its own Bundle, so we'd still have tracking at the individual
problem level.

OLX-Aware Metadata
==================

Data about the OLX contents of a Bundle (e.g. tagging, search indexing) would
need to be associated to the tuple of (BundleVersion, XBlock Directory). Asset
association also happens at this level of granularity.

Publishing Transactions
=======================

When updating a course, a new Snapshot would be created by a Draft, with all the
changes for any given set of XBlocks. Once the Snapshot successfully completes,
a new BundleVersion of the Course would be created to point to that Snapshot. An
interruption in the publishing process during Snapshot creation could result in
an orphaned Snapshot that's not pointed to by a BundleVersion, but shouldn't
result in a broken or inconsistent state.

Hierarchy Representation
========================

The list of XBlock content is represented as a flat set of directories, and all
navigational hierarchy has to be interpreted by OLX-aware clients. A student's
path through a course is an LMS/Compositor level concern that structural OLX is
an input to, and the storage layer of Blockstore shouldn't need to model it.

Reusing Containers
==================

To re-use a Unit, you would first make a Link to the Bundle where that Unit came
from, and then specify the Link name in the ``source`` attribute::

    <xblock-include source="arch_hangout_videos" definition="video/blockstore_overview"/>

This allows for arbitrary reuse at varying levels of granularity.

Intentionality and Tracking Re-use
==================================

A drawback of approach is that it requires more explicit intentionality in
course design in order for its BundleVersion dependency tracking to be
meaningful. You could borrow a single leaf block or container block from another
Course, but Blockstore itself would only know that the link between the
BundleVersions existed, not the specific items that were used. This problem is
significantly lessened in the case of Content Libraries where each problem has
its own Bundle (but many content libraries will have more than one problem).

Another way to look at it is that Blockstore's tracking of reuse is for
update notifications, dependency checking, and licensing enforcement. Finer
granularity measurements are better done by something more OLX-aware. For
instance, if I'm making a CCX that uses a sequence but I hide a Unit that isn't
relevant to my students, should that count towards my reuse of that particular
unit? If someone Links to an entire Unit, but really they just wanted to make
a reference to one image in one leaf of that Unit, is it Blockstore's job to
understand the references well enough to understand that?

If we start with this kind of tracking being at the core of Blockstore's data
model, then OLX awareness and coupling will slowly work its way into the system.

Performance
===========

Storing containers in a granular way makes certain kinds of concurrent
operations simpler, like Drafts independently publishing Units and Chapters.
However it does make lookups slower for tree traversal, and collection of data
from many different blocks at once.

Some outlier queries we should be able to accommodate:

* Some courses have nearly 100 sequentials total, all of which must be
represented in the current Studio Outline view.
* While the median Unit has three children, outliers have been known to have
400+ children.

(Still need to fill this out)

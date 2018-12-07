================
Bundle Granularity
================

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

    /{definition-key}/
                     {tag-type}.xml
                     static/

The ``static`` directory is optional. For a concrete example::

    /problem+blockstore_granularity/
                                    problem.xml
                                    static/
                                           diagram.png

Meanwhile, a container looks like:

    /unit+blockstore_big_questions/problem.xml

When containers reference their children, it's done via a new tag. So a
particular ``unit.xml`` might look like::

    <unit display_name="">
        <!-- Normal usage -->
        <xblock-include definition="unit+blockstore_big_questions" />

        <!-- If we want to include the same content with a modifier to the usage
             key so that we can include it multiple times with different state
             storage. -->
        <xblock-include definition="unit+blockstore_big_questions" usage="alternate" />

        <!-- XBlock that exists in a Linked Bundle aliased to "arch_hangout_vidoes" -->
        <xblock-include definition="arch_hangout_videos/video+blockstore_overview"/>
    </unit>

Links
=====

Link information is stored at the Snapshot level. Since the human-readable
format is going to be a transform, we don't have to make symlink analogies to
make the data easier to work with in authoring. Instead, Links are a mapping of
names to Bundle Snapshots::

    {
        "links": {
            "arch_hangout_videos": {
                "bundle_uuid": "3fcf5f61-bc23-41ec-9452-26d12dc3b13c",
                "snapshot": "8f7bc6e89581591fa925fefa3819d382fd793839"
                "dependencies": [
                    {
                        "bundle_uuid": "fd7ee4b3-0540-406c-98b9-dd050b7ddcb2",
                        "snapshot": "c0c0940e4b3151908b60cecd1ef5e2aa19904676"
                    }
                ]
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
result in a broken or inconsitent state.

Hierarchy Representation
========================

The list of XBlock content is represented as a flat set of directories, and all
navigational hierarchy has to be interpreted by OLX-aware clients. A student's
path through a course is an LMS/Compositor level concern that structural OLX is
an input to, and the storage layer of Blockstore shouldn't need to model it.

Reusing Containers
==================

To re-use a Unit, you would first make a Link to the Bundle where that Unit came
from, and then specify the Link prefix before the directory where the Unit comes
from::

    <xblock-include definition="arch_hangout_videos/video+blockstore_overview"/>

This allows for arbitrary reuse at varying levels of granularity.

Intentionality and Tracking Re-use
==================================

A drawback of approach is that it requires more explicit intentionality in
course design in order for its BundleVersion dependency tracking to be
meaningful. You could borrow a single leaf block or container block from another
Course, but Blockstore itself would only know that the link between the
BundleVersions existed, not the specific items that were used. This problem is
significantly lessened in the case of Content Libraries, since each problem has
its own Bundle there.

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

=======================================
Open edX Courseware Data Migration Plan
=======================================

-------
Context
-------




------------------
Guiding Principles
------------------

At a high level, there are two extreme paths we can follow with this upgrade.
The first is to use Blockstore as an opportunity to rebuild significant parts of
the Open edX platform, to maximize the potential value this new data store can
provide us. The second is to focus exclusively on replicating existing
functionality first, so that the transition can happen as quickly as possible,
even if signficant pieces of that work will get thrown away later.

The approach outlined here takes a middle road, with the goal of building a more
powerful Studio authoring experience while minimizing the necessary upfront
changes to the LMS. Some high level principles:

1. Everything currently authored in Modulestore or Contentstore will be moved to
Blockstore eventually.
2. The transition must be gradual and we will be running in a mixed environment
for some time.
3. Developing powerful and flexible authoring is a higher priority than
improving LMS storage.

------------
Target State
------------

Once this plan is executed, the proposed end state is:

1. Everything from Modulestore and Contentstore is moved to Blockstore on the
authoring side.
2. The LMS continues to use Modulestore to serve courseware.
3. The LMS points to static assets controlled by Blockstore.
4. Content Libraries exist as a special case of a more general (and more
powerful) authoring mechanism.
5. The publish step explicitly pushes data from Blockstore into the Split
Modulestore.

This would get us to a place where we could get much of the search and reuse
use cases for Blockstore on the authoring side, without having to boil the
ocean to rework the existing Modulestore for serving courseware to students.
It would also allow us to separately evolve the LMS's read-optimized data store
from Blockstore's read/write use cases, as well as any other read-optimized
stores and applications as the system evolves to more dynamic use cases.

Note that this is the target state where we can declare that all content
authoring has been migrated to Blockstore. This is not the end state of the
system as a whole, and the number of places Blockstore publishes to would likely
increase to support things like adaptive learning use cases.

----------------------------------------------
Paving the Runway: Necessary Open edX Upgrades
----------------------------------------------

Open edX has layers of cruft that would significantly complicate moving to
Blockstore. In many cases, this is technical debt that we've been meaning to
address for years, but have been unable to prioritize for one reason or another.
Blockstore reaches into the core of our courseware storage and delivery, forcing
us to address some of these issues:

XBlock Conversion
=================

Some of the most critical content types in Open edX have never been converted to
XModules. The proxying magic used to glue together the XModule and XBlock APIs
is complex and confusing, and there are completely redundant APIs for things
like static asset serving. It is significantly easier to create a new XBlock
runtime that supports Blockstore for its persistence layer if we don't have to
carry over XModule compatibility.

While all XModules need to be converted in time, two useful groupings are:

1. XModules already in Content Libraries: Video, HTML, Capa Problems. These are
the most commonly used XModules in the system. Video and Capa represent the two
hardest XModules to port over, given their size and complexity.
2. Container types: Chapter, Sequence. These may be ported to be XBlocks, but
may also evolve into a different API altogether.
3. Everything else. There is a long tail of XModules that are much smaller and
less frequently used: LibraryContent, Poll, Randomize, WordCloud, etc.


Old Mongo Retirement
====================

The newer Split Mongo Modulestore has existed since the Birch release, but
because course content retirement is not well defined, there are installs out
there that still use Old Mongo courses. An Old Mongo course has a course ID that
looks like "Org/CourseName/Run", as opposed to Split's course ID format of
"course-v1:Org+CourseName+Run".

While we recommend deleting Old Mongo courses if possible, we will offer a
conversion management command that will convert Old Mongo courses to Split while
maintaining the IDs (and thus student state). A proof of concept of that work is
at: https://github.com/edx/edx-platform/pull/17393

Converted courses can still be edited in Studio, but Blockstore will only
publish to the Split Modulestore. (TODO: Clarify this.)


---------------------
Phases and Milestones
---------------------


Milestone 1: Content Libraries
==============================

Content Libraries as they exist in Open edX today have a few features that make
them easy to separate and port:

1. They have very simple structures, being a simple list of blocks.
2. Only a few XBlock types are supported: Video, Capa, and HTML.
3. Their contents are completely copied into the Course sequences that use them
at the time of publishing.

The first milestone is would deliver:

* A parallel implementation of Content Libraries.
* A mechanism to convert an existing Modulestore-backed Content Library to be
Blockstore-backed.

It would be useful to see this as a starting point


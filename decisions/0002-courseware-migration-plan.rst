=======================================
Open edX Courseware Data Migration Plan
=======================================

-------
Context
-------

Please note that this migration proposal is at a very early stage of iteration
and no portion of it has yet been accepted.


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
4. Content Libraries will become a more general concept, and the Content Library
of today will be recast as a type of Content Library, like "Problem Bank". With
the idea that additional, pluggable types will follow.
5. The publish step explicitly pushes data from Blockstore into the Split
Modulestore.

This would get us to a place where we could lay the foundation for a more
powerful (search/tagging/reuse) authoring experience, without having to boil the
ocean to rework the existing Modulestore for serving courseware to students.
It would also allow us to separately evolve the LMS's read-optimized data store
from Blockstore's read/write use cases, as well as any other read-optimized
stores and applications as the system evolves to more dynamic use cases.

Note that this is the target state where we can declare that all content
authoring has been migrated to Blockstore. This is not the end state of the
system as a whole, and the number of places Blockstore publishes to would likely
increase to support things like adaptive learning use cases.

----------------
Release Timeline
----------------

This is a high level summary of the release timeline, with more details about
each piece in the sections that follow. The goal is to always give a transition
release cycle for backwards compatibility, and to provide new Blockstore-powered
capabilities with each release.

Juniper
=======

* Old Mongo: Management command to convert Old Mongo courses to Split.
* XBlock Conversion: Video, HTML, and Capa XModules are converted to XBlock.
* Content Libraries: Mixed operation where existing Content Libraries are
supported with a conversion management command. Converted Content Libraries
(Problem Banks) will have a new authoring experience making them easier to
search and manage. Early iteration of a pluggable mechanism for supporting
different Content Library types.

Koa
===

* Old Mongo: Old Mongo entirely removed (requires updating many tests).
* XBlock Conversion: All remaining XModules are converted to XBlock. Remove
XModule proxying.
* Content Libraries: Only allow Blockstore backed Content Libraries. Add a new
Content Library type that can be used with larger sections of reusable, but
still static content. Public release of plugin mechanism.
* Courses: Introduction of Blockstore-backed Courses and a conversion management
command.

Lilac
=====

* Courses: Only allow Blockstore backed Courses. Modulestore for LMS becomes
read-only except for the import mechanism. Move videos to Blockstore and retire
edx-val.
* More dynamic composition of content for students, requiring storage changes
on the LMS.

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

The release timeline would look like:

* Juniper: Old Mongo and Split Mongo both work. A management command is provided
to do in-place conversion of courses from Old Mongo to Split Mongo.
* Koa: Only Split Mongo is supported.

Converted courses can still be edited in Studio, but Blockstore will only
publish to the Split Modulestore. (TODO: Clarify this.)

Publish Step Consolidation
==========================

The ``course_published`` signal (and other course lifecycle signals) are
currently handled inconsistently thoughtout the system, with some tasks
executing on Studio workers and some on LMS workers. This works at the moment,
because the Studio and LMS storage for course content is the same. That will
break when we start shifting things to Blockstore, and we'll want to firmly
draw the distinction that ``course_published`` processing needs to happen in the
LMS.


----------
Milestones
----------

Milestone 1: Content Libraries
==============================

Target Release: Juniper

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

-------------------------------
API Boundaries and Plugabbility
-------------------------------



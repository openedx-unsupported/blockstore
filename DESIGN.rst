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

==========
Tagstore
==========

Tagstore was a system for storing hierarchical tags associated with content.

It was partially developed and then deprecated. This folder only exists to hold
the data migrations that are required to delete old tagstore data from any
installations which may have previously installed it.

----------
Background
----------

Tagstore could tag any kind of content whatsoever, as long as the content has a
stable ID. Since XBlocks have stable usage IDs, Tagstore could be used to tag
XBlocks. It was intended to work with Blockstore, so the focus was on tagging
XBlocks that are stored within Blockstore, but it was extremely generic
(essentially tags use what Django calls a "Generic Foreign Key"), so it could be
used to tag users, content in external systems, XBlocks, or anything else.

The first version of Tagstore used Neo4j to store tags, but the latest version
used MySQL, just like any other Django app.

Tagstore provided a REST API for tagging entities (things) of any type, and it
supported a hierarchical taxonomy, so for example if you tag something as being
a "black bear" but then ask Tagstore to list all entities tagged with any
"Mammal" tag, it will return that thing because it knows that all black bears
are mammals. That hierarchical taxonomy functionality was the main "feature" of
Tagstore, and the rest of it is very straightforward.

Later we realized that you can easily get essentially the same functionality
from ElasticSearch, if you just store tags as a field on your content and index
all of your content metadata (including tags) into ElasticSearch in the
appropriate format, then ElasticSearch can provide the same hierarchical search
functionality. At that point, we discontinued development of Tagstore.

-----------------------------------------
Similar functionality using ElasticSearch
-----------------------------------------

When you are defining the ElasticSearch document that will index your XBlocks,
use a field like this for the tags::

    tags = Keyword(multi=True)

Now, let's say your tag hierarchy looks like this:

- Mammal

  - Black bear
  - Human
  - Elephant

Now say you are indexing a particular XBlock that is about black bears, so it is
tagged with the tag "Black bear". So even though this XBlock only has one
associated tag (Black bear), when you generate the tags field of your
ElasticSearch index document, you actually want to store two tag strings:

- Mammal
- Mammal/Black bear

Then on the frontend, to do a search for all items tagged "Mammal" OR any
sub-tag of Mammal, you simply do an exact match for ``tags=Mammal`` and it will
correctly find the XBlock about black bears, even though the block was only
tagged with "Black bear" and not Mammal. Likewise, if the user wants to find
XBlocks tagged with Black bear, you do an exact match for
``tags=Mammal/Black bear`` and you'll find all such XBlocks.

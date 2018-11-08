Tagstore
========

Tagstore is a system for tagging entities. For example, a common use case would be applying difficulty tags like "easy", "medium", or "hard" to XBlocks (learnable content components) that are stored in Blockstore.

Tagstore holds collections of tags called Taxonomies. The simplest taxonomy is a set of tags; the set {"easy", "medium", "hard"} is an example of a taxonomy for content difficulty levels. The tags in a taxonomy can optionally be hierarchical, so that they exist in a tree with parent-child relationships (e.g. all dogs are mammals, all mammals are animals). This is designed to support learning outcome hierarchies in particular.

Tagstore is part of Blockstore but has been designed to be easily separable should the need arise.

Features
--------

* Python 3 API with type hints
* Allows any "entity" to be tagged, where an entity could be a user, a block, a collection, etc.
* Allows rich searching for entities by tags. e.g. "Find all large animals" will return an entity that was tagged with "large" and "dog", since it knows that the "dog" tag is a type of "animal" tag.
* Designed to support multiple tag storage backends, although the current version of Tagstore only includes a Django ORM backend, which stores tags in MySQL/PostgeSQL/SQLite. (A reasonably complete Neo4j backend implementation also existed in an early version and can found at https://github.com/open-craft/blockstore/commit/714b22f8456fb3b509aca54f59dc96de060d36fe)

Non-features
------------

* Does not allow any tag to be in two different places in the same taxonomy (i.e. a tag cannot have two parents, nor can the same child tag appear in two different places in the hierarchy)
* Does not allow other types of relationships between tags other than organizing them into a hierarchy (no support for arbitrary relationships like "dog is similar to wolf"; such advanced graph relationships - which enable other types of taxonomies and fuzzy searches - could be added later but would mean we can't use SQL backends)
* Does not implement "private tags" (user A applies tag T to entity E, but only user A sees that tag). However, applications that use Tagstore may add an authorization/permissions layer to allow for private or hidden taxonomies.
* Does not allow manipulating tag hierarchies once they are created, other than by adding new tags to the tree. i.e. you cannot remove tags from a hierarchy, nor change their position in the tree etc. We assume that hierarchical tags will usually be created via import/export of externally developed taxonomies.

API Example
-----------

Here is an example of using the Tagstore API::

    from tagstore.backends.django import DjangoTagstore
    from tagstore.models import EntityId
    tagstore = DjangoTagstore()

    # Create a biology taxonomy:
    biology = tagstore.create_taxonomy("Biology", owner_id=None)
    plant = biology.add_tag('plant')
    conifer = biology.add_tag('conifer', parent_tag=plant)
    cypress = biology.add_tag('cypress', parent_tag=conifer)
    pine = biology.add_tag('pine', parent_tag=conifer)
    aster = biology.add_tag('aster', parent_tag=plant)

    # Print tag hierarchy tree:
    depths = {}
    for (tag, parent) in biology.list_tags_hierarchically():
        depths[tag] = depths[parent] + 1 if parent else 0
        print(("  " * depths[tag]) + tag.name)
    # The resulting hierarchy that gets printed out is:
    #   plant
    #     aster
    #     conifer
    #       cypress
    #       pine

    # Create a "sizes" taxonomy:
    sizes = tagstore.create_taxonomy("sizes", owner_id=None)
    small = sizes.add_tag('small')
    med = sizes.add_tag('med')
    large = sizes.add_tag('large')

    # Tag some entities:
    dandelion = EntityId(entity_type='thing', external_id='dandelion')
    tagstore.add_tag_to(small, dandelion)
    tagstore.add_tag_to(aster, dandelion)
    redwood = EntityId(entity_type='thing', external_id='redwood')
    tagstore.add_tag_to(large, redwood)
    tagstore.add_tag_to(cypress, redwood)

    # Find all asters
    set(tagstore.get_entities_tagged_with(aster))
    # result: {dandelion}

    # plants
    set(tagstore.get_entities_tagged_with(plant))
    # result: {dandelion, redwood}

    # small plants
    set(tagstore.get_entities_tagged_with_all({plant, small}))
    # result: {dandelion}

    # plants, with no tag inheritance
    set(tagstore.get_entities_tagged_with(plant, include_child_tags=False))
    # result: set()

    # conifers
    set(tagstore.get_entities_tagged_with(conifer))
    # result: {redwood}

    # plants starting with "d"
    set(tagstore.get_entities_tagged_with(
        plant, entity_types=['thing'], external_id_prefix='d'
    ))
    # result: {dandelion}


Future Features
---------------

* REST API?

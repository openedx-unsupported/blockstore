"""
Methods for searching Tagstore
"""
from typing import Iterator, List, Optional, Set, Union

from django.db.models import Q, Subquery

from .models import EntityId, Entity, TagId, Tag


# Searching Tags ###############################################################


def get_tags_applied_to(*entity_ids: EntityId) -> Set[TagId]:
    """ Get the set of unique tags applied to any of the specified entity IDs """
    entity_filter = Q()
    for eid in entity_ids:
        q = Q(entity_type=eid.entity_type) & Q(external_id=eid.external_id)
        entity_filter = entity_filter | q
    entities = Entity.objects.filter(entity_filter)
    tags = Tag.objects.filter(entity___id__in=Subquery(entities.values('_id')))
    return set(tag.id for tag in tags)

# Searching Entities ###########################################################


def get_entities_tagged_with(tag: Union[Tag, TagId], **kwargs) -> Iterator[EntityId]:
    """
    Get an iterator over all entities that have been tagged with the given tag.

    Also accepts the same filtering keyword arguments as
    get_entities_tagged_with_all()
    """
    for entity_id in get_entities_tagged_with_all({tag}, **kwargs):
        yield entity_id


def get_entities_tagged_with_all(
    tags: Set[Union[Tag, TagId]],
    entity_types: Optional[List[str]] = None,
    external_id_prefix: Optional[str] = None,
    entity_ids: Optional[List[EntityId]] = None,  # use this to filter a list of entity IDs by tag
    include_child_tags=True,  # For hierarchical taxonomies, include child tags
                              # (e.g. search for "Animal" will return results tagged only with "Dog")
) -> Iterator[EntityId]:
    """
    Method for searching/filtering for entities that have all the specified tags
    and match all of the specified conditions
    """
    if not tags:
        raise ValueError("tags must contain at least one Tag")

    entities = Entity.objects.all()  # We start with the all() queryset, and filter it down.

    if include_child_tags:
        # Convert the set of tags to a set of materialized paths:
        tags_filter = Q()
        for tag in tags:
            tags_filter = tags_filter | (Q(taxonomy_id=tag.taxonomy_id) & Q(name=tag.name))
        paths = Tag.objects.filter(tags_filter).values_list('path', flat=True)
        for path in paths:
            entities = entities.filter(tags__path__startswith=path)
    else:
        for tag in tags:
            entities = entities.filter(tags__taxonomy_id=tag.taxonomy_id, tags__name=tag.name)

    if entity_types is not None:
        entities = entities.filter(entity_type__in=entity_types)

    if external_id_prefix is not None:
        entities = entities.filter(external_id__startswith=external_id_prefix)

    if entity_ids is not None:
        addl_filter = Q()
        for eid in entity_ids:
            addl_filter = addl_filter | (Q(entity_type=eid.entity_type) & Q(external_id=eid.external_id))
        entities = entities.filter(addl_filter)

    for e in entities:
        yield e.id

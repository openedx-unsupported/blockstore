"""
Django ORM tag storage backend.
"""
from typing import Iterator, List, Optional, Set, Tuple
from django.db.models import Q, Subquery

from .tagstore_django.models import Entity as EntityModel, Tag as TagModel, Taxonomy as TaxonomyModel

from .. import Tagstore
from ..models import EntityId, Tag, TaxonomyId, Taxonomy, UserId


class DjangoTagstore(Tagstore):
    """
    Django tag storage backend.
    """

    def create_taxonomy(self, name: str, owner_id: Optional[UserId] = None) -> Taxonomy:
        """ Create a new taxonomy with the specified name and owner. """
        owner_obj: Optional[UserId] = None
        if owner_id is not None:
            (owner_obj, _created) = EntityModel.objects.get_or_create(
                entity_type=owner_id.entity_type,
                external_id=owner_id.external_id,
            )
        obj = TaxonomyModel.objects.create(name=name, owner=owner_obj)
        return Taxonomy(uid=obj.id, name=name, owner_id=owner_id, tagstore=self)

    def get_taxonomy(self, taxonomy_uid: TaxonomyId) -> Optional[Taxonomy]:
        try:
            tax = TaxonomyModel.objects.get(pk=taxonomy_uid)
        except TaxonomyModel.DoesNotExist:
            return None
        return tax.as_tuple(self)

    def _add_tag_to_taxonomy(self, taxonomy_uid: TaxonomyId, name: str, parent_tag: Optional[str] = None) -> str:
        if parent_tag:
            # Check the parent tag:
            try:
                pt = TagModel.objects.get(taxonomy_id=taxonomy_uid, name=parent_tag)
            except TagModel.DoesNotExist:
                raise ValueError("Invalid parent tag.")
            path = TagModel.make_path(taxonomy_uid, name, pt.path)
        else:
            path = TagModel.make_path(taxonomy_uid, name)
        db_tag, created = TagModel.objects.get_or_create(
            taxonomy_id=taxonomy_uid,
            name=name,
            defaults={'path': path},
        )
        if not created:
            if db_tag.path != path:
                raise ValueError("That tag already exists with a different parent tag.")
        return db_tag.name

    def get_tag_in_taxonomy(self, name: str, taxonomy_uid: TaxonomyId) -> Optional[Tag]:
        """
        If a tag with the specified name (case insensitive) exists in this taxonomy, get it.

        Otherwise returns None.
        """
        try:
            tag_obj = TagModel.objects.get(taxonomy_id=taxonomy_uid, name=name)
            return Tag(taxonomy_uid=taxonomy_uid, name=tag_obj.name)
        except TagModel.DoesNotExist:
            return None

    def list_tags_in_taxonomy(self, taxonomy_uid: TaxonomyId) -> Iterator[Tag]:
        for tag in TagModel.objects.filter(taxonomy_id=taxonomy_uid).order_by('name'):
            yield Tag(taxonomy_uid=taxonomy_uid, name=tag.name)

    def list_tags_in_taxonomy_hierarchically(self, taxonomy_uid: TaxonomyId) -> Iterator[Tuple[Tag, Tag]]:
        """
        Get a list of all tags in the given taxonomy, in hierarchical and alphabetical order.

        Returns tuples of (Tag, parent_tag) where parent_tag is the parent tag. This method
        guarantees that parent tags will be returned before their child tags.
        """
        for tag in TagModel.objects.filter(taxonomy_id=taxonomy_uid).order_by('path'):
            yield (Tag(taxonomy_uid=taxonomy_uid, name=tag.name), tag.parent_tag_tuple)

    def list_tags_in_taxonomy_hierarchically_as_dict(self, taxonomy_uid: TaxonomyId) -> dict:
        """
        Get all tags in the given taxonomy as a list of nested dictionaries.

        Returns a list in the form of [tag, tag, ...] where tag is a dictionary
        containing the name and id of a top level tag (it has no parent)
        and also a list holding all `children` of that tag recursively (can be empty).
        """
        tags: dict = {'children': []}
        stack = [tags]
        for tag in TagModel.objects.filter(taxonomy_id=taxonomy_uid).order_by('path'):
            parent = tag.parent_tag_tuple.name if tag.parent_tag_tuple else None
            node = {'name': tag.name, 'id': tag.id, 'children': []}
            if parent is None:
                del stack[1:]
                stack[0]['children'].append(node)
                stack.append(node)
            elif parent == stack[-1]['name']:
                stack[-1]['children'].append(node)
                stack.append(node)
            else:
                while parent != stack[-1]['name']:
                    stack.pop()
                stack[-1]['children'].append(node)
                stack.append(node)
        return tags

    def list_tags_in_taxonomy_containing(self, taxonomy_uid: TaxonomyId, text: str) -> Iterator[Tag]:
        for tag in TagModel.objects.filter(taxonomy_id=taxonomy_uid, name__icontains=text).order_by('name'):
            yield Tag(taxonomy_uid=taxonomy_uid, name=tag.name)

    # Tagging Entities ##########################

    def add_tag_to(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Add the specified tag to the specified entity/entities.

        Will be a no-op if the tag is already applied.
        """
        tag_model = TagModel.objects.get(taxonomy_id=tag.taxonomy_uid, name=tag.name)
        for entity in entity_ids:
            (em, _created) = EntityModel.objects.get_or_create(
                entity_type=entity.entity_type,
                external_id=entity.external_id,
            )
            em.tags.add(tag_model)

    def remove_tag_from(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Remove the specified tag from the specified entity/entities

        Will be a no-op if the entities do not have that tag.
        """
        tag = TagModel.objects.get(taxonomy_id=tag.taxonomy_uid, name=tag.name)
        # This could be optimized to a single DB query, but that's probably not necessary
        for eid in entity_ids:
            try:
                EntityModel.objects.get(entity_type=eid.entity_type, external_id=eid.external_id).tags.remove(tag)
            except EntityModel.DoesNotExist:
                pass

    def get_tags_applied_to(self, *entity_ids: EntityId) -> Set[Tag]:
        """ Get the set of unique tags applied to any of the specified entity IDs """
        entity_filter = Q()
        for eid in entity_ids:
            q = Q(entity_type=eid.entity_type) & Q(external_id=eid.external_id)
            entity_filter = entity_filter | q
        entities = EntityModel.objects.filter(entity_filter)
        tags = TagModel.objects.filter(entity__id__in=Subquery(entities.values('id')))
        tags_found = set()
        for tag in tags:
            tags_found.add(Tag(taxonomy_uid=tag.taxonomy_id, name=tag.name))
        return tags_found

    # Searching Entities ##########################

    def get_entities_tagged_with_all(
        self,
        tags: Set[Tag],
        entity_types: Optional[List[str]] = None,
        external_id_prefix: Optional[str] = None,
        entity_ids: Optional[List[EntityId]] = None,  # use this to filter a list of entity IDs by tag
        include_child_tags=True,  # For hierarchical taxonomies, include child tags
                                  # (e.g. search for "Animal" will return results tagged only with "Dog")
    ) -> Iterator[EntityId]:

        if not tags:
            raise ValueError("tags must contain at least one Tag")

        entities = EntityModel.objects.all()  # We start with the all() queryset, and filter it down.

        if include_child_tags:
            # Convert the set of tags to a set of materialized paths:
            tags_filter = Q()
            for tag in tags:
                tags_filter = tags_filter | (Q(taxonomy_id=tag.taxonomy_uid) & Q(name=tag.name))
            paths = TagModel.objects.filter(tags_filter).values_list('path', flat=True)
            for path in paths:
                entities = entities.filter(tags__path__startswith=path)
        else:
            for tag in tags:
                entities = entities.filter(tags__taxonomy_id=tag.taxonomy_uid, tags__name=tag.name)

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
            yield EntityId(entity_type=e.entity_type, external_id=e.external_id)

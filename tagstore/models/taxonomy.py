"""
A taxonomy is a collection of tags that can be applied to content.
"""
from typing import Iterator, NewType, Optional, Tuple, Union

from django.db import models

from .common import MAX_CHAR_FIELD_LENGTH
from .entity import Entity
from .tag import TagId, Tag


TaxonomyId = NewType('TaxonomyId', int)


class Taxonomy(models.Model):
    """
    A taxonomy is a collection of tags, some of which may be organized into
    a hierarchy.
    """
    id: TaxonomyId  # The type of the _instance_ 'id' variable is TaxonomyId
    id = models.BigAutoField(primary_key=True)  # the _class_ 'id' variable is a BigAutoField
    name = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH)
    # The object (user, group, collection, or even Taxonomy) that "owns" this
    # taxonomy. What this means is up to the system using Tagstore.
    # Be careful:
    # * owner.id is of type EntityId (tuple) and is the 'natural key' which
    #   should generally be used.
    # * owner_id is the internal database integer key.
    owner = models.ForeignKey(Entity, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'tagstore_taxonomy'
        verbose_name_plural = 'Taxonomies'

    def __str__(self) -> str:
        return self.name

    def add_tag(self, name: str, parent_tag: Optional[Union[Tag, TagId]] = None) -> Tag:
        """
        Add the specified tag to this given taxonomy, and return it.

        If a Tag already exists in the taxonomy with the given name (case-insensitive)
        and the given parent, then that Tag is returned and no changes are made.

        Will raise Tag.ValidationError if the name or parent is invalid.
        Will raise Tag.DoesNotExist if the specified parent doesn't exist.
        Will raise Tag.AlreadyExistsError if trying to add a child tag that
        already exists anywhere in the taxonomy.
        """
        if parent_tag is not None:
            if parent_tag.taxonomy_id != self.id:
                raise Tag.ValidationError("A tag cannot have a parent from another taxonomy")
            # Check the parent tag or raise Tag.DoesNotExist
            pt = self.tags.get(name=parent_tag.name)
            path = Tag.make_path(self.id, name, pt.path)
        else:
            path = Tag.make_path(self.id, name)

        tag, created = self.tags.get_or_create(
            name=name,
            defaults={
                "path": path,
                "taxonomy_is_saving": True,
            },
        )
        if not created and tag.path.lower() != path.lower():
            raise Tag.AlreadyExistsError("That tag already exists with a different parent tag.")
        # Note that the existing tag's name, if any, may differ in case from the provided name.
        return tag

    def get_tag(self, name: str) -> Optional[TagId]:
        """
        If a tag with the specified name (case insensitive) exists in this
        taxonomy, get its ID. Otherwise returns None.

        Use taxonomy.tags.get(name=name) or taxonomy.add_tag(name) if you want
        to get the actual Tag object instead of just the TagId.
        """
        try:
            return self.tags.get(name__iexact=name).id
        except Tag.DoesNotExist:
            return None

    def list_tags(self) -> Iterator[TagId]:
        """
        Get a (flattened) list of all tags in the given taxonomy, in alphabetical order.
        """
        for tag in self.tags.order_by('name'):
            yield tag.id

    def list_tags_hierarchically(self) -> Iterator[Tuple[TagId, TagId]]:
        """
        Get a list of all tags in the given taxonomy, in hierarchical and alphabetical order.

        Returns tuples of (Tag ID, parent tag ID).
        This method guarantees that parent tags will be returned before their child tags.
        """
        for tag in self.tags.order_by('path'):
            yield (tag.id, tag.parent_tag_id)

    def list_tags_containing(self, text: str) -> Iterator[TagId]:
        """
        Get a (flattened) list of all tags in the given taxonomy that contain the given string
        (case insensitive). This is intended to be used for auto-complete when users tag content
        by typing tags into a text field, for example.
        """
        for tag in self.tags.filter(name__icontains=text).order_by('name'):
            yield tag.id

    def get_tags_hierarchically_as_dict(self) -> dict:
        """
        Get all tags in the given taxonomy as nested dictionaries.

        Returns a dictionary. An example is {'children': [
            {'name': 'mammal', '_id': 57, 'children': [
                {'name': 'cow', '_id': 58, 'children': []}
            ]}
        ]}.

        The '_id' field should never be exposed outside of the Tagstore app.
        """
        root: dict = {'children': []}
        all_nodes: dict = {None: root}
        for tag in self.tags.order_by('path'):
            node = {'name': tag.name, '_id': tag.pk, 'children': []}
            all_nodes[tag.id] = node
            all_nodes[tag.parent_tag_id]['children'].append(node)
        return root

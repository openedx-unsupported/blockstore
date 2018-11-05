"""
A system for storing and retrieving tags related to Blockstore entities
"""

from typing import Iterator, List, Optional, Tuple, Union

from .models.entity import EntityId
from .models.tag import Tag, TagSet
from .models.taxonomy import TaxonomyId, TaxonomyMetadata
from .models.user import UserId


class Tagstore:
    """
    Python API to store and retrieve tags and taxonomies

    This class defines the API only, and the implementation is done
    by a backend subclass.
    """

    # Taxonomy CRUD ##########################

    def create_taxonomy(self, name: str, owner_id: UserId) -> TaxonomyMetadata:
        """ Create a new taxonomy with the specified name and owner. """
        raise NotImplementedError()

    def get_taxonomy(self, uid: int) -> TaxonomyMetadata:
        raise NotImplementedError()

    def add_tag_to_taxonomy(
        self, tag: str, taxonomy: Union[TaxonomyId, TaxonomyMetadata], parent_tag: Optional[Tag] = None
    ) -> Tag:
        """
        Add the specified tag to the given taxonomy

        Will be a no-op if the tag already exists in the taxonomy.
        Will raise a ValueError if the specified taxonomy or parent doesn't exist.
        Will raise a ValueError if trying to add a child tag that
        already exists anywhere in the taxonomy.
        """
        if not isinstance(tag, str) or len(tag) < 1:
            raise ValueError("Tag value must be a (non-empty) string.")

        if tag != tag.strip():
            raise ValueError("Tag cannot start or end with whitespace.")

        if any(char in tag for char in ':,;\n\r\\'):
            raise ValueError("Tag contains an invalid character.")

        if isinstance(taxonomy, TaxonomyMetadata):
            taxonomy_uid = taxonomy.uid
        else:
            taxonomy_uid = taxonomy

        if parent_tag is not None:
            if parent_tag.taxonomy_uid != taxonomy_uid:
                raise ValueError("A tag cannot have a parent from another taxonomy")
            parent_tag_str = parent_tag.tag
        else:
            parent_tag_str = None

        self._add_tag_to_taxonomy(taxonomy_uid=taxonomy_uid, tag=tag, parent_tag=parent_tag_str)
        return Tag(taxonomy_uid=taxonomy_uid, tag=tag)

    def _add_tag_to_taxonomy(self, taxonomy_uid: int, tag: str, parent_tag: Optional[str] = None) -> None:
        raise NotImplementedError()

    def list_tags_in_taxonomy(self, uid: int) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy, in alphabetical order.
        """
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

    def list_tags_in_taxonomy_hierarchically(self, uid: int) -> Iterator[Tuple[Tag, str]]:
        """
        Get a list of all tags in the given taxonomy, in hierarchical and alphabetical order.

        Returns tuples of (Tag, parent_tag) where parent_tag is the 'tag' string which uniquely
        identifies the parent tag. This method guarantees that parent tags will be returned
        before their child tags.
        """
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

    def list_tags_in_taxonomy_containing(self, uid: int, text: str) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy that contain the given string
        """
        # Subclasses can optionally override this method to provide a more efficient implementation.
        text = text.lower()
        for tag in self.list_tags_in_taxonomy(uid):
            if tag.tag.lower().find(text) != -1:
                yield tag

    # Tagging Entities ##########################

    def add_tag_to(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Add the specified tag to the specified entity/entities.

        Will be a no-op if the tag is already applied.
        """
        raise NotImplementedError()

    def remove_tag_from(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Remove the specified tag from the specified entity/entities

        Will be a no-op if the entities do not have that tag.
        """
        raise NotImplementedError()

    def get_tags_applied_to(self, *entity_ids: EntityId) -> TagSet:
        """ Get the set of unique tags applied to any of the specified entity IDs """
        raise NotImplementedError()

    # Searching Entities ##########################

    def get_entities_tagged_with(self, tag: Tag, **kwargs) -> Iterator[EntityId]:
        """
        Get an iterator over all entities that have been tagged with the given tag.

        Also accepts the same filtering keyword arguments as
        get_entities_tagged_with_all()
        """
        # Subclasses do not generally need to override this method.
        for entity_id in self.get_entities_tagged_with_all({tag}, **kwargs):
            yield entity_id

    def get_entities_tagged_with_all(
        self,
        tags: TagSet,
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
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

"""
A backend is a wrapper around a database that stores tags
"""
from typing import Iterator, List, Optional

from ..models import EntityId, Tag, TagSet, TaxonomyMetadata, UserId


class TagstoreBackend:
    """
    Abstract base class for a tag storage backend.
    """

    # Taxonomy CRUD ##########################

    def create_taxonomy(self, name: str, owner_id: UserId) -> TaxonomyMetadata:
        """ Create a new taxonomy with the specified name and owner. """
        raise NotImplementedError()

    def get_taxonomy(self, uid: int) -> TaxonomyMetadata:
        raise NotImplementedError()

    def add_tag_to_taxonomy(self, taxonomy_uid: int, tag: str, parent_tag: Optional[str] = None) -> None:
        """
        Add the specified tag to the given taxonomy

        Will be a no-op if the tag already exists in the taxonomy.
        Will raise a ValueError if the specified taxonomy or parent doesn't exist.
        Will raise a ValueError if trying to add a child tag that
        already exists anywhere in the taxonomy.
        """
        raise NotImplementedError()

    def add_tag_hierarchy_to_taxonomy(self, tag_hierarchy: None) -> None:
        """
        TBD
        """
        raise NotImplementedError()

    def list_tags_in_taxonomy(self, uid: int) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy, in alphabetical order.
        """
        raise NotImplementedError()

    def list_tags_in_taxonomy_containing(self, uid: int, text: str) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy that contain the given string
        """
        # OPTIONAL: Backends do not have to implement this, but it's recommended.
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

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

"""
A backend is a wrapper around a database that stores tags
"""
from typing import AsyncIterator, List, Optional

from ..models.entity import EntityId
from ..models.tag import Tag, TagSet
from ..models.user import UserId
from ..models.taxonomy import TaxonomyMetadata


class TagstoreBackend:
    """
    Abstract base class for a tag storage backend.
    """

    # Taxonomy CRUD ##########################

    async def create_taxonomy(self, name: str, owner_id: UserId) -> TaxonomyMetadata:
        """ Create a new taxonomy with the specified name and owner. """
        raise NotImplementedError()

    async def get_taxonomy(self, uid: int) -> TaxonomyMetadata:
        raise NotImplementedError()

    async def add_tag_to_taxonomy(self, tag: Tag) -> None:
        """
        Add the specified tag to the taxonomy it references

        Will be a no-op if the tag already exists in the taxonomy
        """
        raise NotImplementedError()

    async def add_tag_hierarchy_to_taxonomy(self, tag_hierarchy: None) -> None:
        """
        TBD
        """
        raise NotImplementedError()

    # Tagging Entities ##########################

    async def add_tag_to(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Add the specified tag to the specified entity/entities.

        Will be a no-op if the tag is already applied.
        """
        raise NotImplementedError()

    async def remove_tag_from(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Add the specified tag to the specified entity/entities

        Will be a no-op if the entities do not have that tag.
        """
        raise NotImplementedError()

    async def get_tags_applied_to(self, *entity_ids: EntityId) -> TagSet:
        """ Get the set of unique tags applied to any of the specified entity IDs """
        raise NotImplementedError()

    # Searching Entities ##########################

    async def get_entities_matching(
        self,
        entity_ids: Optional[List[EntityId]] = None,  # use this to filter a list of entity IDs by tag
        entity_id_prefix: Optional[str] = None,
        has_all_of: Optional[TagSet] = None,
        has_any_of: Optional[TagSet] = None,
        include_child_tags=True,  # For hiararchical taxonomies, include child tags
                                  # (e.g. search for "Animal" will return results tagged only with "Dog")
    ) -> AsyncIterator[EntityId]:
        """
        Method for searching/filtering for entities that match the specified conditions.
        """
        raise NotImplementedError()

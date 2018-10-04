"""
A system for storing and retrieving tags related to Blockstore entities

Backed by a graph database (a pluggable backend)
"""

from typing import AsyncIterator, Optional, Union

from .backends.backend import TagstoreBackend
from .models.entity import EntityId
from .models.tag import Tag, TagSet
from .models.taxonomy import TaxonomyId, TaxonomyMetadata
from .models.user import UserId


class Tagstore:
    """
    Python API to store and retrieve tags and taxonomies
    """

    def __init__(self, backend: TagstoreBackend) -> None:
        self.backend = backend

    async def create_taxonomy(self, name: str, owner_id: UserId) -> TaxonomyMetadata:
        return await self.backend.create_taxonomy(name, owner_id)

    async def get_taxonomy(self, uid: int) -> TaxonomyMetadata:
        return await self.backend.get_taxonomy(uid)

    async def add_tag_to_taxonomy(
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

        if any(char in tag for char in '/:,;\n\r\\'):
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

        await self.backend.add_tag_to_taxonomy(taxonomy_uid=taxonomy_uid, tag=tag, parent_tag=parent_tag_str)
        return Tag(taxonomy_uid=taxonomy_uid, tag=tag)

    async def list_tags_in_taxonomy(self, uid: int) -> AsyncIterator[Tag]:
        async for tag in self.backend.list_tags_in_taxonomy(uid):
            yield tag

    async def list_tags_in_taxonomy_containing(self, uid: int, text: str) -> AsyncIterator[Tag]:
        try:
            async for tag in self.backend.list_tags_in_taxonomy_containing(uid, text):
                yield tag
        except NotImplementedError:
            text = text.lower()
            async for tag in self.backend.list_tags_in_taxonomy(uid):
                if tag.tag.lower().find(text) != -1:
                    yield tag

    async def add_tag_to(self, tag: Tag, *entity_ids: EntityId) -> None:
        await self.backend.add_tag_to(tag, *entity_ids)

    async def remove_tag_from(self, tag: Tag, *entity_ids: EntityId) -> None:
        await self.backend.remove_tag_from(tag, *entity_ids)

    async def get_tags_applied_to(self, *entity_ids: EntityId) -> TagSet:
        return await self.backend.get_tags_applied_to(*entity_ids)

    async def get_entities_tagged_with(self, tag: Tag, **kwargs) -> AsyncIterator[EntityId]:
        async for entity_id in self.backend.get_entities_tagged_with_all({tag}, **kwargs):
            yield entity_id

    async def get_entities_tagged_with_all(self, tags: TagSet, **kwargs) -> AsyncIterator[EntityId]:
        async for entity_id in self.backend.get_entities_tagged_with_all(tags, **kwargs):
            yield entity_id

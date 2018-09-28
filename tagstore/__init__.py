"""
A system for storing and retrieving tags related to Blockstore entities

Backed by a graph database (a pluggable backend)
"""

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

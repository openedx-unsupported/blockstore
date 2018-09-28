"""
Neo4j tag storage backend.
"""
from typing import Dict
from .neo4j_async import Neo4j

from .backend import (
    TagstoreBackend,
    TaxonomyMetadata,
    UserId,
)


# pylint: disable=abstract-method
class Neo4jTagstoreBackend(TagstoreBackend):
    """
    Neo4j tag storage backend.
    """
    def __init__(self, config: Dict[str, str], loop):
        super().__init__()
        # Wrap the Neo4j driver in an asynchronous wrapper.
        # Note that the underlying library is not really async yet so this
        # only makes _reads_ asynchronous. Writes should use the normal driver
        # API directly.
        self.async_wrapper = Neo4j(config, loop)

    async def _create_unique_id(self, entity_type: str):
        """ Atomically create a unique integer ID for the given type of object """
        with self.async_wrapper.driver.session() as session:
            result = session.write_transaction(
                lambda tx: tx.run('''
                    MERGE (id:UniqueId{name: $entity_type })
                    ON CREATE SET id.count = 1
                    ON MATCH SET id.count = id.count + 1
                    RETURN id.count
                ''', entity_type=entity_type),
            )
            return result.single().value()

    async def create_taxonomy(self, name: str, owner_id: UserId) -> TaxonomyMetadata:
        """ Create a new taxonomy with the specified name and owner. """
        uid = await self._create_unique_id('Taxonomy')
        with self.async_wrapper.driver.session() as session:
            session.write_transaction(
                lambda tx: tx.run('''
                MERGE (u:User:TaggableEntity {type: 'user', externalId: $owner_id})
                MERGE (t:Taxonomy {uid: $uid, name: $name})-[:OWNEDBY]->(u)
                ''', uid=uid, name=name, owner_id=owner_id)
            )
        return TaxonomyMetadata(uid=uid, name=name, owner_id=owner_id)

    async def get_taxonomy(self, uid: int) -> TaxonomyMetadata:
        result = await self.async_wrapper.afetch_one('''
            MATCH (t:Taxonomy {uid: $uid})
            MATCH (t)-[:OWNEDBY]->(user)
            RETURN t, user
        ''', uid=uid)
        if result is None:
            return None
        taxonomy_node = result['t']
        return TaxonomyMetadata(
            uid=taxonomy_node.get('uid'),
            name=taxonomy_node.get('name'),
            owner_id=result['user'].get('externalId'),
        )

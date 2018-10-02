"""
Neo4j tag storage backend.
"""
from typing import AsyncIterator, Dict, List, Optional
from .neo4j_async import Neo4j

from .backend import (
    EntityId,
    Tag,
    TagSet,
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
        # only makes some parts of the query reading async, while the rest
        # is still blocking.
        self.async_wrapper = Neo4j(config, loop)

    async def _create_unique_id(self, entity_type: str):
        """ Atomically create a unique integer ID for the given type of object """
        return (await self.async_wrapper.afetch_one('''
            MERGE (id:UniqueId{name: $entity_type })
            ON CREATE SET id.count = 1
            ON MATCH SET id.count = id.count + 1
            RETURN id.count
        ''', entity_type=entity_type))['id.count']

    async def create_taxonomy(self, name: str, owner_id: UserId) -> TaxonomyMetadata:
        """ Create a new taxonomy with the specified name and owner. """
        uid = await self._create_unique_id('Taxonomy')
        await self.async_wrapper.aexec('''
            MERGE (u:User:TaggableEntity {type: 'user', externalId: $owner_id})
            MERGE (t:Taxonomy {uid: $uid, name: $name})-[:OWNEDBY]->(u)
        ''', uid=uid, name=name, owner_id=owner_id)
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

    async def add_tag_to_taxonomy(self, taxonomy_uid: int, tag: str, parent_tag: Optional[str] = None) -> None:
        if parent_tag is not None:
            # The MATCH WHERE NOT clause makes this a no-op if the taxonomy already contains
            # the specified tag, to avoid circular tag relationships.
            # We use CONTAINS for the taxonomy->tag relationships and INCLUDES
            # for the parent tag -> child tag relationships
            result = await self.async_wrapper.afetch_one('''
                MATCH (tx:Taxonomy {uid: $uid}) WHERE NOT (tx)-[:CONTAINS]->(:Tag {tag: $tag})
                MATCH (tx)-[:CONTAINS]->(parent:Tag {tag: $parent_tag})
                MERGE (tx)-[:CONTAINS]->(tag:Tag {tag: $tag})
                MERGE (parent)-[:INCLUDES]->(tag)
                RETURN tag
            ''', uid=taxonomy_uid, tag=tag, parent_tag=parent_tag)
            if result is None:
                raise ValueError(f"Invalid parent tag, or child tag already exists.")
        else:
            await self.async_wrapper.aexec('''
                MATCH (tx:Taxonomy {uid: $uid})
                MERGE (tx)-[:CONTAINS {}]->(tag:Tag {tag: $tag})
            ''', uid=taxonomy_uid, tag=tag)

    async def list_tags_in_taxonomy(self, uid: int) -> AsyncIterator[Tag]:
        async for result in self.async_wrapper.afetch('''
            MATCH (:Taxonomy {uid: $uid})-[:CONTAINS {}]->(tag:Tag)
            RETURN tag ORDER BY tag.tag
        ''', uid=uid):
            yield Tag(taxonomy_uid=uid, tag=result['tag'].get('tag'))

    async def list_tags_in_taxonomy_containing(self, uid: int, text: str) -> AsyncIterator[Tag]:
        async for result in self.async_wrapper.afetch('''
            MATCH (:Taxonomy {uid: $uid})-[:CONTAINS {}]->(tag:Tag) WHERE lower(tag.tag) contains lower($text)
            RETURN tag ORDER BY tag.tag
        ''', uid=uid, text=text):
            yield Tag(taxonomy_uid=uid, tag=result['tag'].get('tag'))

    # Tagging Entities ##########################

    async def add_tag_to(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Add the specified tag to the specified entity/entities.

        Will be a no-op if the tag is already applied or does not exist
        in the given taxonomy.
        """
        await self.async_wrapper.aexec('''
            MATCH (:Taxonomy {uid: $uid})-[:CONTAINS {}]->(tag:Tag {tag: $tag})
            UNWIND $entities AS entity_id
                MERGE (e:TaggableEntity {type: entity_id[0], externalId: entity_id[1]})
                MERGE (e)-[:TAGGEDWITH]->(tag)
        ''', uid=tag.taxonomy_uid, tag=tag.tag, entities=[[e.entity_type, e.external_id] for e in entity_ids])

    async def get_tags_applied_to(self, *entity_ids: EntityId) -> TagSet:
        """ Get the set of unique tags applied to any of the specified entity IDs """
        tags = set()
        async for result in self.async_wrapper.afetch('''
            MATCH (t:Taxonomy)-[:CONTAINS]->(tag:Tag)<-[:TAGGEDWITH]-(e:TaggableEntity)
            WHERE [e.type, e.externalId] IN $entities
            RETURN t, tag ORDER BY tag.tag
        ''', entities=[[e.entity_type, e.external_id] for e in entity_ids]):
            tags.add(Tag(taxonomy_uid=result['t']['uid'], tag=result['tag']['tag']))
        return tags

    # Searching Entities ##########################

    async def get_entities_tagged_with_all(
        self,
        tags: TagSet,
        entity_types: Optional[List[str]] = None,
        external_id_prefix: Optional[str] = None,
        entity_ids: Optional[List[EntityId]] = None,  # use this to filter a list of entity IDs by tag
        include_child_tags=True,  # For hierarchical taxonomies, include child tags
                                  # (e.g. search for "Animal" will return results tagged only with "Dog")
    ) -> AsyncIterator[EntityId]:

        if not tags:
            raise ValueError("tags must contain at least one Tag")

        tags = tags.copy()
        first_tag = tags.pop()
        kwargs = dict()

        def add_match_clause(tag: Tag):
            """ Generate a cypher MATCH clause to require the specified tag """
            uid_var = f'uid{add_match_clause.match_index}'
            tag_var = f'tag{add_match_clause.match_index}'
            kwargs[uid_var] = tag.taxonomy_uid
            kwargs[tag_var] = tag.tag
            add_match_clause.match_index += 1
            clause = f'\nMATCH (:Taxonomy {{uid: ${uid_var}}})-[:CONTAINS]->(:Tag {{tag: ${tag_var}}})'
            if include_child_tags:
                clause += f'-[:INCLUDES*0..99]->(:Tag)'
            clause += f'<-[:TAGGEDWITH]-(e:TaggableEntity)'
            return clause
        add_match_clause.match_index = 1

        cypher = add_match_clause(first_tag)

        conditions = []

        if entity_types is not None:
            conditions.append('e.type IN $etypes')
            kwargs['etypes'] = entity_types

        if external_id_prefix is not None:
            conditions.append('e.externalId STARTS WITH $ext_id_starts')
            kwargs['ext_id_starts'] = external_id_prefix

        if entity_ids is not None:
            conditions.append('[e.type, e.externalId] IN $entities')
            kwargs['entities'] = [[e.entity_type, e.external_id] for e in entity_ids]

        if conditions:
            cypher += '\nWHERE ' + ' AND '.join(map(lambda cond: '(' + cond + ')', conditions))

        for additional_tag in tags:
            cypher += add_match_clause(additional_tag)

        cypher += '\nRETURN e'

        async for result in self.async_wrapper.afetch(cypher, **kwargs):
            yield EntityId(entity_type=result['e']['type'], external_id=result['e']['externalId'])

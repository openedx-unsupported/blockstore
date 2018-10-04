"""
Tests for all included backends
"""
# pylint: disable=no-member, too-many-statements
import asyncio
from typing import Iterable

import asynctest

from .. import Tagstore, TagstoreBackend
from ..models import EntityId, TaxonomyMetadata
from .django import DjangoTagstoreBackend
from .neo4j import Neo4jTagstoreBackend


class AbstractBackendTest:
    """ Abstract test that tests any backend implementation """
    tagstore: Tagstore

    def get_backend(self) -> TagstoreBackend:
        raise NotImplementedError()

    def setUp(self):
        backend = self.get_backend()
        self.tagstore = Tagstore(backend)

    # Taxonomy CRUD

    async def test_create_taxonomy(self):
        """ Creating a taxonomy generates a unique integer ID """
        taxonomy1 = await self.tagstore.create_taxonomy("Taxonomy 1", owner_id=1)
        self.assertIsInstance(taxonomy1.uid, int)
        self.assertEqual(taxonomy1.name, "Taxonomy 1")
        self.assertEqual(taxonomy1.owner_id, 1)
        taxonomy2 = await self.tagstore.create_taxonomy("Taxonomy 2", owner_id=1)
        self.assertNotEqual(taxonomy1.uid, taxonomy2.uid)

    async def test_get_taxonomy(self):
        """ Retrieve a taxonomy's metadata """
        written = await self.tagstore.create_taxonomy("TestTax", owner_id=10)
        read = await self.tagstore.get_taxonomy(written.uid)
        self.assertEqual(written.uid, read.uid)
        self.assertEqual(written.name, read.name)
        self.assertEqual(written.owner_id, read.owner_id)

    async def test_get_taxonomy_nonexistent(self):
        """ get_taxonomy() must return None if the taxonomy ID is invalid """
        result = await self.tagstore.get_taxonomy(1e8)
        self.assertIsNone(result)

    async def test_add_tag_to_taxonomy(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy """
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        self.assertEqual(len([t async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]), 0)
        tag = await self.tagstore.add_tag_to_taxonomy('testing', tax)
        tags = [t async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], tag)

    async def test_case_sensitive_tags(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy """
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        self.assertEqual(len([t async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]), 0)
        tag1 = await self.tagstore.add_tag_to_taxonomy('testing', tax)
        tag2 = await self.tagstore.add_tag_to_taxonomy('Testing', tax)
        tags = set([t async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)])
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags, {tag1, tag2})

    async def test_allowed_tag_names(self):
        """ add_tag_to_taxonomy will allow these tags """
        valid_tags = [
            'lower',
            'UPPER',
            'spaces between words',
            '@handle',
            'Αλφα',
            '🔥',
        ]
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        for tag in valid_tags:
            await self.tagstore.add_tag_to_taxonomy(tag, tax)
        tags_created = set([t.tag async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)])
        self.assertEqual(tags_created, set(valid_tags))

    async def test_forbidden_tag_names(self):
        """ add_tag_to_taxonomy will reject certain tags """
        invalid_tags = [
            '',
            'misleading    ',
            ' misleading',
            'one, two',
            'one/two',
            'foo:bar',
            'foo;bar',
            'new\nline',
            'new\rline',
        ]
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        for tag in invalid_tags:
            with self.assertRaises(ValueError):
                await self.tagstore.add_tag_to_taxonomy(tag, tax)

    async def test_add_tag_to_taxonomy_idempotent(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy only once """
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        await self.tagstore.add_tag_to_taxonomy('testing', tax)
        await self.tagstore.add_tag_to_taxonomy('testing', tax)
        tags = [t async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(len(tags), 1)

    async def test_add_tag_to_taxonomy_circular(self):
        """ add_tag_to_taxonomy will not allow circular tags """
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        grandma = await self.tagstore.add_tag_to_taxonomy('grandma', tax)
        mother = await self.tagstore.add_tag_to_taxonomy('mother', tax, parent_tag=grandma)
        with self.assertRaises(ValueError):
            await self.tagstore.add_tag_to_taxonomy('grandma', tax, parent_tag=mother)

    async def _create_taxonomy_with_tags(self, tags: Iterable[str]) -> TaxonomyMetadata:
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        await asyncio.gather(*[self.tagstore.add_tag_to_taxonomy(tag, tax) for tag in tags])
        return tax

    async def test_list_tags_in_taxonomy(self):
        """ Test that listing tags in a taxonomy returns tags in alphabetical order """
        tags_in = ['Zulu', 'Uniform', 'Foxtrot', 'Βήτα', 'Alfa', 'Alpha', 'Αλφα']
        tags_out_expected = ['Alfa', 'Alpha', 'Foxtrot', 'Uniform', 'Zulu', 'Αλφα', 'Βήτα']
        tax = await self._create_taxonomy_with_tags(tags_in)
        tags_out = [t.tag async for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(tags_out, tags_out_expected)

    async def test_list_tags_in_taxonomy_containing(self):
        """ Test filtering tags """
        tags_in = ['Zulu', 'Uniform', 'Foxtrot', 'Βήτα', 'Alfa', 'Alpha', 'Αλφα']
        tax = await self._create_taxonomy_with_tags(tags_in)
        # Contains 'al' (case insensitive)
        results = [t.tag async for t in self.tagstore.list_tags_in_taxonomy_containing(tax.uid, "al")]
        self.assertEqual(results, ['Alfa', 'Alpha'])
        # Contains 'FO' (case insensitive)
        results = [t.tag async for t in self.tagstore.list_tags_in_taxonomy_containing(tax.uid, "FO")]
        self.assertEqual(results, ['Foxtrot', 'Uniform'])
        # Contains 'nomatch' (case insensitive)
        results = [t.tag async for t in self.tagstore.list_tags_in_taxonomy_containing(tax.uid, "nomatch")]
        self.assertEqual(results, [])

    # Tagging entities

    async def test_add_tag_to(self):
        """ Test add_tag_to """
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        tag = await self.tagstore.add_tag_to_taxonomy('testing', tax)
        entity_id = EntityId(entity_type='content', external_id='block-v1:b1')

        self.assertEqual(await self.tagstore.get_tags_applied_to(entity_id), set())
        await self.tagstore.add_tag_to(tag, entity_id)
        self.assertEqual(await self.tagstore.get_tags_applied_to(entity_id), {tag})

    async def test_entity_ids(self):
        """ Test that entities are always identified by their type AND external_id together """
        tax = await self.tagstore.create_taxonomy("TestTax", owner_id=1)
        tag1 = await self.tagstore.add_tag_to_taxonomy('t1', tax)
        tag2 = await self.tagstore.add_tag_to_taxonomy('t2', tax)
        tag3 = await self.tagstore.add_tag_to_taxonomy('t3', tax)
        tag4 = await self.tagstore.add_tag_to_taxonomy('t4', tax)
        entity1 = EntityId(entity_type='typeA', external_id='alpha')
        entity2 = EntityId(entity_type='typeA', external_id='beta')
        entity3 = EntityId(entity_type='typeB', external_id='alpha')  # Differs from entity1 only by type
        entity4 = EntityId(entity_type='typeB', external_id='beta')
        await self.tagstore.add_tag_to(tag1, entity1)
        await self.tagstore.add_tag_to(tag2, entity2)
        await self.tagstore.add_tag_to(tag3, entity3)
        await self.tagstore.add_tag_to(tag4, entity4)
        self.assertEqual(await self.tagstore.get_tags_applied_to(entity1), {tag1})
        self.assertEqual(await self.tagstore.get_tags_applied_to(entity2), {tag2})
        self.assertEqual(await self.tagstore.get_tags_applied_to(entity3), {tag3})
        self.assertEqual(await self.tagstore.get_tags_applied_to(entity4), {tag4})

    # Searching entities

    async def test_get_entities_tagged_with(self):
        """ Test get_entities_tagged_with() """
        sizes = await self.tagstore.create_taxonomy("sizes", owner_id=1)
        small = await self.tagstore.add_tag_to_taxonomy('small', sizes)
        med = await self.tagstore.add_tag_to_taxonomy('med', sizes)
        large = await self.tagstore.add_tag_to_taxonomy('large', sizes)

        biology = await self.tagstore.create_taxonomy("Biology", owner_id=1)
        plant = await self.tagstore.add_tag_to_taxonomy('plant', biology)
        conifer = await self.tagstore.add_tag_to_taxonomy('conifer', biology, parent_tag=plant)
        cypress = await self.tagstore.add_tag_to_taxonomy('cypress', biology, parent_tag=conifer)
        _pine = await self.tagstore.add_tag_to_taxonomy('pine', biology, parent_tag=conifer)
        aster = await self.tagstore.add_tag_to_taxonomy('aster', biology, parent_tag=plant)

        animal = await self.tagstore.add_tag_to_taxonomy('animal', biology)
        mammal = await self.tagstore.add_tag_to_taxonomy('mammal', biology, parent_tag=animal)
        fish = await self.tagstore.add_tag_to_taxonomy('fish', biology, parent_tag=animal)
        canine = await self.tagstore.add_tag_to_taxonomy('canine', biology, parent_tag=mammal)

        # Create some entities:
        elephant = EntityId(entity_type='thing', external_id='elephant')
        await self.tagstore.add_tag_to(large, elephant)
        await self.tagstore.add_tag_to(mammal, elephant)
        dog = EntityId(entity_type='thing', external_id='dog')
        await self.tagstore.add_tag_to(med, dog)
        await self.tagstore.add_tag_to(canine, dog)
        dandelion = EntityId(entity_type='thing', external_id='dandelion')
        await self.tagstore.add_tag_to(small, dandelion)
        await self.tagstore.add_tag_to(aster, dandelion)
        redwood = EntityId(entity_type='thing', external_id='redwood')
        await self.tagstore.add_tag_to(large, redwood)
        await self.tagstore.add_tag_to(cypress, redwood)

        # Run some searches and test the results:

        # large
        result = set([e async for e in self.tagstore.get_entities_tagged_with(large)])
        self.assertEqual(result, {elephant, redwood})

        # asters
        result = set([e async for e in self.tagstore.get_entities_tagged_with(aster)])
        self.assertEqual(result, {dandelion})

        # plants
        result = set([e async for e in self.tagstore.get_entities_tagged_with(plant)])
        self.assertEqual(result, {dandelion, redwood})

        # plants, with no tag inheritance
        result = set([e async for e in self.tagstore.get_entities_tagged_with(plant, include_child_tags=False)])
        self.assertEqual(result, set())

        # fish
        result = set([e async for e in self.tagstore.get_entities_tagged_with(fish)])
        self.assertEqual(result, set())

        # conifers
        result = set([e async for e in self.tagstore.get_entities_tagged_with(conifer)])
        self.assertEqual(result, {redwood})

        # cypress, with no tag inheritance
        result = set([e async for e in self.tagstore.get_entities_tagged_with(cypress, include_child_tags=False)])
        self.assertEqual(result, {redwood})

        # large things
        result = set([e async for e in self.tagstore.get_entities_tagged_with(large, entity_types=['thing'])])
        self.assertEqual(result, {elephant, redwood})

        # large non-things:
        result = set([e async for e in self.tagstore.get_entities_tagged_with(large, entity_types=['nonthing'])])
        self.assertEqual(result, set())

        # small things starting with "d"
        result = set([e async for e in self.tagstore.get_entities_tagged_with(
            small, entity_types=['thing'], external_id_prefix='d'
        )])
        self.assertEqual(result, {dandelion})

        # filter a pre-set list:
        result = set([e async for e in self.tagstore.get_entities_tagged_with(large, entity_ids=[elephant, dog])])
        self.assertEqual(result, {elephant})

        # large mammals:
        result = set([e async for e in self.tagstore.get_entities_tagged_with_all({large, mammal})])
        self.assertEqual(result, {elephant})


class Neo4jBackendTest(AbstractBackendTest, asynctest.TestCase):
    """ Test the Neo4j backend implementation """

    def get_backend(self) -> TagstoreBackend:
        # Run Neo4j with:
        #   docker run --publish=7474:7474 --publish=7687:7687 neo4j:3.4
        # Then go to http://localhost:7474/browser/ login (neo4j/neo4j)
        # and change the password to 'edx'
        import socket
        try:
            docker_host = 'host.docker.internal'
            socket.gethostbyaddr(docker_host)
            neo4j_host = docker_host
        except socket.gaierror:
            neo4j_host = 'localhost'
        return Neo4jTagstoreBackend({
            'url': f'bolt://{neo4j_host}:7687',
            'user': 'neo4j',
            'pass': 'edx',
        }, self.loop)

    async def setUp(self):
        super().setUp()
        # Reset Neo4j before each test case:
        await self.tagstore.backend.async_wrapper.aexec('''
            MATCH (n)
            DETACH DELETE n
        ''')


class DjangoBackendTest(AbstractBackendTest, asynctest.TestCase):
    """ Test the Django backend implementation """

    def get_backend(self) -> TagstoreBackend:
        return DjangoTagstoreBackend()

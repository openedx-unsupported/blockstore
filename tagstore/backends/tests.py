"""
Tests for all included backends
"""
# pylint: disable=no-member
import asynctest

from .. import Tagstore, TagstoreBackend
from .neo4j import Neo4jTagstoreBackend


class AbstractBackendTest:
    """ Abstract test that tests any backend implementation """

    def get_backend(self) -> TagstoreBackend:
        raise NotImplementedError()

    def setUp(self):
        backend = self.get_backend()
        self.tagstore = Tagstore(backend)

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


class Neo4jBackendTest(AbstractBackendTest, asynctest.TestCase):
    """ Test the Neo4j backend implementation """

    def get_backend(self) -> TagstoreBackend:
        return Neo4jTagstoreBackend({
            'url': 'bolt://host.docker.internal:7687',
            'user': 'neo4j',
            'pass': 'edx',
        }, self.loop)

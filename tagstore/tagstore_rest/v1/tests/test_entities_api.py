"""
Tests for Tagstore REST API v1: Entities
========================================

These tests help guarantee API functionality and backwards compatibility. A
test failure in this module should represent an instance where we're making a
breaking change to the REST API contract. Internal refactoring should never
result in breaking these tests. To that end:

1. Data setup should happen via REST API. No factories or models.
2. Introspection should happen via REST API. No query counts or model queries.
3. Tests should look for particular fields of interest but not assume they know
   every field, since additional ones can be added in a backwards compatible
   way. Testing one attribute at a time also makes it a lot easier to see when
   there is a regression, instead of trying to look at a large diff.

This file has many 😀 emojis in strings to test for Unicode encoding/decoding
related issues.
"""
from django.test import TestCase

from .api_client import TagstoreAPIClient
from .test_taxonomies_api import VALID_TAG_NAMES


class EntitiesTestCase(TestCase):
    """ Base class for tests of the Taxonomies API. """

    def setUp(self):
        super().setUp()
        self.client = TagstoreAPIClient()

    @classmethod
    def setUpClass(cls):
        """
        Create a taxonomy with some tags that the test cases can use.
        """
        super().setUpClass()
        client = TagstoreAPIClient()
        cls.taxonomy = client.create_taxonomy({"name": "Random Tag Collection"})
        client.add_taxonomy_tag(cls.taxonomy["id"], {"name": "parent tag"})
        client.add_taxonomy_tag(cls.taxonomy["id"], {"name": "child tag", "parent": "parent tag"})
        for tag_name in VALID_TAG_NAMES:
            client.add_taxonomy_tag(cls.taxonomy["id"], {"name": tag_name})

    def test_get_new_entity(self):
        """
        Test getting an entity that Tagstore has never seen, and which has no tags.
        """
        data = self.client.get_entity("course", "Calc101")
        self.assertDictContainsSubset({
            "entity_type": "course",
            "external_id": "Calc101",
            "persisted": False,  # The entity has never been tagged, so isn't yet persisted in Tagstore
            "tags": []
        }, data)

    def test_get_entity_with_tags(self):
        """
        An entity will be auto-created when its first tag is applied, and after that
        point it will have "persisted: true".
        """
        self.client.entity_add_tag(
            entity_type="course", external_id="Calc101",
            taxonomy_id=self.taxonomy["id"], tag_name="child tag",
        )

        data = self.client.get_entity("course", "Calc101")
        self.assertDictContainsSubset({
            "entity_type": "course",
            "external_id": "Calc101",
            "persisted": True,  # Now this has changed to true
        }, data)
        self.assertEqual(len(data["tags"]), 1)
        self.assertDictContainsSubset({
            "taxonomy_id": self.taxonomy["id"],
            "name": "child tag",
        }, data["tags"][0])
        # The exact value of "path" is an implementation detail so we don't assert
        # on it, but it should be a string.
        self.assertIsInstance(data["tags"][0]["path"], str)

    def test_has_tag(self):
        """
        Test the method for checking whether or not an entity has one
        specific tag.
        """
        args = dict(entity_type="course", external_id="Bio350", taxonomy_id=self.taxonomy["id"])
        for tag_name in VALID_TAG_NAMES:
            # At first, has_tag should return a 404 (the entity does not have that tag)
            self.client.entity_has_tag(**args, tag_name=tag_name, expect=404)
            # Then tag the entity:
            self.client.entity_add_tag(**args, tag_name=tag_name)
            # Now the we should be able to retrieve just that tag:
            data = self.client.entity_has_tag(**args, tag_name=tag_name)
            self.assertEqual(data["name"], tag_name)
            self.assertEqual(data["taxonomy_id"], self.taxonomy["id"])
            self.assertIsInstance(data["path"], str)

    def test_add_tag_nonexistent(self):
        """
        Tagstore should raise a 404 error if attempting to add a tag that doesn't exist
        to any entity.
        """
        self.client.entity_add_tag(
            entity_type="course", external_id="Calc101",
            taxonomy_id=self.taxonomy["id"], tag_name="This tag does not exist.",
            expect=404,
        )

    def test_remove_tag(self):
        """
        Test removing a tag from an entity.
        """
        entity_args = dict(entity_type="person", external_id="Alex")
        tag_name = "parent tag"
        tag_args = dict(taxonomy_id=self.taxonomy["id"], tag_name=tag_name)
        # First add a tag to the entity
        self.client.entity_add_tag(**entity_args, **tag_args)
        # Now the entity has that tag:
        self.assertIn(
            tag_name,
            [t["name"] for t in self.client.get_entity(**entity_args)["tags"]]
        )
        # Now remove the tag from the entity:
        self.client.entity_remove_tag(**entity_args, **tag_args)
        # Now the entity should not have that tag:
        self.assertNotIn(
            tag_name,
            [t["name"] for t in self.client.get_entity(**entity_args)["tags"]]
        )
        self.client.entity_has_tag(**entity_args, **tag_args, expect=404)

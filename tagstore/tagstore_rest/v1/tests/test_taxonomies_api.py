"""
Tests for Tagstore REST API v1: Taxonomies and Tags
===================================================

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


VALID_TAG_NAMES = [
    # The following tag names are all allowed, so we should test our REST API using them
    "basic",
    "Happy 😀",
    "challenging/difficult",
    "!@#$%^&*",
    "FOO => BAR",
]


class TaxonomiesTestCase(TestCase):
    """ Base class for tests of the Taxonomies API. """

    def setUp(self):
        super().setUp()
        self.client = TagstoreAPIClient()

    # Create & Retrieve

    def test_create_no_owner(self):
        """
        Test creating a taxonomy with no owner.
        """
        create_data = self.client.create_taxonomy({"name": "Test Taxonomy"})
        self.assertEqual(create_data["name"], "Test Taxonomy")
        tax_id = create_data["id"]

        get_data = self.client.get_taxonomy(tax_id)
        self.assertEqual(get_data["name"], "Test Taxonomy")
        self.assertEqual(get_data["owner"], None)

    def test_create_with_owner(self):
        """
        Test creating a taxonomy with an owner.

        The Entity object for the owner should be created automatically.
        """
        owner_data = {
            "entity_type": "user",
            "external_id": "123456",
        }
        create_data = self.client.create_taxonomy({
            "name": "Test Taxonomy",
            "owner": owner_data
        })
        self.assertEqual(create_data["name"], "Test Taxonomy")
        tax_id = create_data["id"]

        get_data = self.client.get_taxonomy(tax_id)
        self.assertEqual(get_data["name"], "Test Taxonomy")
        self.assertEqual(get_data["owner"], owner_data)

        # Create another taxonomy with the same owner to test it when
        # the entity already exists:
        create_data2 = self.client.create_taxonomy({
            "name": "Second Taxonomy",
            "owner": owner_data,
        })
        self.assertEqual(create_data2["name"], "Second Taxonomy")
        tax2_id = create_data2["id"]
        self.assertNotEqual(tax_id, tax2_id)
        self.assertEqual(create_data2["owner"], owner_data)

    def test_create_tag(self):
        """
        Create a taxonomy with one tag
        """
        taxonomy = self.client.create_taxonomy({"name": "Color Taxonomy"})
        # At first, the new taxonomy should not contain any tags:
        self.assertEqual(
            self.client.get_taxonomy_tags(taxonomy["id"])["results"],
            [],
        )
        # Now add a tag:
        tag1 = self.client.add_taxonomy_tag(taxonomy["id"], {"name": "yellow"})
        self.assertEqual(tag1["name"], "yellow")
        self.assertEqual(tag1["parent"], None)
        self.assertIsInstance(tag1["path"], str)  # Exact value of "path" is an implementation detail

        # At first, the new taxonomy should not contain any tags:
        tags = self.client.get_taxonomy_tags(taxonomy["id"])["results"]
        self.assertEqual(len(tags), 1)
        self.assertDictContainsSubset({"name": "yellow"}, tags[0])

    def test_create_tag_differing_case(self):
        """
        When creating a tag that differs only in case, the API should return
        the existing tag.

        We also stress-test Unicode capitalization.
        """
        taxonomy = self.client.create_taxonomy({"name": "Capitalization Test"})
        beyonce = self.client.add_taxonomy_tag(taxonomy["id"], {"name": "Beyoncé"})
        self.assertEqual(beyonce["name"], "Beyoncé")
        hello = self.client.add_taxonomy_tag(taxonomy["id"], {"name": "ħëłłô / 👋"})
        self.assertEqual(hello["name"], "ħëłłô / 👋")

        # Now, adding those tags with different capitalization should succeed but return
        # the original capitalization
        beyonce2 = self.client.add_taxonomy_tag(taxonomy["id"], {"name": "BEYONCÉ"})
        self.assertEqual(beyonce2["name"], "Beyoncé")
        hello = self.client.add_taxonomy_tag(taxonomy["id"], {"name": "ĦËŁŁÔ / 👋"})
        self.assertEqual(hello["name"], "ħëłłô / 👋")
        # And make sure that there are only two tags in the taxonomy
        self.assertEqual(self.client.get_taxonomy_tags(taxonomy["id"])["count"], 2)

    def test_get_tag_differing_case(self):
        """
        When directly querying a single tag, the API is case-insensitive.

        Also tests that we can encode '/' and special characters in the URL
        """
        taxonomy = self.client.create_taxonomy({"name": "Capitalization Test 2"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "Beyoncé"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "ħëłłô / 👋 / ?!"})

        self.assertEqual(
            self.client.get_taxonomy_tag(taxonomy["id"], "Beyoncé")["name"],
            "Beyoncé",
        )
        self.assertEqual(
            self.client.get_taxonomy_tag(taxonomy["id"], "BEYONCÉ")["name"],
            "Beyoncé",
        )
        self.assertEqual(
            self.client.get_taxonomy_tag(taxonomy["id"], "ĦËŁŁÔ / 👋 / ?!")["name"],
            "ħëłłô / 👋 / ?!",
        )

    def test_create_multiple_tags(self):
        """
        Create a taxonomy with multiple tags
        """
        taxonomy = self.client.create_taxonomy({"name": "Multitag Taxonomy"})
        for tag_name in VALID_TAG_NAMES:
            tag_data = self.client.add_taxonomy_tag(taxonomy["id"], {"name": tag_name})
            self.assertEqual(tag_data["name"], tag_name)

        # Now check that all the tags exist in the taxonomy:
        tags_data = self.client.get_taxonomy_tags(taxonomy["id"])
        self.assertEqual(tags_data["count"], len(VALID_TAG_NAMES))
        self.assertEqual(tags_data["num_pages"], 1)
        self.assertEqual(tags_data["current_page"], 1)
        self.assertEqual(tags_data["start"], 0)
        tags = tags_data["results"]
        self.assertEqual(len(tags), len(VALID_TAG_NAMES))
        tag_names = set(t["name"] for t in tags)
        self.assertSetEqual(tag_names, set(VALID_TAG_NAMES))

    def test_create_hierarchy(self):
        """
        Create a taxonomy with hierarchical data

        plants
            trees
                pine
            flowers
                daisy
        animals
            human
        """
        taxonomy = self.client.create_taxonomy({"name": "Biology"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "plants"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "trees", "parent": "plants"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "pine", "parent": "trees"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "flowers", "parent": "plants"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "daisy", "parent": "flowers"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "animals"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "human", "parent": "animals"})

        # Once a tag is created in one place, adding it elsewhere is an error:
        self.client.add_taxonomy_tag(
            taxonomy["id"], {"name": "human", "parent": "plants"},
            expect=400,
        )

        # Now read the hierarchy:
        all_tags = self.client.get_taxonomy_tags(taxonomy["id"])["results"]
        basic_data = [(t["name"], t["parent"]) for t in all_tags]
        expected_tags = [
            # The tags and their parents should be returned in alphabetical order,
            # parents always before children
            ("animals", None),
            ("human", "animals"),
            ("plants", None),
            ("flowers", "plants"),
            ("daisy", "flowers"),
            ("trees", "plants"),
            ("pine", "trees"),
        ]
        self.assertEqual(basic_data, expected_tags)

        # The "path" property of each tag should be globally unique
        self.assertEqual(len(set(t["path"] for t in all_tags)), len(expected_tags))

        # And children paths are guaranteed to begin with their parent's path:
        plants_path = self.client.get_taxonomy_tag(taxonomy["id"], "plants")["path"]
        trees_path = self.client.get_taxonomy_tag(taxonomy["id"], "trees")["path"]
        pine_path = self.client.get_taxonomy_tag(taxonomy["id"], "pine")["path"]
        self.assertTrue(trees_path.startswith(plants_path))
        self.assertTrue(pine_path.startswith(trees_path))
        self.assertTrue(pine_path.startswith(plants_path))

    def test_list_taxonomies(self):
        """
        Test the list of all taxonomies.

        They should be returned in alphabetical order by name
        """
        # Create Taxonomy B before A to confirm result sorting
        tb = self.client.create_taxonomy({"name": "Test Taxonomy B"})
        ta_owner_data = {"entity_type": "user", "external_id": "test_user"}
        ta = self.client.create_taxonomy({"name": "Test Taxonomy A", "owner": ta_owner_data})

        data = self.client.list_taxonomies()
        self.assertDictContainsSubset({
            "next": None,
            "previous": None,
            "count": 2,
            "num_pages": 1,
            "current_page": 1,
            "start": 0,
        }, data)
        # Taxonomy A should be first:
        self.assertDictContainsSubset({
            "id": ta["id"],
            "name": "Test Taxonomy A",
            "owner": ta_owner_data,
        }, data["results"][0])
        # Taxonomy B should be second:
        self.assertDictContainsSubset({
            "id": tb["id"],
            "name": "Test Taxonomy B",
            "owner": None,
        }, data["results"][1])

    # Update

    # Not implemented yet... eventually we should have a method to change a Taxonomy's name and/or owner

    # Delete

    def test_delete_tag(self):
        """
        Test deleting a tag from a taxonomy.
        """
        taxonomy = self.client.create_taxonomy({"name": "Deletion Test"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "tag1"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "tag2"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "tag3"})

        self.client.delete_taxonomy_tag(taxonomy["id"], "tag2")
        # Now we should get a 404 for that tag:
        self.client.get_taxonomy_tag(taxonomy["id"], "tag2", expect=404)
        # And make sure the tag2 is gone. Note that the API always returns tags in alphabetical order.
        tags = [t["name"] for t in self.client.get_taxonomy_tags(taxonomy["id"])["results"]]
        self.assertEqual(tags, ["tag1", "tag3"])

    def test_delete_taxonomy(self):
        """
        Test deleting a taxonomy.
        """
        taxonomy = self.client.create_taxonomy({"name": "Taxonomy Deletion Test"})
        self.client.add_taxonomy_tag(taxonomy["id"], {"name": "tag"})

        self.client.get_taxonomy(taxonomy["id"], expect=200)
        self.client.delete_taxonomy(taxonomy["id"])
        # Now we should get a 404 for that tag:
        self.client.get_taxonomy(taxonomy["id"], expect=404)

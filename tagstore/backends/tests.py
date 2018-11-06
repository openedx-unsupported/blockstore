"""
Tests for all included backends
"""
# pylint: disable=no-member, too-many-statements
from typing import Iterable

from django.test import TestCase

from .. import Tagstore
from ..models import EntityId, TaxonomyMetadata, UserId
from .django import DjangoTagstore


# Identify a user that will own the taxonomies we create
some_user = UserId(EntityId(entity_type='user', external_id='janedoe'))


class AbstractBackendTest:
    """ Abstract test that tests any backend implementation """
    tagstore: Tagstore

    def get_tagstore(self) -> Tagstore:
        raise NotImplementedError()

    def setUp(self):
        self.tagstore = self.get_tagstore()

    # Taxonomy CRUD

    def test_create_taxonomy(self):
        """ Creating a taxonomy generates a unique integer ID """
        taxonomy1 = self.tagstore.create_taxonomy("Taxonomy 1", owner_id=some_user)
        self.assertIsInstance(taxonomy1.uid, int)
        self.assertEqual(taxonomy1.name, "Taxonomy 1")
        self.assertEqual(taxonomy1.owner_id, some_user)
        taxonomy2 = self.tagstore.create_taxonomy("Taxonomy 2", owner_id=None)  # This one has no owner
        self.assertNotEqual(taxonomy1.uid, taxonomy2.uid)
        self.assertEqual(taxonomy2.owner_id, None)

    def test_get_taxonomy(self):
        """ Retrieve a taxonomy's metadata """
        written = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        read = self.tagstore.get_taxonomy(written.uid)
        self.assertEqual(written.uid, read.uid)
        self.assertEqual(written.name, read.name)
        self.assertEqual(written.owner_id, read.owner_id)

    def test_get_taxonomy_nonexistent(self):
        """ get_taxonomy() must return None if the taxonomy ID is invalid """
        result = self.tagstore.get_taxonomy(1e8)
        self.assertIsNone(result)

    def test_add_tag_to_taxonomy(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        self.assertEqual(len([t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]), 0)
        tag = self.tagstore.add_tag_to_taxonomy('testing', tax)
        tags = [t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], tag)
        # And it can also add by taxonomy ID alone:
        tag2 = self.tagstore.add_tag_to_taxonomy('testing 2', tax.uid)
        self.assertEqual(set(t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)), {tag, tag2})

    def test_case_sensitive_tags(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        self.assertEqual(len([t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]), 0)
        tag1 = self.tagstore.add_tag_to_taxonomy('testing', tax)
        tag2 = self.tagstore.add_tag_to_taxonomy('Testing', tax)
        tags = set([t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)])
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags, {tag1, tag2})

    def test_allowed_tag_names(self):
        """ add_tag_to_taxonomy will allow these tags """
        valid_tags = [
            'lower',
            'UPPER',
            'spaces between words',
            'true/correct',
            '@handle',
            'Αλφα',
            '🔥',
        ]
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        for tag in valid_tags:
            self.tagstore.add_tag_to_taxonomy(tag, tax)
        tags_created = set([t.tag for t in self.tagstore.list_tags_in_taxonomy(tax.uid)])
        self.assertEqual(tags_created, set(valid_tags))

    def test_forbidden_tag_names(self):
        """ add_tag_to_taxonomy will reject certain tags """
        invalid_tags = [
            '',
            'misleading    ',
            ' misleading',
            'one, two',
            'foo:bar',
            'foo;bar',
            'new\nline',
            'new\rline',
        ]
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        for tag in invalid_tags:
            with self.assertRaises(ValueError):
                self.tagstore.add_tag_to_taxonomy(tag, tax)

    def test_add_tag_to_taxonomy_idempotent(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy only once """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag1 = self.tagstore.add_tag_to_taxonomy('testing', tax)
        tag2 = self.tagstore.add_tag_to_taxonomy('testing', tax)
        self.assertEqual(tag1, tag2)
        tags = [t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(tags, [tag1])

    def test_add_tag_to_taxonomy_idempotent_parent(self):
        """
        add_tag_to_taxonomy will add a tag to the given taxonomy only once,
        including when it's a child tag with a parent
        """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        parent = self.tagstore.add_tag_to_taxonomy('parent', tax)
        child1 = self.tagstore.add_tag_to_taxonomy('child', tax, parent_tag=parent)
        child2 = self.tagstore.add_tag_to_taxonomy('child', tax, parent_tag=parent)
        self.assertEqual(child1, child2)
        tags = [t for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(len(tags), 2)  # the 2 tags are 'parent' and 'child'

    def test_add_tag_to_taxonomy_exists_elsewhere(self):
        """ add_tag_to_taxonomy will not allow a child that exists elsewhere """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        parent = self.tagstore.add_tag_to_taxonomy('parent', tax)
        other = self.tagstore.add_tag_to_taxonomy('other', tax)
        self.tagstore.add_tag_to_taxonomy('child', tax, parent_tag=parent)
        with self.assertRaises(ValueError):
            self.tagstore.add_tag_to_taxonomy('child', tax, parent_tag=other)
        with self.assertRaises(ValueError):
            self.tagstore.add_tag_to_taxonomy('child', tax)

    def test_add_tag_to_taxonomy_circular(self):
        """ add_tag_to_taxonomy will not allow circular tags """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        grandma = self.tagstore.add_tag_to_taxonomy('grandma', tax)
        mother = self.tagstore.add_tag_to_taxonomy('mother', tax, parent_tag=grandma)
        with self.assertRaises(ValueError):
            self.tagstore.add_tag_to_taxonomy('grandma', tax, parent_tag=mother)

    def test_add_tag_to_taxonomy_bad_parent(self):
        """ add_tag_to_taxonomy will not allow a parent from another taxonomy """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tax2 = self.tagstore.create_taxonomy("Other Taxonomy", owner_id=some_user)
        parent = self.tagstore.add_tag_to_taxonomy('parent', tax2)
        with self.assertRaises(ValueError):
            self.tagstore.add_tag_to_taxonomy('child', tax, parent_tag=parent)

    def _create_taxonomy_with_tags(self, tags: Iterable[str]) -> TaxonomyMetadata:
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        for tag in tags:
            self.tagstore.add_tag_to_taxonomy(tag, tax)
        return tax

    def test_list_tags_in_taxonomy(self):
        """ Test that listing tags in a taxonomy returns tags in alphabetical order """
        tags_in = ['Zulu', 'Uniform', 'Foxtrot', 'Βήτα', 'Alfa', 'Alpha', 'Αλφα']
        tags_out_expected = ['Alfa', 'Alpha', 'Foxtrot', 'Uniform', 'Zulu', 'Αλφα', 'Βήτα']
        tax = self._create_taxonomy_with_tags(tags_in)
        tags_out = [t.tag for t in self.tagstore.list_tags_in_taxonomy(tax.uid)]
        self.assertEqual(tags_out, tags_out_expected)

    def test_list_tags_in_taxonomy_hierarchically(self):
        """ Test that tags get returned with hierarchy information """
        biology = self.tagstore.create_taxonomy("Biology", owner_id=some_user)
        plant = self.tagstore.add_tag_to_taxonomy('plant', biology)
        conifer = self.tagstore.add_tag_to_taxonomy('conifer', biology, parent_tag=plant)
        cypress = self.tagstore.add_tag_to_taxonomy('cypress', biology, parent_tag=conifer)
        pine = self.tagstore.add_tag_to_taxonomy('pine', biology, parent_tag=conifer)
        aster = self.tagstore.add_tag_to_taxonomy('aster', biology, parent_tag=plant)

        tags_out = list(self.tagstore.list_tags_in_taxonomy_hierarchically(biology.uid))

        self.assertEqual(tags_out, [
            (plant, None),
            (aster, plant),
            (conifer, plant),
            (cypress, conifer),
            (pine, conifer),
        ])

    def test_list_tags_in_taxonomy_containing(self):
        """ Test filtering tags """
        tags_in = ['Zulu', 'Uniform', 'Foxtrot', 'Βήτα', 'Alfa', 'Alpha', 'Αλφα']
        tax = self._create_taxonomy_with_tags(tags_in)
        # Contains 'al' (case insensitive)
        results = [t.tag for t in self.tagstore.list_tags_in_taxonomy_containing(tax.uid, "al")]
        self.assertEqual(results, ['Alfa', 'Alpha'])
        # Contains 'FO' (case insensitive)
        results = [t.tag for t in self.tagstore.list_tags_in_taxonomy_containing(tax.uid, "FO")]
        self.assertEqual(results, ['Foxtrot', 'Uniform'])
        # Contains 'nomatch' (case insensitive)
        results = [t.tag for t in self.tagstore.list_tags_in_taxonomy_containing(tax.uid, "nomatch")]
        self.assertEqual(results, [])

    # Tagging entities

    def test_add_tag_to(self):
        """ Test add_tag_to """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag = self.tagstore.add_tag_to_taxonomy('testing', tax)
        entity_id = EntityId(entity_type='content', external_id='block-v1:b1')

        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), set())
        self.tagstore.add_tag_to(tag, entity_id)
        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), {tag})

    def test_remove_tag_from(self):
        """ Test remove_tag_from """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag1 = self.tagstore.add_tag_to_taxonomy('tag1', tax)
        tag2 = self.tagstore.add_tag_to_taxonomy('tag2', tax)
        entity_id = EntityId(entity_type='content', external_id='block-v1:b1')
        untagged_entity_id = EntityId(entity_type='content', external_id='block-v1:b2')

        self.tagstore.add_tag_to(tag1, entity_id)
        self.tagstore.add_tag_to(tag2, entity_id)
        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), {tag1, tag2})
        self.tagstore.remove_tag_from(tag1, entity_id)
        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), {tag2})
        self.tagstore.remove_tag_from(tag2, entity_id, untagged_entity_id)
        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), set())

    def test_entity_ids(self):
        """ Test that entities are always identified by their type AND external_id together """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag1 = self.tagstore.add_tag_to_taxonomy('t1', tax)
        tag2 = self.tagstore.add_tag_to_taxonomy('t2', tax)
        tag3 = self.tagstore.add_tag_to_taxonomy('t3', tax)
        tag4 = self.tagstore.add_tag_to_taxonomy('t4', tax)
        entity1 = EntityId(entity_type='typeA', external_id='alpha')
        entity2 = EntityId(entity_type='typeA', external_id='beta')
        entity3 = EntityId(entity_type='typeB', external_id='alpha')  # Differs from entity1 only by type
        entity4 = EntityId(entity_type='typeB', external_id='beta')
        self.tagstore.add_tag_to(tag1, entity1)
        self.tagstore.add_tag_to(tag2, entity2)
        self.tagstore.add_tag_to(tag3, entity3)
        self.tagstore.add_tag_to(tag4, entity4)
        self.assertEqual(self.tagstore.get_tags_applied_to(entity1), {tag1})
        self.assertEqual(self.tagstore.get_tags_applied_to(entity2), {tag2})
        self.assertEqual(self.tagstore.get_tags_applied_to(entity3), {tag3})
        self.assertEqual(self.tagstore.get_tags_applied_to(entity4), {tag4})

    # Searching entities

    def test_get_entities_tagged_with(self):
        """ Test get_entities_tagged_with() """
        sizes = self.tagstore.create_taxonomy("sizes", owner_id=some_user)
        small = self.tagstore.add_tag_to_taxonomy('small', sizes)
        med = self.tagstore.add_tag_to_taxonomy('med', sizes)
        large = self.tagstore.add_tag_to_taxonomy('large', sizes)

        biology = self.tagstore.create_taxonomy("Biology", owner_id=some_user)
        plant = self.tagstore.add_tag_to_taxonomy('plant', biology)
        conifer = self.tagstore.add_tag_to_taxonomy('conifer', biology, parent_tag=plant)
        cypress = self.tagstore.add_tag_to_taxonomy('cypress', biology, parent_tag=conifer)
        _pine = self.tagstore.add_tag_to_taxonomy('pine', biology, parent_tag=conifer)
        aster = self.tagstore.add_tag_to_taxonomy('aster', biology, parent_tag=plant)

        animal = self.tagstore.add_tag_to_taxonomy('animal', biology)
        mammal = self.tagstore.add_tag_to_taxonomy('mammal', biology, parent_tag=animal)
        fish = self.tagstore.add_tag_to_taxonomy('fish', biology, parent_tag=animal)
        canine = self.tagstore.add_tag_to_taxonomy('canine', biology, parent_tag=mammal)

        # Create some entities:
        elephant = EntityId(entity_type='thing', external_id='elephant')
        self.tagstore.add_tag_to(large, elephant)
        self.tagstore.add_tag_to(mammal, elephant)
        dog = EntityId(entity_type='thing', external_id='dog')
        self.tagstore.add_tag_to(med, dog)
        self.tagstore.add_tag_to(canine, dog)
        dandelion = EntityId(entity_type='thing', external_id='dandelion')
        self.tagstore.add_tag_to(small, dandelion)
        self.tagstore.add_tag_to(aster, dandelion)
        redwood = EntityId(entity_type='thing', external_id='redwood')
        self.tagstore.add_tag_to(large, redwood)
        self.tagstore.add_tag_to(cypress, redwood)

        # Run some searches and test the results:

        # large
        result = set([e for e in self.tagstore.get_entities_tagged_with(large)])
        self.assertEqual(result, {elephant, redwood})

        # asters
        result = set([e for e in self.tagstore.get_entities_tagged_with(aster)])
        self.assertEqual(result, {dandelion})

        # plants
        result = set([e for e in self.tagstore.get_entities_tagged_with(plant)])
        self.assertEqual(result, {dandelion, redwood})

        # plants, with no tag inheritance
        result = set([e for e in self.tagstore.get_entities_tagged_with(plant, include_child_tags=False)])
        self.assertEqual(result, set())

        # fish
        result = set([e for e in self.tagstore.get_entities_tagged_with(fish)])
        self.assertEqual(result, set())

        # conifers
        result = set([e for e in self.tagstore.get_entities_tagged_with(conifer)])
        self.assertEqual(result, {redwood})

        # cypress, with no tag inheritance
        result = set([e for e in self.tagstore.get_entities_tagged_with(cypress, include_child_tags=False)])
        self.assertEqual(result, {redwood})

        # large things
        result = set([e for e in self.tagstore.get_entities_tagged_with(large, entity_types=['thing'])])
        self.assertEqual(result, {elephant, redwood})

        # large non-things:
        result = set([e for e in self.tagstore.get_entities_tagged_with(large, entity_types=['nonthing'])])
        self.assertEqual(result, set())

        # small things starting with "d"
        result = set([e for e in self.tagstore.get_entities_tagged_with(
            small, entity_types=['thing'], external_id_prefix='d'
        )])
        self.assertEqual(result, {dandelion})

        # filter a pre-set list:
        result = set([e for e in self.tagstore.get_entities_tagged_with(large, entity_ids=[elephant, dog])])
        self.assertEqual(result, {elephant})

        # large mammals:
        result = set([e for e in self.tagstore.get_entities_tagged_with_all({large, mammal})])
        self.assertEqual(result, {elephant})


class DjangoBackendTest(AbstractBackendTest, TestCase):
    """ Test the Django backend implementation """

    def get_tagstore(self) -> Tagstore:
        return DjangoTagstore()

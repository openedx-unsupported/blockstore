"""
Tests for all included backends
"""
# pylint: disable=no-member, too-many-statements
from typing import Iterable

from django.test import TestCase

from ... import Tagstore
from ...models import EntityId, Tag, Taxonomy, UserId
from ..django import DjangoTagstore


# Identify a user that will own the taxonomies we create
some_user = UserId(EntityId(entity_type='user', external_id='janedoe'))


class AbstractBackendTest:
    """ Abstract test that tests any backend implementation """
    tagstore = None

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
        self.assertEqual(len(list(tax.list_tags())), 0)
        tag = tax.add_tag('testing')
        tags = list(tax.list_tags())
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], tag)
        tag2 = tax.add_tag('testing 2')
        self.assertEqual(set(t for t in tax.list_tags()), {tag, tag2})

    def test_case_sensitive_tags(self):
        """
        Check case sensitive behavior

        Tags preserve the case that they are originally created with.
        Searching for tags is always case-insensitive.
        """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        self.assertEqual(len(list(tax.list_tags())), 0)
        tag1 = tax.add_tag('testing')
        tag2 = tax.add_tag('Testing')
        self.assertEqual(tag2.name, 'testing')  # It should have returned the existing tag's case
        tags = set(tax.list_tags())
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags, {tag1, tag2})
        # get_tag should also respect the original case:
        self.assertEqual(tax.get_tag('testing').name, 'testing')
        self.assertEqual(tax.get_tag('teSTING').name, 'testing')

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
            tax.add_tag(tag)
        tags_created = set(t.name for t in tax.list_tags())
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
                tax.add_tag(tag, tax)

    def test_add_tag_to_taxonomy_idempotent(self):
        """ add_tag_to_taxonomy will add a tag to the given taxonomy only once """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag1 = tax.add_tag('testing')
        tag2 = tax.add_tag('testing')
        self.assertEqual(tag1, tag2)
        tags = list(tax.list_tags())
        self.assertEqual(tags, [tag1])

    def test_add_tag_to_taxonomy_idempotent_parent(self):
        """
        add_tag_to_taxonomy will add a tag to the given taxonomy only once,
        including when it's a child tag with a parent
        """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        parent = tax.add_tag('parent')
        child1 = tax.add_tag('child', parent_tag=parent)
        child2 = tax.add_tag('child', parent_tag=parent)
        self.assertEqual(child1, child2)
        self.assertEqual(len(list(tax.list_tags())), 2)  # the 2 tags are 'parent' and 'child'

    def test_add_tag_to_taxonomy_exists_elsewhere(self):
        """ add_tag_to_taxonomy will not allow a child that exists elsewhere """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        parent = tax.add_tag('parent')
        other = tax.add_tag('other')
        tax.add_tag('child', parent_tag=parent)
        with self.assertRaises(ValueError):
            tax.add_tag('child', parent_tag=other)
        with self.assertRaises(ValueError):
            tax.add_tag('child')

    def test_add_tag_to_taxonomy_circular(self):
        """ add_tag_to_taxonomy will not allow circular tags """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        grandma = tax.add_tag('grandma')
        mother = tax.add_tag('mother', parent_tag=grandma)
        with self.assertRaises(ValueError):
            tax.add_tag('grandma', parent_tag=mother)

    def test_add_tag_to_taxonomy_bad_parent(self):
        """ add_tag_to_taxonomy will not allow a parent from another taxonomy """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tax2 = self.tagstore.create_taxonomy("Other Taxonomy", owner_id=some_user)
        parent = tax2.add_tag('parent')
        with self.assertRaises(ValueError):
            tax.add_tag('child', parent_tag=parent)

    def test_add_tag_to_taxonomy_nonexistent_parent(self):
        """ add_tag_to_taxonomy will not allow a parent that doesn't exist """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        parent = Tag(taxonomy_uid=tax.uid, name='bad')
        with self.assertRaises(ValueError):
            tax.add_tag('child', parent_tag=parent)

    def test_get_tag_in_taxonomy(self):
        """ get_tag_in_taxonomy will retrieve Tags """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        self.assertEqual(tax.get_tag('testing'), None)
        tag = tax.add_tag('testing')
        self.assertEqual(tax.get_tag('testing'), tag)

    def _create_taxonomy_with_tags(self, tags: Iterable[str]) -> Taxonomy:
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)  # type: ignore
        for tag in tags:
            tax.add_tag(tag)
        return tax

    def test_list_tags_in_taxonomy(self):
        """ Test that listing tags in a taxonomy returns tags in alphabetical order """
        tags_in = ['Zulu', 'Uniform', 'Foxtrot', 'Βήτα', 'Alfa', 'Alpha', 'Αλφα']
        tags_out_expected = ['Alfa', 'Alpha', 'Foxtrot', 'Uniform', 'Zulu', 'Αλφα', 'Βήτα']
        tax = self._create_taxonomy_with_tags(tags_in)
        tags_out = [t.name for t in tax.list_tags()]
        self.assertEqual(tags_out, tags_out_expected)

    def test_list_tags_in_taxonomy_hierarchically(self):
        """ Test that tags get returned with hierarchy information """
        biology = self.tagstore.create_taxonomy("Biology", owner_id=some_user)
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        cypress = biology.add_tag('cypress', parent_tag=conifer)
        pine = biology.add_tag('pine', parent_tag=conifer)
        aster = biology.add_tag('aster', parent_tag=plant)

        tags_out = list(biology.list_tags_hierarchically())

        self.assertEqual(tags_out, [
            (plant, None),
            (aster, plant),
            (conifer, plant),
            (cypress, conifer),
            (pine, conifer),
        ])

    def test_get_tags_in_taxonomy_hierarchically_as_dict(self):
        """ Test that tags get returned as dictionary """
        biology = self.tagstore.create_taxonomy("Biology", owner_id=some_user)
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        biology.add_tag('cypress', parent_tag=conifer)
        biology.add_tag('pine', parent_tag=conifer)
        biology.add_tag('aster', parent_tag=plant)

        tags_out = self.tagstore.get_tags_in_taxonomy_hierarchically_as_dict(biology.uid)

        self.assertEqual(tags_out['children'][0]['name'], 'plant')
        self.assertEqual(tags_out['children'][0]['children'][0]['name'], 'aster')
        self.assertEqual(tags_out['children'][0]['children'][1]['name'], 'conifer')
        tags_out_conifer = tags_out['children'][0]['children'][1]
        self.assertEqual(tags_out_conifer['children'][0]['name'], 'cypress')
        self.assertEqual(tags_out_conifer['children'][1]['name'], 'pine')

    def test_list_tags_in_taxonomy_containing(self):
        """ Test filtering tags """
        tags_in = ['Zulu', 'Uniform', 'Foxtrot', 'Βήτα', 'Alfa', 'Alpha', 'Αλφα']
        tax = self._create_taxonomy_with_tags(tags_in)
        # Contains 'al' (case insensitive)
        results = [t.name for t in tax.list_tags_containing("al")]
        self.assertEqual(results, ['Alfa', 'Alpha'])
        # Contains 'FO' (case insensitive)
        results = [t.name for t in tax.list_tags_containing("FO")]
        self.assertEqual(results, ['Foxtrot', 'Uniform'])
        # Contains 'nomatch' (case insensitive)
        results = [t.name for t in tax.list_tags_containing("nomatch")]
        self.assertEqual(results, [])

    # Tagging entities

    def test_add_tag_to(self):
        """ Test add_tag_to """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag = tax.add_tag('testing')
        entity_id = EntityId(entity_type='content', external_id='block-v1:b1')

        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), set())
        self.tagstore.add_tag_to(tag, entity_id)
        self.assertEqual(self.tagstore.get_tags_applied_to(entity_id), {tag})

    def test_remove_tag_from(self):
        """ Test remove_tag_from """
        tax = self.tagstore.create_taxonomy("TestTax", owner_id=some_user)
        tag1 = tax.add_tag('tag1')
        tag2 = tax.add_tag('tag2')
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
        tag1 = tax.add_tag('t1')
        tag2 = tax.add_tag('t2')
        tag3 = tax.add_tag('t3')
        tag4 = tax.add_tag('t4')
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
        small = sizes.add_tag('small')
        med = sizes.add_tag('med')
        large = sizes.add_tag('large')

        biology = self.tagstore.create_taxonomy("Biology", owner_id=some_user)
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        cypress = biology.add_tag('cypress', parent_tag=conifer)
        _pine = biology.add_tag('pine', parent_tag=conifer)
        aster = biology.add_tag('aster', parent_tag=plant)

        animal = biology.add_tag('animal')
        mammal = biology.add_tag('mammal', parent_tag=animal)
        fish = biology.add_tag('fish', parent_tag=animal)
        canine = biology.add_tag('canine', parent_tag=mammal)

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
        result = set(self.tagstore.get_entities_tagged_with(large))
        self.assertEqual(result, {elephant, redwood})

        # asters
        result = set(self.tagstore.get_entities_tagged_with(aster))
        self.assertEqual(result, {dandelion})

        # plants
        result = set(self.tagstore.get_entities_tagged_with(plant))
        self.assertEqual(result, {dandelion, redwood})

        # plants, with no tag inheritance
        result = set(self.tagstore.get_entities_tagged_with(plant, include_child_tags=False))
        self.assertEqual(result, set())

        # fish
        result = set(self.tagstore.get_entities_tagged_with(fish))
        self.assertEqual(result, set())

        # conifers
        result = set(self.tagstore.get_entities_tagged_with(conifer))
        self.assertEqual(result, {redwood})

        # cypress, with no tag inheritance
        result = set(self.tagstore.get_entities_tagged_with(cypress, include_child_tags=False))
        self.assertEqual(result, {redwood})

        # large things
        result = set(self.tagstore.get_entities_tagged_with(large, entity_types=['thing']))
        self.assertEqual(result, {elephant, redwood})

        # large non-things:
        result = set(self.tagstore.get_entities_tagged_with(large, entity_types=['nonthing']))
        self.assertEqual(result, set())

        # small things starting with "d"
        result = set(self.tagstore.get_entities_tagged_with(
            small, entity_types=['thing'], external_id_prefix='d'
        ))
        self.assertEqual(result, {dandelion})

        # filter a pre-set list:
        result = set(self.tagstore.get_entities_tagged_with(large, entity_ids=[elephant, dog]))
        self.assertEqual(result, {elephant})

        # large mammals:
        result = set(self.tagstore.get_entities_tagged_with_all({large, mammal}))
        self.assertEqual(result, {elephant})

    def test_get_entities_tagged_with_all_invalid(self):
        """ Test get_entities_tagged_with_all() with invalid arguments """
        with self.assertRaises(ValueError):
            # Passing zero tags as the first argument should raise a value error:
            list(self.tagstore.get_entities_tagged_with_all(set(), entity_types=['thing']))


class DjangoBackendTest(AbstractBackendTest, TestCase):
    """ Test the Django backend implementation """

    def get_tagstore(self) -> Tagstore:
        return DjangoTagstore()

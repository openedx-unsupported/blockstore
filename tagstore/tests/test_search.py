"""
Tests for tag-based searching
"""
from django.test import TestCase

from tagstore.models import EntityId, Taxonomy
from tagstore.search import (
    get_entities_tagged_with,
    get_entities_tagged_with_all,
)


class TagstoreSearchTest(TestCase):
    """ Tests for tag-based searching """

    def setUp(self):
        super().setUp()

        self.sizes = sizes = Taxonomy.objects.create(name="sizes")
        self.small = sizes.add_tag('small')
        self.med = sizes.add_tag('med')
        self.large = sizes.add_tag('large')

        self.biology = Taxonomy.objects.create(name="Biology")

        self.plant = self.biology.add_tag('plant')
        self.conifer = self.biology.add_tag('conifer', parent_tag=self.plant)
        self.cypress = self.biology.add_tag('cypress', parent_tag=self.conifer)
        self.pine = self.biology.add_tag('pine', parent_tag=self.conifer)
        self.aster = self.biology.add_tag('aster', parent_tag=self.plant)

        self.animal = self.biology.add_tag('animal')
        self.mammal = self.biology.add_tag('mammal', parent_tag=self.animal)
        self.fish = self.biology.add_tag('fish', parent_tag=self.animal)
        self.canine = self.biology.add_tag('canine', parent_tag=self.mammal)

        # Create some entities:
        self.elephant = EntityId(entity_type='thing', external_id='elephant')
        self.large.add_to(self.elephant)
        self.mammal.add_to(self.elephant)
        self.dog = EntityId(entity_type='thing', external_id='dog')
        self.med.add_to(self.dog)
        self.canine.add_to(self.dog)
        self.dandelion = EntityId(entity_type='thing', external_id='dandelion')
        self.small.add_to(self.dandelion)
        self.aster.add_to(self.dandelion)
        self.redwood = EntityId(entity_type='thing', external_id='redwood')
        self.large.add_to(self.redwood)
        self.cypress.add_to(self.redwood)

        # To test that we can use Tag or TagId in the search API, convert some
        # Tags to TagIds
        self.animal = self.animal.id
        self.mammal = self.mammal.id
        self.fish = self.fish.id
        self.canine = self.canine.id

    def test_get_entities_tagged_with(self):
        """ Test get_entities_tagged_with() """

        # Run some searches and test the results:

        # large
        result = set(get_entities_tagged_with(self.large))
        self.assertEqual(result, {self.elephant, self.redwood})

        # asters
        result = set(get_entities_tagged_with(self.aster))
        self.assertEqual(result, {self.dandelion})

        # plants
        result = set(get_entities_tagged_with(self.plant))
        self.assertEqual(result, {self.dandelion, self.redwood})

        # plants, with no tag inheritance
        result = set(get_entities_tagged_with(self.plant, include_child_tags=False))
        self.assertEqual(result, set())

        # fish
        result = set(get_entities_tagged_with(self.fish))
        self.assertEqual(result, set())

        # conifers
        result = set(get_entities_tagged_with(self.conifer))
        self.assertEqual(result, {self.redwood})

        # cypress, with no tag inheritance
        result = set(get_entities_tagged_with(self.cypress, include_child_tags=False))
        self.assertEqual(result, {self.redwood})

        # large things
        result = set(get_entities_tagged_with(self.large, entity_types=['thing']))
        self.assertEqual(result, {self.elephant, self.redwood})

        # large non-things:
        result = set(get_entities_tagged_with(self.large, entity_types=['nonthing']))
        self.assertEqual(result, set())

        # small things starting with "d"
        result = set(get_entities_tagged_with(
            self.small, entity_types=['thing'], external_id_prefix='d'
        ))
        self.assertEqual(result, {self.dandelion})

        # filter a pre-set list:
        result = set(get_entities_tagged_with(self.large, entity_ids=[self.elephant, self.dog]))
        self.assertEqual(result, {self.elephant})

    def test_get_entities_tagged_with_all(self):
        """ Test get_entities_tagged_with_all() """

        # large mammals:
        result = set([e for e in get_entities_tagged_with_all({self.large, self.mammal})])
        self.assertEqual(result, {self.elephant})

    def test_get_entities_tagged_with_all_invalid(self):
        """ Test get_entities_tagged_with_all() with invalid arguments """
        with self.assertRaises(ValueError):
            # Passing zero tags as the first argument should raise a value error:
            list(get_entities_tagged_with_all(set(), entity_types=['thing']))

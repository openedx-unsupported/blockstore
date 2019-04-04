"""
Tests for tagging entities
"""
from django.test import TestCase

from tagstore.models import EntityId, Taxonomy
from tagstore.search import get_tags_applied_to


class TagstoreTaggingTest(TestCase):
    """ Tests for tagging entities """

    def test_add_to(self):
        """ Test add_to """
        tax = Taxonomy.objects.create(name="TestTax")
        tag = tax.add_tag('testing')
        entity_id = EntityId(entity_type='content', external_id='block-v1:b1')

        self.assertEqual(get_tags_applied_to(entity_id), set())
        tag.add_to(entity_id)
        self.assertEqual(get_tags_applied_to(entity_id), {tag.id})

    def test_remove_from(self):
        """ Test remove_from """
        tax = Taxonomy.objects.create(name="TestTax")
        tag1 = tax.add_tag('tag1')
        tag2 = tax.add_tag('tag2')
        entity_id = EntityId(entity_type='content', external_id='block-v1:b1')
        untagged_entity_id = EntityId(entity_type='content', external_id='block-v1:b2')

        tag1.add_to(entity_id)
        tag2.add_to(entity_id)
        self.assertEqual(get_tags_applied_to(entity_id), {tag1.id, tag2.id})
        tag1.remove_from(entity_id)
        self.assertEqual(get_tags_applied_to(entity_id), {tag2.id})
        tag2.remove_from(entity_id, untagged_entity_id)
        self.assertEqual(get_tags_applied_to(entity_id), set())

    def test_entity_ids(self):
        """ Test that entities are always identified by their type AND external_id together """
        tax = Taxonomy.objects.create(name="TestTax")
        tag1 = tax.add_tag('t1')
        tag2 = tax.add_tag('t2')
        tag3 = tax.add_tag('t3')
        tag4 = tax.add_tag('t4')
        entity1 = EntityId(entity_type='typeA', external_id='alpha')
        entity2 = EntityId(entity_type='typeA', external_id='beta')
        entity3 = EntityId(entity_type='typeB', external_id='alpha')  # Differs from entity1 only by type
        entity4 = EntityId(entity_type='typeB', external_id='beta')
        tag1.add_to(entity1)
        tag2.add_to(entity2)
        tag3.add_to(entity3)
        tag4.add_to(entity4)
        self.assertEqual(get_tags_applied_to(entity1), {tag1.id})
        self.assertEqual(get_tags_applied_to(entity2), {tag2.id})
        self.assertEqual(get_tags_applied_to(entity3), {tag3.id})
        self.assertEqual(get_tags_applied_to(entity4), {tag4.id})

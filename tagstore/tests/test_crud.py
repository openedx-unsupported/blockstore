"""
Tests for Entity/Tag/Taxonomy Create, Read, Update, Delete
"""
from typing import Iterable

from django.core.exceptions import ValidationError
from django.test import TestCase

from tagstore.models import EntityId, Entity, Tag, Taxonomy


# Identify a user that will own the taxonomies we create
some_user = EntityId(entity_type='user', external_id='janedoe')


class TagstoreCrudTest(TestCase):
    """ Tests for Entity/Tag/Taxonomy Create, Read, Update, Delete """

    def test_create_taxonomy(self):
        """ Creating a taxonomy generates a unique integer ID """
        taxonomy1 = Taxonomy.objects.create(name="Taxonomy 1", owner=Entity.get(some_user))
        # self.assertIsInstance(taxonomy1.id, TaxonomyId)  # We can't type check NewType[] objects :/
        self.assertEqual(taxonomy1.name, "Taxonomy 1")
        self.assertEqual(taxonomy1.owner.id, some_user)
        taxonomy2 = Taxonomy.objects.create(name="Taxonomy 2", owner_id=None)  # This one has no owner
        # self.assertNotEqual(taxonomy1.id, taxonomy2.id)  # We can't type check NewType[] objects :/
        self.assertEqual(taxonomy2.name, "Taxonomy 2")
        self.assertEqual(taxonomy2.owner, None)

    def test_add_tag(self):
        """ Taxonomy.add_tag will add a tag to the given taxonomy """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        self.assertEqual(len(list(tax.list_tags())), 0)
        tag = tax.add_tag('testing')
        tags = list(tax.list_tags())
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], tag.id)
        tag2 = tax.add_tag('testing 2')
        self.assertEqual(set(tax.list_tags()), {tag.id, tag2.id})

    def test_add_tag_directly(self):
        """ Tag().save() is forbidden since it cannot validate hierarchy """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        with self.assertRaises(Exception):
            Tag.objects.create(taxonomy=tax, name='test')
        with self.assertRaises(Exception):
            Tag(taxonomy_id=tax.pk, name='other_test').save()

    def test_case_sensitive_tags(self):
        """
        Check case sensitive behavior

        Tags preserve the case that they are originally created with.
        Searching for tags is always case-insensitive.
        """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        self.assertEqual(len([t for t in tax.list_tags()]), 0)
        tag1 = tax.add_tag('testing')
        tag2 = tax.add_tag('Testing')
        self.assertEqual(tag2.name, 'testing')  # It should have returned the existing tag's case
        tags = set([t for t in tax.list_tags()])
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags, {tag1.id, tag2.id})
        # get_tag should also respect the original case:
        self.assertEqual(tax.get_tag('testing').name, 'testing')
        self.assertEqual(tax.get_tag('teSTING').name, 'testing')

    def test_allowed_tag_names(self):
        """ add_tag will allow these tags """
        valid_tags = [
            'lower',
            'UPPER',
            'spaces between words',
            'true/correct',
            '@handle',
            'Αλφα',
            '🔥',
        ]
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        for tag in valid_tags:
            tax.add_tag(tag)
        tags_created = set([t.name for t in tax.list_tags()])
        self.assertEqual(tags_created, set(valid_tags))

    def test_forbidden_tag_names(self):
        """ add_tag will reject certain tags """
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
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        for tag in invalid_tags:
            with self.assertRaises(ValidationError):
                tax.add_tag(tag)

    def test_add_tag_idempotent(self):
        """ add_tag will add a tag to the given taxonomy only once """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        tag1 = tax.add_tag('testing')
        tag2 = tax.add_tag('testing')
        self.assertEqual(tag1, tag2)
        tags = list(tax.list_tags())
        self.assertEqual(tags, [tag1.id])

    def test_add_tag_idempotent_parent(self):
        """
        add_tag will add a tag to the given taxonomy only once,
        including when it's a child tag with a parent
        """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        parent = tax.add_tag('parent')
        child1 = tax.add_tag('child', parent_tag=parent)
        child2 = tax.add_tag('child', parent_tag=parent)
        self.assertEqual(child1, child2)
        tags = [t for t in tax.list_tags()]
        self.assertEqual(len(tags), 2)  # the 2 tags are 'parent' and 'child'

    def test_add_tag_exists_elsewhere(self):
        """ add_tag will not allow a child that exists elsewhere """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        parent = tax.add_tag('parent')
        other = tax.add_tag('other')
        tax.add_tag('child', parent_tag=parent)
        with self.assertRaises(Tag.AlreadyExistsError):
            tax.add_tag('child', parent_tag=other)
        with self.assertRaises(Tag.AlreadyExistsError):
            tax.add_tag('child')

    def test_add_tag_circular(self):
        """ add_tag will not allow circular tags """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        grandma = tax.add_tag('grandma')
        mother = tax.add_tag('mother', parent_tag=grandma)
        with self.assertRaises(Tag.AlreadyExistsError):
            tax.add_tag('grandma', parent_tag=mother)

    def test_add_tag_bad_parent(self):
        """ add_tag will not allow a parent from another taxonomy """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        tax2 = Taxonomy.objects.create(name="Other Taxonomy", owner=Entity.get(some_user))
        parent = tax2.add_tag('parent')
        with self.assertRaises(Tag.ValidationError):
            tax.add_tag('child', parent_tag=parent)

    def test_add_tag_nonexistent_parent(self):
        """ add_tag will not allow a parent that doesn't exist """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        parent = Tag(taxonomy_id=tax.id, name='bad')
        with self.assertRaises(Tag.DoesNotExist):
            tax.add_tag('child', parent_tag=parent)

    def test_tag_delete(self):
        """
        Test Tag.delete()
        """
        biology = Taxonomy.objects.create(name="Biology", owner=Entity.get(some_user))
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        cypress = biology.add_tag('cypress', parent_tag=conifer)
        pine = biology.add_tag('pine', parent_tag=conifer)
        aster = biology.add_tag('aster', parent_tag=plant)

        self.assertEqual(biology.get_tag('conifer'), conifer.id)
        self.assertEqual(biology.get_tag('cypress'), cypress.id)
        self.assertEqual(biology.get_tag('pine'), pine.id)
        conifer.delete()
        self.assertEqual(biology.get_tag('conifer'), None)
        self.assertEqual(biology.get_tag('cypress'), None)
        self.assertEqual(biology.get_tag('pine'), None)
        self.assertEqual(biology.get_tag('aster'), aster.id)

    def test_taxonomy_delete_tag(self):
        """
        Test Taxonomy.delete_tag()
        """
        biology = Taxonomy.objects.create(name="Biology", owner=Entity.get(some_user))
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        _cypress = biology.add_tag('cypress', parent_tag=conifer)
        _pine = biology.add_tag('pine', parent_tag=conifer)
        aster = biology.add_tag('aster', parent_tag=plant)

        # Delete the aster tag by name:
        self.assertEqual(biology.get_tag('aster'), aster.id)
        biology.delete_tag('aster')
        self.assertEqual(biology.get_tag('aster'), None)
        # Delete the 'conifer' tag and subtags by ID:
        self.assertEqual(biology.get_tag('conifer'), conifer.id)
        biology.delete_tag(conifer.id)
        self.assertEqual(biology.get_tag('conifer'), None)
        self.assertEqual(biology.get_tag('cypress'), None)
        self.assertEqual(biology.get_tag('pine'), None)

    def test_taxonomy_delete_tag_from_other_taxonomy(self):
        """
        Test Taxonomy.delete_tag() with a TagId from another taxonomy
        """
        biology = Taxonomy.objects.create(name="Biology")
        plant = biology.add_tag('plant')
        sizes = Taxonomy.objects.create(name="Sizes")
        _large = biology.add_tag('large')

        with self.assertRaises(ValueError):
            sizes.delete_tag(plant.id)

    def test_get_tag(self):
        """ get_tag will retrieve Tag IDs """
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
        self.assertEqual(tax.get_tag('testing'), None)
        tag = tax.add_tag('testing')
        self.assertEqual(tax.get_tag('testing'), tag.id)

    def _create_taxonomy_with_tags(self, tags: Iterable[str]) -> Taxonomy:
        tax = Taxonomy.objects.create(name="TestTax", owner=Entity.get(some_user))
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
        biology = Taxonomy.objects.create(name="Biology", owner=Entity.get(some_user))
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        cypress = biology.add_tag('cypress', parent_tag=conifer)
        pine = biology.add_tag('pine', parent_tag=conifer)
        aster = biology.add_tag('aster', parent_tag=plant)

        tags_out = list(biology.list_tags_hierarchically())

        self.assertEqual(tags_out, [
            (plant.id, None),
            (aster.id, plant.id),
            (conifer.id, plant.id),
            (cypress.id, conifer.id),
            (pine.id, conifer.id),
        ])

    def test_get_tags_hierarchically_as_dict(self):
        """ Test that tags get returned as dictionary """
        biology = Taxonomy.objects.create(name="Biology", owner=Entity.get(some_user))
        plant = biology.add_tag('plant')
        conifer = biology.add_tag('conifer', parent_tag=plant)
        biology.add_tag('cypress', parent_tag=conifer)
        biology.add_tag('pine', parent_tag=conifer)
        biology.add_tag('aster', parent_tag=plant)

        tags_out = biology.get_tags_hierarchically_as_dict()

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

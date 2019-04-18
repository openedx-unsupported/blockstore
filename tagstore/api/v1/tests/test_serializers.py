""" Tests for api v1 serializers. """

from django.test import TestCase

from tagstore.models import (
    Entity,
    Taxonomy,
)
from tagstore.api.serializers import (
    TagSerializer,
    EntitySerializer,
    EntityDetailSerializer,
)


class TagSerializerTestCase(TestCase):
    """
    Test TagSerializer
    """

    def test_tag_serializer(self):
        """
        Test serializing a tag.
        """
        taxonomy = Taxonomy.objects.create(name="Test Taxonomy")

        parent_tag = taxonomy.add_tag("parent")
        child_tag = taxonomy.add_tag("child", parent_tag=parent_tag)

        parent_out = TagSerializer(parent_tag).data
        self.assertDictEqual(parent_out, {
            "taxonomy_id": taxonomy.id,
            "name": "parent",
            "path": f"{taxonomy.id}:{parent_tag}:",
            "parent": None,
        })

        child_out = TagSerializer(child_tag).data
        self.assertDictEqual(child_out, {
            "taxonomy_id": taxonomy.id,
            "name": "child",
            "path": f"{taxonomy.id}:{parent_tag}:{child_tag}:",
            "parent": parent_tag.name,
        })
        # Test that with the 'exclude_parent=True' flag, the serializer omits
        # the 'parent' field, which is only needed when displaying a taxonomy
        child_out_no_parent = TagSerializer(child_tag, exclude_parent=True).data
        self.assertDictEqual(child_out_no_parent, {
            "taxonomy_id": taxonomy.id,
            "name": "child",
            "path": f"{taxonomy.id}:{parent_tag}:{child_tag}:",
        })


class EntitySerializerTestCase(TestCase):
    """
    Test EntitySerializer
    """

    def test_persisted_entity(self):
        """
        Test serializing an entity that exists in Tagstore's database
        """
        entity = Entity.objects.create(entity_type='xblock', external_id='alpha')

        entity_out = EntitySerializer(entity).data
        self.assertDictEqual(entity_out, {
            "entity_type": "xblock",
            "external_id": "alpha",
        })

    def test_non_persisted_entity(self):
        """
        Test serializing an entity that does not exist in Tagstore's database
        """
        entity = Entity(entity_type='xblock', external_id='alpha')

        entity_out = EntitySerializer(entity).data
        self.assertDictEqual(entity_out, {
            "entity_type": "xblock",
            "external_id": "alpha",
        })


class EntityDetailSerializerTestCase(TestCase):
    """
    Test EntityDetailSerializer
    """

    def test_persisted_entity(self):
        """
        Test serializing an entity that exists in Tagstore's database
        """
        entity = Entity.objects.create(entity_type='xblock', external_id='alpha')
        taxonomy = Taxonomy.objects.create(name="Test Taxonomy")
        tag = taxonomy.add_tag("some tag")
        tag.add_to(entity.id)

        entity_out = EntityDetailSerializer(entity).data
        self.assertDictEqual(entity_out, {
            "entity_type": "xblock",
            "external_id": "alpha",
            "persisted": True,
            "tags": [
                {
                    "taxonomy_id": taxonomy.id,
                    "name": "some tag",
                    "path": f"{taxonomy.id}:some tag:",
                }
            ],
        })

    def test_non_persisted_entity(self):
        """
        Test serializing an entity that does not exist in Tagstore's database
        """
        entity = Entity(entity_type='xblock', external_id='alpha')

        entity_out = EntityDetailSerializer(entity).data
        self.assertDictEqual(entity_out, {
            "entity_type": "xblock",
            "external_id": "alpha",
            "persisted": False,
            "tags": [],
        })

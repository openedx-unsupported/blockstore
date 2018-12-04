""" Tests for api v1 serializers. """

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from tagstore.backends.tagstore_django.models import Entity

from ..serializers.entities import EntitySerializer, EntityTagSerializer


class SerializerBaseTestCase(TestCase):
    """
    Base class for serializer tests.
    """

    def setUp(self):

        super().setUp()

        self.request = APIRequestFactory().get('/')
        self.request.query_params = {}
        self.context = {
            'request': self.request
        }


class EntitySerializerTestCase(SerializerBaseTestCase):
    """
    Tests for the EntitySerializer
    """

    def test_entity_serializer_data(self):

        entity = Entity(
            entity_type='xblock',
            external_id='some-resource-uri',
        )

        entity_serializer = EntitySerializer(
            entity, context=self.context,
        )

        self.assertSequenceEqual(list(entity_serializer.data.keys()), [
            'id', 'entity_type', 'external_id',
        ])

        self.assertEqual(entity_serializer.data['entity_type'], 'xblock')
        self.assertEqual(entity_serializer.data['external_id'], 'some-resource-uri')


class EntityTagSerializerTestCase(TestCase):
    """
    Tests for the EntityTagSerializer
    """

    def setUp(self):

        super().setUp()

        self.entity_tags = {
            'tags': [
                {
                    'taxonomy_uid': 7,
                    'taxonomy_name': 'Subject Area',
                    'tag': 'Biochemistry'
                },
                {
                    'taxonomy_uid': 9,
                    'taxonomy_name': 'License',
                    'tag': 'CC-BY-SA-4.0'
                }
            ]
        }

    def test_entity_tag_serializer_data(self):

        entity_tag_serializer = EntityTagSerializer(
            self.entity_tags
        )

        self.assertSequenceEqual(list(entity_tag_serializer.data.keys()), ['tags'])
        self.assertSequenceEqual(list(entity_tag_serializer.data['tags'][0].keys()), [
            'taxonomy_uid', 'taxonomy_name', 'tag',
        ])

        self.assertEqual(entity_tag_serializer.data['tags'][0]['taxonomy_uid'], 7)
        self.assertEqual(entity_tag_serializer.data['tags'][0]['taxonomy_name'], 'Subject Area')

"""
Test the API views and URLs.
"""
import uuid
import ddt
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ...core.models import Tag, Unit, Pathway
from ..serializers import (
    TagSerializer,
    TagUnitsSerializer,
    UnitSerializer,
    UnitPathwaysSerializer,
    PathwaySerializer,
)


@ddt.ddt
class AnonymousAccessTest(TestCase):
    """
    As an anonymous user, I want to view all publicly accessible content on the platform.
    """
    fixtures = ['multiple_pathways']
    client = Client()

    def test_list_pathways(self):
        """Listing pathways is allowed to anonymous users."""
        pathways = Pathway.objects.all()
        url = reverse('api:v1:pathways')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = PathwaySerializer(pathways, many=True)
        self.assertEqual(response.data['results'], serialized.data)

        # Pathway units are present and properly sorted
        self.assertIn("units", response.data['results'][0])
        self.assertEqual(len(response.data['results'][0]['units']), 4)
        serialized = [UnitSerializer(unit).data for unit in pathways.first().units.all()]
        self.assertEqual(serialized, response.data['results'][0]['units'])

        # Pathway units' tags are present as expected
        self.assertIn("tags", response.data['results'][0])
        self.assertEqual(len(response.data['results'][0]['tags']), 7)
        serialized = [TagSerializer(tag).data for tag in pathways.first().tags.all()]
        self.assertEqual(serialized, response.data['results'][0]['tags'])

    def test_get_pathway(self):
        """Viewing a single pathway is allowed to anonymous users."""
        pathway = Pathway.objects.first()
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = PathwaySerializer(pathway)
        self.assertEqual(response.data, serialized.data)

        # Pathway units are present and properly sorted
        self.assertIn("units", response.data)
        self.assertEqual(len(response.data['units']), 4)
        serialized = [UnitSerializer(unit).data for unit in pathway.units.all()]
        self.assertEqual(serialized, response.data['units'])

        # Pathway units' tags are present as expected
        self.assertIn("tags", response.data)
        self.assertEqual(len(response.data['tags']), 7)
        serialized = [TagSerializer(tag).data for tag in pathway.tags.all()]
        self.assertEqual(serialized, response.data['tags'])

    @ddt.data(
        'put', 'patch', 'delete'
    )
    def test_modify_pathway_denied(self, http_method):
        """Modifying a pathway is denied to anonymous users."""
        pathway = Pathway.objects.first()
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = getattr(self.client, http_method)(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_pathway_denied(self):
        """Creating a pathway is denied to anonymous users."""
        url = reverse('api:v1:pathway.new')
        response = self.client.post(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_units(self):
        """Listing units is allowed to anonymous users."""
        units = Unit.objects.all()
        url = reverse('api:v1:units')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = UnitSerializer(units, many=True)
        self.assertEqual(response.data['results'], serialized.data)
        self.assertIn("tags", response.data['results'][0])

    def test_get_unit(self):
        """Viewing a single unit is allowed to anonymous users."""
        unit = Unit.objects.first()
        url = reverse('api:v1:unit', kwargs={'pk': unit.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = UnitSerializer(unit)
        self.assertEqual(response.data, serialized.data)
        self.assertIn("tags", response.data)

    @ddt.data(
        'put', 'patch', 'delete'
    )
    def test_modify_unit_denied(self, http_method):
        """Modifying a unit is denied to anonymous users."""
        unit = Unit.objects.first()
        url = reverse('api:v1:unit', kwargs={'pk': unit.id})
        response = getattr(self.client, http_method)(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_unit_denied(self):
        """Creating a unit is denied to anonymous users."""
        url = reverse('api:v1:unit.new')
        response = self.client.post(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_tag(self):
        """Viewing a single tag is allowed to anonymous users."""
        tag = Tag.objects.first()
        url = reverse('api:v1:tag', kwargs={'name': tag.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = TagSerializer(tag)
        self.assertEqual(response.data, serialized.data)

    def test_get_tag_units(self):
        """Viewing the units that contain a tag is allowed to anonymous users."""
        tag = Tag.objects.get(name='Microbiology')
        url = reverse('api:v1:tag.units', kwargs={'name': tag.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = TagUnitsSerializer(tag)
        self.assertEqual(response.data, serialized.data)
        self.assertIn("units", response.data)
        self.assertEqual(len(response.data["units"]), 6)

    @ddt.data(
        'put', 'patch', 'delete'
    )
    def test_modify_tag_denied(self, http_method):
        """Modifying a tag is denied to anonymous users."""
        tag = Tag.objects.first()
        url = reverse('api:v1:tag', kwargs={'name': tag.name})
        response = getattr(self.client, http_method)(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_tag_denied(self):
        """Creating a tag is denied to anonymous users."""
        url = reverse('api:v1:tag.new')
        response = self.client.post(
            url,
            data={'name': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@ddt.ddt
class DiscoverabilityTest(TestCase):
    """
    As a LabXchange educator, I want to be able to discover existing high-quality content (Learning Objects)
    (not covered) that exists in courses on edx.org and other Open edX sites
    and to offer it to students in new contexts like Pathways.
    """
    fixtures = ['multiple_pathways']
    client = Client()

    def test_get_unit_pathways(self):
        """Viewing the pathways that contain a unit is allowed to anonymous users."""
        unit = Unit.objects.get(id='c6283b14-56db-468c-a548-8c9a36165fef')
        url = reverse('api:v1:unit.pathways', kwargs={'pk': unit.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serialized = UnitPathwaysSerializer(unit)
        self.assertEqual(response.data, serialized.data)
        self.assertIn("pathways", response.data)
        self.assertEqual(len(response.data["pathways"]), 2)

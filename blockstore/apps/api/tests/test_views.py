"""
Test the API views and URLs.
"""
import uuid
import ddt
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ...core.models import Tag, Unit, Pathway, User
from ..serializers import (
    TagSerializer,
    TagUnitsSerializer,
    UnitSerializer,
    UnitPathwaysSerializer,
    PathwaySerializer,
)


class UserClientMixin(object):
    """Initializes a user on the class, and a client on the instance."""
    user = None
    username = 'user'
    password = 'password'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=cls.username)
        cls.user.set_password(cls.password)
        cls.user.save()

    def setUp(self):
        super().setUp()
        self.client = Client()

    def assert_login(self):
        """Ensure the user is logged in."""
        self.assertTrue(self.client.login(username=self.username, password=self.password))


@ddt.ddt
class AccessDeniedTest(UserClientMixin, TestCase):
    """
    As an anonymous user, I want to view all publicly accessible content on the platform.
    """
    fixtures = ['multiple_pathways']

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

    def test_create_pathway_denied(self):
        """Creating a pathway is denied to anonymous users."""
        url = reverse('api:v1:pathway.new')
        response = self.client.post(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @ddt.data(
        ('put', False),
        ('patch', False),
        ('delete', False),
        ('put', True),
        ('patch', True),
        ('delete', True),
    )
    @ddt.unpack
    def test_modify_pathway_denied(self, http_method, auth_user):
        """Modifying a pathway is denied to anonymous users and non-authors."""
        if auth_user:
            self.assert_login()
        else:
            self.client.logout()

        pathway = Pathway.objects.first()
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = getattr(self.client, http_method)(
            url,
            data={'uuid': uuid.uuid4()},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @ddt.data(
        ('post', False),
        ('post', True),
    )
    @ddt.unpack
    def test_add_pathway_units_denied(self, http_method, auth_user):
        """Adding pathway units is denied to anonymous users, and non-authors."""
        if auth_user:
            self.assert_login()
        else:
            self.client.logout()

        pathway = Pathway.objects.first()
        unit = Unit.objects.get(id='c6283b14-56db-468c-a548-8c9a36165fef')
        url = reverse('api:v1:pathway.unit')
        response = getattr(self.client, http_method)(
            url,
            data={
                'pathway': pathway.id,
                'unit': unit.id,
                'index': 99,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @ddt.data(
        ('post', False),
        ('post', True),
    )
    @ddt.unpack
    def test_add_pathway_tags_denied(self, http_method, auth_user):
        """Adding pathway tags is denied to anonymous users, and non-authors."""
        if auth_user:
            self.assert_login()
        else:
            self.client.logout()

        pathway = Pathway.objects.first()
        tag = Tag.objects.get(name='Laboratory basics')
        url = reverse('api:v1:pathway.tag')
        response = getattr(self.client, http_method)(
            url,
            data={
                'pathway': pathway.id,
                'tag': tag.id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_pathway_tag(self):
        """Logged-in users can add tags to the pathways they own."""
        self.assert_login()

        # Create a pathway
        url = reverse('api:v1:pathway.new')
        response = self.client.post(
            url,
            data={'author': self.user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # New pathway is owned by the user, no tags, no units.
        pathway = Pathway.objects.get(id=response.data['id'])
        self.assertEqual(pathway.author.id, self.user.id)
        self.assertEqual(list(pathway.tags.all()), [])
        self.assertEqual(list(pathway.units.all()), [])

        # Add an existing tag to the pathway
        url = reverse('api:v1:pathway.tag')
        tag = Tag.objects.get(name='Microbiology')
        response = self.client.post(
            url,
            data={
                'pathway': pathway.id,
                'tag': tag.id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], str(tag.id))
        self.assertIn("name", response.data)
        self.assertEqual(response.data["name"], tag.name)

    def test_get_tag_units(self):
        """Viewing the units that contain a tag is allowed to anonymous users."""
        tag = Tag.objects.get(name='Microbiology')
        url = reverse('api:v1:tag.units', kwargs={'name': tag.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["id"], str(tag.id))
        self.assertIn("name", response.data)
        self.assertEqual(response.data["name"], tag.name)
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
class DiscoverabilityTest(UserClientMixin, TestCase):
    """
    As a LabXchange educator, I want to be able to discover existing high-quality content (Learning Objects)
    (not covered) that exists in courses on edx.org and other Open edX sites
    and to offer it to students in new contexts like Pathways.
    """
    fixtures = ['multiple_pathways']

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

    def test_add_pathway_with_units(self):
        """Logged-in users can create pathways with units."""
        self.assert_login()

        # Create a pathway with units
        unit = Unit.objects.get(id='c6283b14-56db-468c-a548-8c9a36165fef')
        url = reverse('api:v1:pathway.new')
        response = self.client.post(
            url,
            data={
                'author': self.user.id,
                'units': [unit.id],
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # New pathway is owned by the user, and contains the expected unit(s) and tags
        pathway = Pathway.objects.get(id=response.data['id'])
        self.assertEqual(pathway.author.id, self.user.id)
        self.assertEqual(list(pathway.units.all()), [unit])
        self.assertEqual(list(pathway.tags.all()), list(unit.tags.all()))

    def test_add_pathway_with_tags(self):
        """Logged-in users can create pathways with tags."""
        self.assert_login()

        # Create a pathway with tags
        url = reverse('api:v1:pathway.new')
        tags = [
            Tag.objects.get(name='Microbiology'),
            Tag.objects.get(name='Case study'),
        ]
        response = self.client.post(
            url,
            data={
                'author': self.user.id,
                'tags': [tag.id for tag in tags],
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # New pathway is owned by the user, and contains no units, and the expected tags
        pathway = Pathway.objects.get(id=response.data['id'])
        self.assertEqual(pathway.author.id, self.user.id)
        self.assertEqual(list(pathway.units.all()), [])

        # Tags sorted by name
        self.assertEqual(list(pathway.tags.all()), list(reversed(tags)))

    @ddt.data(
        (None, 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
        ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', None),
        ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
        ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'c6283b14-56db-468c-a548-8c9a36165fef'),
        ('c6283b14-56db-468c-a548-8c9a36165fef', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
    )
    @ddt.unpack
    def test_add_unit_to_pathway_must_exist(self, unit_id, pathway_id):
        """The pathway must exist before we can add units to it."""
        self.assert_login()
        url = reverse('api:v1:pathway.unit')
        response = self.client.post(
            url,
            data={
                'pathway': pathway_id,
                'unit': unit_id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_unit_and_tags_to_pathway(self):
        """Logged-in users can add units and tags to the pathways they own."""
        self.assert_login()

        # Create a pathway
        url = reverse('api:v1:pathway.new')
        response = self.client.post(
            url,
            data={'author': self.user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # New pathway is owned by the user
        pathway = Pathway.objects.get(id=response.data['id'])
        self.assertEqual(pathway.author.id, self.user.id)

        # Retrieve the new pathway: it contains no units
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("units", response.data)
        self.assertEqual(len(response.data['units']), 0)

        # Add an existing unit to the pathway
        unit = Unit.objects.get(id='c6283b14-56db-468c-a548-8c9a36165fef')
        url = reverse('api:v1:pathway.unit')
        response = self.client.post(
            url,
            data={
                'pathway': pathway.id,
                'unit': unit.id,
                'index': 99,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Retrieve the updated pathway: it contains the added unit, and its tags
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("units", response.data)
        self.assertEqual(len(response.data['units']), 1)
        self.assertEqual(response.data['units'][0]['id'], str(unit.id))

        # Pathway units' tags are present as expected
        self.assertIn("tags", response.data)
        serialized = TagSerializer(unit.tags.all(), many=True).data
        self.assertEqual(serialized, response.data['tags'])

        # Add tags to pathway, adding one tag twice
        tags = list(unit.tags.all())
        video_tag = Tag.objects.get(name='Video')
        tags.append(video_tag)
        tags.append(Tag.objects.get(name='Microbiology'))
        self.assertEqual(len(tags), 4)
        self.assertEqual(tags.count(video_tag), 2)
        url = reverse('api:v1:pathway.tag')
        for tag in tags:
            response = self.client.post(
                url,
                data={
                    'pathway': pathway.id,
                    'tag': tag.id,
                }
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Retrieve the updated pathway: it contains the unit's + added tags, de-duplicated, and sorted
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tags", response.data)
        self.assertEqual(len(response.data['tags']), 3)
        self.assertEqual(response.data['tags'][0]['name'], 'Laboratory basics')
        self.assertEqual(response.data['tags'][1]['name'], 'Microbiology')
        self.assertEqual(response.data['tags'][2]['name'], 'Video')


class PathwayTaggingTest(UserClientMixin, TestCase):
    """
    As a LabXchange educator, I want to be able to tag pathways with topics, learning outcomes, etc. to enable other
    educators and students to find and use my work.
    """
    fixtures = ['multiple_pathways']

    def test_add_tag_to_pathway(self):
        """Logged-in users can add tags to the pathways they own."""
        self.assert_login()

        # Create a pathway
        url = reverse('api:v1:pathway.new')
        response = self.client.post(
            url,
            data={'author': self.user.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # New pathway is owned by the user, no tags, no units.
        pathway = Pathway.objects.get(id=response.data['id'])
        self.assertEqual(pathway.author.id, self.user.id)
        self.assertEqual(list(pathway.tags.all()), [])
        self.assertEqual(list(pathway.units.all()), [])

        # Add an existing tag to the pathway
        url = reverse('api:v1:pathway.tag')
        tag = Tag.objects.get(name='Microbiology')
        response = self.client.post(
            url,
            data={
                'pathway': pathway.id,
                'tag': tag.id,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Retrieve the updated pathway: it contains the added tag
        url = reverse('api:v1:pathway', kwargs={'pk': pathway.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tags", response.data)
        self.assertEqual(len(response.data['tags']), 1)
        self.assertEqual(response.data['tags'][0]['id'], str(tag.id))
        self.assertEqual(response.data['tags'][0]['name'], tag.name)

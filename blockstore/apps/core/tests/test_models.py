""" Tests for core models. """

from django.test import TestCase
from django_dynamic_fixture import G
from social_django.models import UserSocialAuth

from ...core.models import User, Tag, Unit, Pathway, PathwayUnit, PathwayTag


class UserTests(TestCase):
    """ User model tests. """
    TEST_CONTEXT = {'foo': 'bar', 'baz': None}

    def test_access_token(self):
        user = G(User)
        self.assertIsNone(user.access_token)

        social_auth = G(UserSocialAuth, user=user)
        self.assertIsNone(user.access_token)

        access_token = 'My voice is my passport. Verify me.'
        social_auth.extra_data['access_token'] = access_token
        social_auth.save()
        self.assertEqual(user.access_token, access_token)

    def test_get_full_name(self):
        """ Test that the user model concatenates first and last name if the full name is not set. """
        full_name = 'George Costanza'
        user = G(User, full_name=full_name)
        self.assertEqual(user.get_full_name(), full_name)

        first_name = 'Jerry'
        last_name = 'Seinfeld'
        user = G(User, full_name=None, first_name=first_name, last_name=last_name)
        expected = '{first_name} {last_name}'.format(first_name=first_name, last_name=last_name)
        self.assertEqual(user.get_full_name(), expected)

        user = G(User, full_name=full_name, first_name=first_name, last_name=last_name)
        self.assertEqual(user.get_full_name(), full_name)

    def test_string(self):
        """Verify that the model's string method returns the user's full name."""
        full_name = 'Bob'
        user = G(User, full_name=full_name)
        self.assertEqual(str(user), full_name)


class ModelTest(TestCase):
    """Test the model's string and fields."""
    fixtures = ['multiple_pathways']

    def test_first_pathway(self):
        pathway = Pathway.objects.first()
        self.assertEqual(str(pathway), "Pathway: Three Steps of PCR")
        self.assertEqual(str(pathway.first_unit), "Three Steps of PCR")

    def test_last_pathway(self):
        pathway = Pathway.objects.last()
        self.assertEqual(str(pathway), "Pathway: Separating DNA with Gel Electrophoresis")

    def test_pathway_summary(self):
        pathway = Pathway.objects.first()
        self.assertEqual(pathway.summary, "Simulation")

    def test_pathway_tags(self):
        pathway = Pathway.objects.first()
        self.assertEqual(
            [str(tag) for tag in pathway.tags],
            ['ABE',
             'Colony PCR',
             'Laboratory basics',
             'Microbiology',
             'PCR',
             'Tools',
             'Video'])

    def test_first_unit(self):
        unit = Unit.objects.first()
        self.assertEqual(str(unit), "Intro to PCR")

    def test_last_unit(self):
        unit = Unit.objects.last()
        self.assertEqual(str(unit), "DNA Sequencing")

    def test_first_pathway_unit(self):
        pathway_unit = PathwayUnit.objects.first()
        self.assertEqual(str(pathway_unit), "Pathway: Three Steps of PCR[1] -> Laboratory basics")

    def test_last_pathway_unit(self):
        pathway_unit = PathwayUnit.objects.last()
        self.assertEqual(str(pathway_unit), "Pathway: Intro to PCR[11] -> Three Steps of PCR")

    def test_first_pathway_tag(self):
        pathway_tag = PathwayTag.objects.first()
        self.assertEqual(str(pathway_tag), "Pathway: Intro to PCR -> Laboratory basics")

    def test_last_pathway_tag(self):
        pathway_tag = PathwayTag.objects.last()
        self.assertEqual(str(pathway_tag), "Pathway: Intro to PCR -> PCR")

    def test_first_tag(self):
        tag = Tag.objects.first()
        self.assertEqual(str(tag), "ABE")

    def test_last_tag(self):
        tag = Tag.objects.last()
        self.assertEqual(str(tag), "Video")

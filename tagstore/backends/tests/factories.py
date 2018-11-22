""" Factories for tagstore models. """

import factory

from tagstore.backends.tagstore_django.models import Entity, Tag, Taxonomy


class EntityFactory(factory.DjangoModelFactory):

    class Meta:
        model = Entity


class TagFactory(factory.DjangoModelFactory):

    class Meta:
        model = Tag


class TaxonomyFactory(factory.DjangoModelFactory):

    class Meta:
        model = Taxonomy

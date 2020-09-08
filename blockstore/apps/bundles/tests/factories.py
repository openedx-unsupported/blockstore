""" Factories for bundle models. """
# Not in the main package list, and not named the same as the requirement besides.
import factory  # pylint: disable=import-error

from ..store import FileInfo
from ..models import Bundle, BundleVersion, Collection


class BundleFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Bundle


class BundleVersionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = BundleVersion


class CollectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Collection


class FileInfoFactory(factory.Factory):

    class Meta:
        model = FileInfo

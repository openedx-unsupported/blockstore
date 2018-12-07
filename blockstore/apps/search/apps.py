""" AppConfig for search app. """

from django.apps import AppConfig
from django.conf import settings
from elasticsearch_dsl import connections, Index

from .documents import BlockDocument


class SearchConfig(AppConfig):

    name = 'blockstore.apps.search'
    verbose_name = 'Blockstore Search'

    def ready(self):

        # Create the ElasticSearch connections.
        connections.configure(**settings.ELASTICSEARCH)

        index = Index('blocks')
        index.document(BlockDocument)
        BlockDocument._index = index  # pylint: disable=protected-access

        # Create the BlockDocument index and mappings.
        # TODO: This will need to be done in a migration.
        index.save()

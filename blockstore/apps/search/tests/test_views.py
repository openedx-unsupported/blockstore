""" Tests for views. """

from elasticsearch.exceptions import NotFoundError
import pytest

from ..core.tests.test_base import ViewsBaseTestCase
from ..documents import BlockDocument
from ..fieldsets import (
    SummaryFieldSet,
)


class BlockDocumentsViewSetTestCase(ViewsBaseTestCase):
    """ Tests for BlockDocumentsViewSet. """

    document_class = BlockDocument

    list_path = 'api:v1:index-blocks-list'
    detail_path = 'api:v1:index-blocks-detail'

    def test_list(self):

        response = self.response(self.list_path)
        self.assertEqual(response.data['results'], [])

        titles = {'Video 1', 'Video 2', 'Video 3'}
        for title in titles:
            document = BlockDocument(summary=SummaryFieldSet.Document(title=title))
            document.save(refresh=True)

        response = self.response(self.list_path)
        self.assertEqual(len(response.data['results']), 3)
        self.assertSetEqual(titles, {document['summary']['title'] for document in response.data['results']})

    def test_get(self):
        document = BlockDocument(summary=SummaryFieldSet.Document(title='Block to get'))
        document.save(refresh=True)

        self.assertEqual(BlockDocument.get(document.uuid).summary.title, 'Block to get')

        response = self.response(self.detail_path, kwargs={'uuid': document.uuid})
        self.assertDictEqual(response.data, {
            'analytics': {'favorites': None, 'remixes': None, 'views': None},
            'authorship': {'author_ids': []},
            'entity': {'type': None, 'id': None},
            'ownership': {'org_id': None},
            'summary': {'title': 'Block to get', 'description': None, 'image': None},
            'tags': {'paths': []},
            'url': 'http://testserver/api/v1/index/blocks/{}'.format(document.uuid),
            'uuid': str(document.uuid),
        })

    def test_create(self):

        response = self.response(self.list_path)
        self.assertEqual(response.data['results'], [])

        response = self.response(
            self.list_path,
            method='post',
            data={
                'summary': {
                    'title': 'Block created',
                },
            },
            format='json',
            expected_response_code=201,
        )

        document = BlockDocument.get(response.data['uuid'])
        self.assertEqual(document.summary.title, 'Block created')

    def test_update(self):

        self.maxDiff = None

        document = BlockDocument(summary=SummaryFieldSet.Document(title='Block to update'))
        document.save(refresh=True)

        self.assertEqual(BlockDocument.get(document.uuid).summary.title, 'Block to update')

        # Add some data
        self.response(
            self.detail_path,
            method='patch',
            kwargs={'uuid': str(document.uuid)},
            data={
                'analytics': {'favorites': 3},
                'authorship': {'author_ids': ['The only author']},
                'entity': {'type': 'xblock', 'id': 'block-v1:Blockstore+Course+type@video+block@0eae35c'},
                'ownership': {'org_id': "Blockstore"},
                'summary': {
                    'title': 'Block updated',
                    'description': 'After the block is added it is indexed.',
                    'image': 'https://storage.com/block.png',
                },
            },
            format='json',
            expected_response_code=200,
        )

        response = self.response(self.detail_path, kwargs={'uuid': document.uuid})
        self.assertDictEqual(response.data, {
            'analytics': {'favorites': 3, 'remixes': None, 'views': None},
            'authorship': {'author_ids': ['The only author']},
            'entity': {'type': 'xblock', 'id': 'block-v1:Blockstore+Course+type@video+block@0eae35c'},
            'ownership': {'org_id': "Blockstore"},
            'summary': {
                'title': 'Block updated',
                'description': 'After the block is added it is indexed.',
                'image': 'https://storage.com/block.png',
            },
            'tags': {'paths': []},
            'url': 'http://testserver/api/v1/index/blocks/{}'.format(document.uuid),
            'uuid': str(document.uuid),
        })

        # Update the tags field.
        self.response(
            self.detail_path,
            method='patch',
            kwargs={'uuid': str(document.uuid)},
            data={
                'tags': {
                    'paths': ['tag1', 'tag2', 'tag3']
                }
            },
            format='json',
            expected_response_code=200,
        )

        response = self.response(self.detail_path, kwargs={'uuid': document.uuid})
        self.assertDictEqual(response.data, {
            'analytics': {'favorites': 3, 'remixes': None, 'views': None},
            'authorship': {'author_ids': ['The only author']},
            'entity': {'type': 'xblock', 'id': 'block-v1:Blockstore+Course+type@video+block@0eae35c'},
            'ownership': {'org_id': "Blockstore"},
            'summary': {
                'title': 'Block updated',
                'description': 'After the block is added it is indexed.',
                'image': 'https://storage.com/block.png',
            },
            'tags': {'paths': ['tag1', 'tag2', 'tag3']},
            'url': 'http://testserver/api/v1/index/blocks/{}'.format(document.uuid),
            'uuid': str(document.uuid),
        })

        # Set a nested field.
        self.response(
            self.detail_path,
            method='patch',
            kwargs={'uuid': str(document.uuid)},
            data={
                'analytics': {'remixes': 3},
            },
            format='json',
            expected_response_code=200,
        )

        response = self.response(self.detail_path, kwargs={'uuid': document.uuid})
        self.assertDictEqual(response.data, {
            'analytics': {'favorites': 3, 'remixes': 3, 'views': None},
            'authorship': {'author_ids': ['The only author']},
            'entity': {'type': 'xblock', 'id': 'block-v1:Blockstore+Course+type@video+block@0eae35c'},
            'ownership': {'org_id': "Blockstore"},
            'summary': {
                'title': 'Block updated',
                'description': 'After the block is added it is indexed.',
                'image': 'https://storage.com/block.png',
            },
            'tags': {'paths': ['tag1', 'tag2', 'tag3']},
            'url': 'http://testserver/api/v1/index/blocks/{}'.format(document.uuid),
            'uuid': str(document.uuid),
        })

        # Update a nested field.
        self.response(
            self.detail_path,
            method='patch',
            kwargs={'uuid': str(document.uuid)},
            data={
                'summary': {'image': 'https://storage.com/block2.png'},
            },
            format='json',
            expected_response_code=200,
        )

        response = self.response(self.detail_path, kwargs={'uuid': document.uuid})
        self.assertDictEqual(response.data, {
            'analytics': {'favorites': 3, 'remixes': 3, 'views': None},
            'authorship': {'author_ids': ['The only author']},
            'entity': {'type': 'xblock', 'id': 'block-v1:Blockstore+Course+type@video+block@0eae35c'},
            'ownership': {'org_id': "Blockstore"},
            'summary': {
                'title': 'Block updated',
                'description': 'After the block is added it is indexed.',
                'image': 'https://storage.com/block2.png',
            },
            'tags': {'paths': ['tag1', 'tag2', 'tag3']},
            'url': 'http://testserver/api/v1/index/blocks/{}'.format(document.uuid),
            'uuid': str(document.uuid),
        })

        # Update a nested field.
        self.response(
            self.detail_path,
            method='patch',
            kwargs={'uuid': str(document.uuid)},
            data={
                'summary': {'image': 'Not a url'},
            },
            format='json',
            expected_response_code=400,
        )

    def test_delete(self):

        document = BlockDocument(summary=SummaryFieldSet.Document(title='Block to be deleted'))
        document.save(refresh=True)

        self.assertEqual(BlockDocument.get(document.uuid).summary.title, 'Block to be deleted')

        self.response(self.detail_path, kwargs={'uuid': document.uuid}, expected_response_code=200)
        self.response(self.detail_path, kwargs={'uuid': document.uuid}, method='delete', expected_response_code=204)
        self.response(self.detail_path, kwargs={'uuid': document.uuid}, expected_response_code=404)

        with pytest.raises(NotFoundError):
            BlockDocument.get(document.uuid)

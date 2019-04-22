"""
An API client for use in Tagstore tests

Note: Carefully read the module docstring in test_contract.py before
making any changes to this file. This API client should be relatively
"dumb", and any changes to it must be checked to ensure they are not
breaking backwards-compatibility.
"""
from urllib.parse import quote

from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

V1_API = '/tagstore/api/v1'


class TagstoreAPIClient(APIClient):
    """
    Simple API Test Client for Tagstore

    Automatically checks the response's status code, and returns the data directly.
    """
    def handle_response(self, response: Response, expect=None, data_only=True):
        """
        Given an API response, verify its status code and return its JSON body data.
        """
        if expect is not None:
            if response.status_code != expect:
                msg = f"Unexpected status code {response.status_code} (expected {expect})"
                if hasattr(response, 'data'):
                    msg += f":\n{response.data}"
                raise Exception(msg)
        return response.data if data_only else response

    def get(self, *args, expect=status.HTTP_200_OK, data_only=True, **kwargs):  # pylint: disable=arguments-differ
        return self.handle_response(super().get(*args, **kwargs), expect, data_only)

    def post(self, *args, expect=status.HTTP_200_OK, data_only=True, **kwargs):  # pylint: disable=arguments-differ
        return self.handle_response(super().post(*args, **kwargs), expect, data_only)

    def delete(self, *args, expect=status.HTTP_200_OK, data_only=True, **kwargs):  # pylint: disable=arguments-differ
        return self.handle_response(super().delete(*args, **kwargs), expect, data_only)

    # Specific API methods follow:

    def list_taxonomies(self):
        return self.get(f'{V1_API}/taxonomies')

    def get_taxonomy(self, taxonomy_id: int, **kwargs):
        return self.get(f'{V1_API}/taxonomies/{taxonomy_id}', **kwargs)

    def create_taxonomy(self, data: dict):
        return self.post(f'{V1_API}/taxonomies', data, format='json')

    def delete_taxonomy(self, taxonomy_id: int):
        return self.delete(f'{V1_API}/taxonomies/{taxonomy_id}')

    def get_taxonomy_tags(self, taxonomy_id: int):
        return self.get(f'{V1_API}/taxonomies/{taxonomy_id}/tags')

    def get_taxonomy_tag(self, taxonomy_id: int, name: str, **kwargs):
        return self.get(f'{V1_API}/taxonomies/{taxonomy_id}/tags/{quote(name)}', **kwargs)

    def add_taxonomy_tag(self, taxonomy_id: int, data: dict, **kwargs):
        return self.post(f'{V1_API}/taxonomies/{taxonomy_id}/tags', data, **kwargs)

    def delete_taxonomy_tag(self, taxonomy_id: int, name: str):
        return self.delete(f'{V1_API}/taxonomies/{taxonomy_id}/tags/{quote(name)}')

    def get_entity(self, entity_type: str, external_id: str):
        return self.get(f'{V1_API}/entities/{entity_type}/{quote(external_id)}')

    def entity_has_tag(self, entity_type: str, external_id: str, taxonomy_id: int, name: str, **kwargs):
        return self.get(
            f'{V1_API}/entities/{entity_type}/{quote(external_id)}/tags/{taxonomy_id}/{quote(name)}',
            **kwargs,
        )

    def entity_add_tag(self, entity_type: str, external_id: str, taxonomy_id: int, name: str, **kwargs):
        return self.post(
            f'{V1_API}/entities/{entity_type}/{quote(external_id)}/tags/{taxonomy_id}/{quote(name)}',
            **kwargs,
        )

    def entity_remove_tag(self, entity_type: str, external_id: str, taxonomy_id: int, name: str):
        return self.delete(
            f'{V1_API}/entities/{entity_type}/{quote(external_id)}/tags/{taxonomy_id}/{quote(name)}',
        )

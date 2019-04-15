"""
A Customization for the OpenAPI Schema Generator

We override get_tags so that the API spec file will use "blockstore_api" and
"tagstore_api" as the names of each part of the API, instead of "api_api".
"""
from drf_yasg.inspectors.view import SwaggerAutoSchema


class BlockstoreAutoSchema(SwaggerAutoSchema):
    """
    Custom schema generation class for Blockstore
    """
    def get_tags(self, operation_keys):
        """
        Get a list of tags for this operation.
        Tags determine how operations relate with each other, and in the UI and
        auto-generated API clients, the endpoints with each tag will be grouped
        together (in the API clients, each tag becomes a class).

        e.g. "tagstore" tag will give a class called "TagstoreApi" in any API
        client auto-generated from the spec file.
        """
        tags = self.overrides.get('tags')
        if not tags:
            default_tag = operation_keys[0]
            if default_tag == "api":
                default_tag = "blockstore"
            tags = [default_tag]
        return tags

    def get_operation_id(self, operation_keys):
        """
        Return an unique ID for this operation. The ID must be unique across
        all operations in the API.

        operation_keys is an array of the python path parts for the operation.
        """
        operation_id = self.overrides.get('operation_id', '')
        if not operation_id:
            # Strip out parts of the operation ID we don't need:
            operation_keys = [key for key in operation_keys if key not in (
                'api',
                'tagstore',
                'v1',
            )]
            operation_id = '_'.join(operation_keys)
        return operation_id

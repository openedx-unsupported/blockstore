"""
A Customization for the OpenAPI Schema Generator

We override get_tags so that the API spec file will use "blockstore_api" and
"tagstore_api" as the names of each part of the API, instead of "api_api".
"""
from functools import wraps

from drf_yasg.inspectors.view import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response


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

    def is_list_view(self):
        """
        Determine whether this view is a list or a detail view. We override to
        ensure that TaxonomyViewSet.tags() is marked as using pagination.
        """
        if self.path.endswith('/taxonomies/{id}/tags'):
            return True
        return super().is_list_view()


def api_method(
    response_serializer: serializers.Serializer,
    function_view_methods=None,
    response_status_code=200,
    **kwargs
):
    """
    Wrapper for our APIs endpoint view methods, to declare request/response data
    types and add automatic validation using Django Rest Framework Serializers.

    The primary purpose of this is to make it easy to specify the shape of the
    API response, _and_ to forcibly validate that the API implementation returns
    data in that same shape (via the serializer's validation).

    To specify the types of input arguments, path parameters, etc., pass any
    kwargs that @swagger_auto_schema accepts, e.g. `manual_parameters`,
    `method`, `operation_id`, `request_body`, etc.

    If you are wrapping a function-based view (as opposed to a ViewSet view),
    you must set function_view_methods=['GET', ...], in order to apply the
    DRF @api_view decorator.
    """
    def wrap(api_view_fn):
        """ Wrap a specific method as described above """
        @wraps(api_view_fn)
        def wrapper(*args, **kwds):  # pylint: disable=missing-docstring
            # Call the actual view function and get the result
            return_value = api_view_fn(*args, **kwds)
            # Now convert the result:
            serialized_data = response_serializer.to_representation(return_value)
            # And then convert to an actual JSON+HTTP response
            return Response(serialized_data)

        wrapped_view = wrapper
        # If it's a function-based view, we need to also apply the @api_view() decorator,
        # before we apply the @swagger_auto_schema decorator, but after we convert the
        # return value into a Response.
        if function_view_methods is not None:
            wrapped_view = api_view(function_view_methods)(wrapped_view)

        # Tell the OpenAPI generator that our API returns responses with the data
        # types defined by `response_serializer`
        return swagger_auto_schema(responses={response_status_code: response_serializer}, **kwargs)(wrapped_view)
    return wrap

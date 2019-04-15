"""
Test the OpenApi spec generation.
"""
import os

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO


class TestOpenAPISpec(TestCase):

    def test_generate_swagger_output_matches_committed_spec(self):
        """
        Test that the committed spec matches the current state of the views.

        If this test fails, you need to regenerate the OpenAPI spec.
        """
        spec_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '../../../../api-spec.yaml',
        )
        with open(spec_path) as file:
            committed_spec = file.read()
            out = StringIO()
            call_command(
                'generate_swagger',
                '--format=yaml',
                stdout=out,
            )
            generated_spec = out.getvalue()
            self.assertIn("swagger: '2.0'", generated_spec)
            self.assertEqual(
                committed_spec, generated_spec,
                """
                The API spec file (api-spec.yaml) does not match the current
                state of the API in the python code. To update it, run:
                    make generate_openapi_spec
                """
            )

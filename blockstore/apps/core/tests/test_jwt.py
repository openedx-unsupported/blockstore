"""
Tests for the JWT sanity check.
Checking edx-drf-extensinos method.
Checking jwt.encode and jwt.decode methods.
"""
from time import time
from django.test import TestCase

import jwt
from auth_backends.tests.test_backends import EdXOAuth2Tests
from django.contrib.auth import get_user_model
from edx_rest_framework_extensions.auth.jwt.decoder import jwt_decode_handler  # pylint: disable=import-error
from edx_rest_framework_extensions.auth.jwt.tests.utils import (    # pylint: disable=import-error
    generate_jwt_token, generate_latest_version_payload
)

User = get_user_model()


def get_jwt_payload():
    """ Returns a JWT payload with the necessary claims to create a new user. """
    email = 'gcostanza@gmail.com'
    username = 'gcostanza'
    payload = dict({'preferred_username': username, 'email': email})

    return payload


class Oauth2Tests(EdXOAuth2Tests):       # pylint: disable=test-inherits-tests
    """Running EdXOAuth2Tests here."""


class JWTDecodeHandlerTests(TestCase):
    """ Tests for the `jwt_decode_handler` utility function. """

    def test_success(self):
        """
        Confirms that the format of the valid response from the token decoder matches the payload
        """
        user = User.objects.create(username='test-service-user')
        payload = generate_latest_version_payload(user)
        jwt_tk = generate_jwt_token(payload)
        self.assertDictEqual(jwt_decode_handler(jwt_tk), payload)

    def test_encode_decode(self):
        """
        This test checking directly jwt.encode and jwt.decode methods.
        """
        now = int(time())
        payload = {
            "iss": 'test-issue',
            "aud": 'test-audience',
            "exp": now + 10,
            "iat": now,
            "username": 'staff',
            "email": 'staff@example.com',
        }
        secret = 'test-secret'
        jwt_message = jwt.encode(payload, secret)
        decoded_payload = jwt.decode(jwt_message, secret, verify=False)

        assert payload == decoded_payload

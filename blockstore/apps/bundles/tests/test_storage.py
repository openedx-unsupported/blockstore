"""
Tests for storage classes in storage.py
"""
from unittest.mock import patch

from django.test import override_settings
import pytest

from .. import storage as storage_module


class _MockS3backend:
    """
    A fake replacment for S3Boto3Backend in these tests.
    """
    def __init__(self, **settings):
        self.accesss_key = settings["access_key"]
        self.secret_key = settings["secret_key"]

    def url(self, name):
        return f"https://example.com/s3/{name}"


_patch_default_storage = patch.object(
    storage_module, 'default_storage', autospec=True
)
_patch_get_storage_class = patch.object(
    storage_module, 'get_storage_class', autospec=True, return_value=_MockS3backend
)
_patch_s3_credentials = override_settings(
    BUNDLE_ASSET_URL_STORAGE_KEY="a-key", BUNDLE_ASSET_URL_STORAGE_SECRET="a-secret"
)


@_patch_default_storage
def test_asset_storage_long_lived_urls_disabled(mock_default_storage):
    """
    Test that `AssetStorage` is just pass-through when long-lived S3
    URL signing is not configured.
    """
    backend = storage_module.AssetStorage()
    assert backend.url_backend is mock_default_storage
    backend.url('abc')
    backend.listdir('123')
    backend.get_accessed_time('xyz')
    mock_default_storage.url.assert_called_once_with('abc')
    mock_default_storage.listdir.assert_called_once_with('123')
    mock_default_storage.get_accessed_time.assert_called_once_with('xyz')


@_patch_s3_credentials
@_patch_get_storage_class
@_patch_default_storage
def test_asset_storage_long_lived_urls_enabled(mock_default_storage, *_args):
    """
    Test that `AssetStorage` is just pass-through when long-lived S3
    URL signing is not configured.
    """
    backend = storage_module.AssetStorage()
    assert isinstance(backend.url_backend, storage_module.LongLivedSignedUrlStorage)
    assert backend.url_backend.s3_backend.accesss_key == "a-key"
    assert backend.url_backend.s3_backend.secret_key == "a-secret"
    assert backend.url('abc') == "https://example.com/s3/abc"
    backend.listdir('123')
    backend.get_accessed_time('xyz')
    assert not mock_default_storage.url.called
    mock_default_storage.listdir.assert_called_once_with('123')
    mock_default_storage.get_accessed_time.assert_called_once_with('xyz')


@_patch_default_storage
def test_long_lived_url_storage_raises_if_no_boto3(*_args):
    """
    Test that `AssetStorage` is just pass-through when long-lived S3
    URL signing is not configured.
    """
    with pytest.raises(storage_module.LongLivedSignedUrlStorage.BackendNotAvailable):
        storage_module.LongLivedSignedUrlStorage()


@_patch_get_storage_class
@_patch_default_storage
def test_long_lived_url_storage_raises_if_no_credentials(*_args):
    """
    Test that `AssetStorage` is just pass-through when long-lived S3
    URL signing is not configured.
    """
    with pytest.raises(storage_module.LongLivedSignedUrlStorage.BackendNotAvailable):
        storage_module.LongLivedSignedUrlStorage()

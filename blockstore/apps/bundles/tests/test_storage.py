"""
Tests for storage classes in storage.py
"""
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.test import override_settings
import pytest

from .. import storage as storage_module


class _MockS3backend:
    """
    A fake replacment for S3Boto3Backend in these tests.
    """
    def __init__(self, **kwargs):
        self.access_key = kwargs.get("access_key", getattr(settings, 'AWS_S3_ACCESS_KEY_ID', None))
        self.secret_key = kwargs.get("secret_key", getattr(settings, 'AWS_S3_SECRET_ACCESS_KEY', None))
        self.bucket_name = kwargs.get("bucket_name", getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None))
        self.location = kwargs.get("location", getattr(settings, 'AWS_LOCATION', None))

    def url(self, name):
        return f"https://{self.bucket_name}/{self.location}{name}"


def get_storage_class(class_name):
    """
    Returns the MockS3Backend if S3Boto3Storage requested,
    or a mock class spec'd on default_storage for any other class name.
    """
    if class_name == 'storages.backends.s3boto3.S3Boto3Storage':
        return _MockS3backend
    return MagicMock(spec=storage_module.default_storage).__class__


_patch_default_storage = patch.object(
    storage_module, 'default_storage', autospec=True
)
_patch_get_storage_class = patch.object(
    storage_module, 'get_storage_class', autospec=True, side_effect=get_storage_class
)
_patch_storage_class = override_settings(
    AWS_LOCATION="s3/",
    AWS_STORAGE_BUCKET_NAME="example-bucket",
    AWS_S3_ACCESS_KEY_ID="another_key",
    AWS_S3_SECRET_ACCESS_KEY="another_secret",
    BUNDLE_ASSET_URL_STORAGE_KEY="a-key",
    BUNDLE_ASSET_URL_STORAGE_SECRET="a-secret",
    BUNDLE_ASSET_STORAGE_SETTINGS={
        'STORAGE_CLASS': 'storages.backends.s3boto3.S3Boto3Storage',
    },
)
_patch_s3_long_lived_credentials = override_settings(
    BUNDLE_ASSET_URL_STORAGE_KEY="a-key", BUNDLE_ASSET_URL_STORAGE_SECRET="a-secret",
    BUNDLE_ASSET_STORAGE_SETTINGS={
        'STORAGE_CLASS': 'storages.backends.some.other.backend',
        'STORAGE_KWARGS': {
            'bucket_name': 'example-bucket',
            'location': 's3/',
            'access_key': 'another_key',
            'secret_key': 'another_secret',
        },
    },
)
_patch_s3_credentials = override_settings(
    BUNDLE_ASSET_STORAGE_SETTINGS={
        'STORAGE_CLASS': 'storages.backends.some.other.backend',
        'STORAGE_KWARGS': {
            'bucket_name': 'example-bucket',
            'location': 's3/',
            'access_key': 'another_key',
            'secret_key': 'another_secret',
        },
    },
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


@_patch_storage_class
@_patch_get_storage_class
@_patch_default_storage
def test_asset_storage_class(mock_default_storage, *_args):
    """
    Test that overriding the storage class works without the optional setting storage kwargs.
    """
    backend = storage_module.AssetStorage()
    assert isinstance(backend.url_backend, storage_module.LongLivedSignedUrlStorage)
    assert backend.url_backend.s3_backend.access_key == "a-key"
    assert backend.url_backend.s3_backend.secret_key == "a-secret"
    assert backend.url_backend.s3_backend.bucket_name == "example-bucket"
    assert backend.url_backend.s3_backend.location == "s3/"
    assert backend.asset_backend.access_key == "another_key"
    assert backend.asset_backend.secret_key == "another_secret"
    assert backend.asset_backend.bucket_name == "example-bucket"
    assert backend.asset_backend.location == "s3/"
    assert backend.url('abc') == "https://example-bucket/s3/abc"
    assert not mock_default_storage.url.called


@_patch_s3_long_lived_credentials
@_patch_get_storage_class
@_patch_default_storage
def test_asset_storage_long_lived_urls_enabled(mock_default_storage, *_args):
    """
    Test that `AssetStorage` is just pass-through when long-lived S3
    URL signing is not configured.
    """
    backend = storage_module.AssetStorage()
    assert isinstance(backend.url_backend, storage_module.LongLivedSignedUrlStorage)
    assert backend.url_backend.s3_backend.access_key == "a-key"
    assert backend.url_backend.s3_backend.secret_key == "a-secret"
    assert backend.url_backend.s3_backend.bucket_name == "example-bucket"
    assert backend.url_backend.s3_backend.location == "s3/"
    assert backend.asset_backend.access_key == "another_key"
    assert backend.asset_backend.secret_key == "another_secret"
    assert backend.asset_backend.bucket_name == "example-bucket"
    assert backend.asset_backend.location == "s3/"
    assert backend.url('abc') == "https://example-bucket/s3/abc"
    backend.listdir('123')
    backend.get_accessed_time('xyz')
    assert not mock_default_storage.url.called
    backend.asset_backend.listdir.assert_called_once_with('123')
    backend.asset_backend.get_accessed_time.assert_called_once_with('xyz')


@_patch_s3_credentials
@_patch_get_storage_class
@_patch_default_storage
def test_asset_storage_basic_s3(mock_default_storage, *_args):
    """
    Test that `AssetStorage` is configured as expected when there's no long-lived URL signing credentials configured.
    """
    backend = storage_module.AssetStorage()
    assert backend.url_backend is backend.asset_backend
    assert backend.asset_backend.access_key == "another_key"
    assert backend.asset_backend.secret_key == "another_secret"
    assert backend.asset_backend.bucket_name == "example-bucket"
    assert backend.asset_backend.location == "s3/"
    backend.url('abc')
    backend.listdir('123')
    backend.get_accessed_time('xyz')
    assert not mock_default_storage.url.called
    backend.asset_backend.listdir.assert_called_once_with('123')
    backend.asset_backend.get_accessed_time.assert_called_once_with('xyz')


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

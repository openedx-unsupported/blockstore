"""
Django Storage backends for bundles app.

If you don't care about the specifics, just import and use `default_asset_storage`,
which is a `Storage` instance just like `default_storage`.
"""
from django.conf import settings
from django.core.files.storage import Storage, default_storage, get_storage_class


# You probably just want to import this.
# (Forward-declaring here for visibility)
default_asset_storage: Storage


class LongLivedSignedUrlStorage(Storage):  # pylint: disable=abstract-method
    """
    Storage backend for generating longer-lived signed URLs.

    It only implements the `url` operation; all other operations (delete,
    exists, listdir, etc.) will raise NotImplementedErrors.
    This is why we disable pylint's abstract method check for this class.

    THIS CLASS IS SPECIFIC TO THE S3Boto3Storage BACKEND.
    It will not work with FileSystemStorage or any other backend.
    (If it seemed prudent, though, this class could be generalized to work
     with other storage backends.)

    Context:

        When powering Blockstore with the S3SBoto3torageBackend, asset URLs are
        exposed to clients (and users) by generating signed S3 URLs.
        The ideal time-to-live of these URLs is ~24-48 hours;
        that is, long enough such that users may interact with content without
        losing access to assets in the middle of their session,
        but short enough as to avoid granting perpetual unauthenticated access
        to copyrighted content.

        However, servers deployed on AWS are often given *temporary*
        credentials instead of permanent ones. In particular, edx.org
        does this according to the AWS IAM best practices [1], which state:
        > "Use temporary security credentials (IAM roles) instead of long-term access keys".

        If such temporary credentials are used
        to sign S3 URLs, then the S3 URLs will automatically expire when
        then the temporary credentials  expire (even if the URL was just
        signed!). Thus, temporary credentials, although preferred by some operators,
        cannot be depended upon to sign our "long-lasting" S3 URLs.

        The compromise here is to allow Blockstore to have two separate
        sets of credentials:
        1. temporary credentials that allow full read/write/delete access to S3
           (along with any other necessary AWS permissions), and
        2. permanent credentials that *only* grant read access to S3.

        The first set of credentials remain the default credentials for Blockstore,
        while the second set of credentials can be specifically used to sign
        S3 URLs. Hence, this class.

        [1] https://docs.aws.amazon.com/general/latest/gr/aws-access-keys-best-practices.html
    """

    class BackendNotAvailable(Exception):
        """
        Raised if `LongLivedSignedUrlStorage` is not configured for use.
        """
        def __str__(self):
            return (
                "In order to instantiate this storage backend, "
                "boto3 must be installed "
                "and both BUNDLE_ASSET_URL_STORAGE_KEY "
                "and BUNDLE_ASSET_URL_STORAGE_SECRET "
                "must be configured in Django settings."
            )

    def __init__(self):
        """
        Construct a storage backend instance.

        Raises `BackendNotAvailable` if we are not configured.
        """
        try:
            S3Boto3Storage = get_storage_class("storages.backends.s3boto3.S3Boto3Storage")
        except ImportError as import_error:
            raise self.BackendNotAvailable from import_error
        try:
            key = settings.BUNDLE_ASSET_URL_STORAGE_KEY
            secret = settings.BUNDLE_ASSET_URL_STORAGE_SECRET
        except AttributeError as attr_error:
            raise self.BackendNotAvailable from attr_error
        if not (key and secret):
            raise self.BackendNotAvailable
        self.s3_backend = S3Boto3Storage(
            # All other S3 settings will be pulled in automatically from Django settings
            # (such as AWS_QUERYSTRING_EXPIRE and AWS_STORAGE_BUCKET_NAME).
            access_key=key, secret_key=secret
        )

    def url(self, name):
        """
        Generate a URL using the configured backend.
        """
        return self.s3_backend.url(name)


class AssetStorage(Storage):
    """
    Storage backend for assets related to bundles.

    This is largely a pass-through wrapper around the `default_storage` class;
    the one key difference is that URLs are generated through the
    `LongLivedSignedUrlStorage` class, if it is active.
    """

    def __init__(self):
        """
        Initialize an instance of AssetStorage.

        If `LongLivedSignedUrlStorage` is active, then instantiate an instance of
        it for generating URLs; otherwise, fall back to the default storage class.
        """
        try:
            self.url_backend = LongLivedSignedUrlStorage()
        except LongLivedSignedUrlStorage.BackendNotAvailable:
            self.url_backend = default_storage

    def url(self, name):
        return self.url_backend.url(name)

    def delete(self, name):
        return default_storage.delete(name)

    def exists(self, name):
        return default_storage.exists(name)

    def listdir(self, path):
        return default_storage.listdir(path)

    def path(self, name):
        return default_storage.path(name)

    def size(self, name):
        return default_storage.size(name)

    def get_accessed_time(self, name):
        return default_storage.get_accessed_time(name)

    def get_created_time(self, name):
        return default_storage.get_created_time(name)

    def get_modified_time(self, name):
        return default_storage.get_modified_time(name)

    def get_valid_name(self, name):
        return default_storage.get_valid_name(name)

    def get_alternative_name(self, file_root, file_ext):
        return default_storage.get_alternative_name(file_root, file_ext)

    def get_available_name(self, name, max_length=None):
        return default_storage.get_available_name(name, max_length=None)

    def _open(self, name, mode='rb'):
        return default_storage._open(name, mode=mode)  # pylint: disable=protected-access

    def _save(self, name, content):
        return default_storage._save(name, content)  # pylint: disable=protected-access


default_asset_storage = AssetStorage()

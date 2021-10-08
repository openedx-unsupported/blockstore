"""
Basic utilities for media file storage isolation while running tests.

We generate a lot of files with Blockstore tests, and Django doesn't natively
support isolating tests from each others file writes. All tests that write data
to file storages should use either the isolate_test_storage or
isolate_class_storage decorators.

I originally tried to use dj-inmemorystore (an in-memory Storage backend), but
ran into bugs re-reading recently written data where the files would show but
the data content would read back as empty. It was also difficult to debug issues
because the files were never persisted, so I kept on printing them out to debug
test failures. In the end, it seemed easier to just have them write out to disk.
"""
from datetime import datetime
from functools import wraps
from pathlib import Path
import re

from django.conf import settings
from django.conf.urls import url
from django.views.static import serve
from django.test import override_settings


def create_timestamped_path(prefix):
    """
    Create a timestamped dir like: "{prefix}/2019-01-04.17_26_38/"

    Returns a pathlib.Path object for the directory created. Creates any
    intermediate directories as necessary.
    """
    now = datetime.now()
    path = Path(prefix, now.strftime("%Y-%m-%d.%H_%M_%S"))
    Path.mkdir(path, parents=True)
    return str(path)


def isolate_class_storage(cls):
    """
    Class decorator to isolate Django test class file storage.

    This function uses Django's override_settings to change the value of
    settings.MEDIA_ROOT on a per-class basis, using the module and qualified
    name of the class for namespacing. So if the real MEDIA_ROOT for tests is
    "test_storage/", then a test class's private media root might be:
    "test_storage/blockstore.apps.bundles.tests.test_store/TestDrafts/"

    There is currently no cleanup.
    """
    test_class_name = ".".join([cls.__module__, cls.__qualname__])
    cls_media_path = Path(settings.MEDIA_ROOT, test_class_name)
    Path.mkdir(cls_media_path)
    override_fn = override_settings(MEDIA_ROOT=str(cls_media_path))
    return override_fn(cls)


def isolate_test_storage(cls):
    """
    Class decorator to isolate file storage for each individual test.

    This uses Django's override_settings function to change the value of
    settings.MEDIA_ROOT on a per-test method basis. The setUp() is included in
    the override, so any data you initialize there should be available in your
    test.

    There is currently no cleanup.
    """
    # Decorate the setUp method so that files written during setUp end up in the
    # right place. The override will persist until after tearDown() is called.
    original_setUp = cls.setUp

    @wraps(cls.setUp)
    def setUp(self):
        # TestCase.id() returns a string value for the currently executing test
        media_root = Path(settings.MEDIA_ROOT, self.id())
        Path.mkdir(media_root)
        storage_override = override_settings(MEDIA_ROOT=str(media_root))
        storage_override.enable()
        self.addCleanup(storage_override.disable)
        return original_setUp(self)

    cls.setUp = setUp

    return cls


def serve_media(request, path):
    """
    View function that serves MEDIA files and checks the MEDIA_ROOT each time.

    The isolate_class_storage and isolate_test_storage decorators make it easier
    to keep tests from trampling over each other by constantly changing the
    MEDIA_ROOT where these files get written. However, the normal way you add
    support for reading media files in debug settings is to do something like
    this:

        urlpatterns = [
            # ... the rest of your URLconf goes here ...
        ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    That doesn't work for us because the URL lookup is being initialized at
    startup and the value of settings.MEDIA_ROOT is fixed at that point. So we
    make a new view that pretty much does the same thing, except that we look up
    settings.MEDIA_ROOT every time so that we can see the values updated by our
    test isolation decorators.

    It also doesn't work for us because that `static()` call just returns an
    empty list (so essentially is a no-op) unless settings.DEBUG is True. This
    is intended as a safety feature to make sure you don't turn on horribly
    inefficient in-proc file serving in a real environment, but it also means
    that the URL pattern won't be added for tests by default.
    """
    return serve(request, path, document_root=settings.MEDIA_ROOT)


def url_for_test_media():
    """
    url() entry for MEDIA files (Snapshot data) during development and testing.

    You should never turn this on in a production setting because it has
    horrible performance characteristics.
    """
    media_url = re.escape(settings.MEDIA_URL.lstrip('/'))
    return url(
        fr'^{media_url}(?P<path>.*)$',
        serve_media,
    )

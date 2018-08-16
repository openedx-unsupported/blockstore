"""
BundleStore is the primary interface for the actual data stored by a Bundle.

* BundleSnapshots exists at this layer, but BundleVersions do not.
* BundleVersions will handle how they map to BundleSnapshots.

Whenever there's a need for hashing of content in some way, we use 20-byte
BLAKE2b.
"""
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime, timezone
import base64
import codecs
import hashlib
import logging
import pathlib
import json
import uuid

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile, File
from django.dispatch import Signal

import attr


snapshot_created = Signal(providing_args=["bundle_uuid", "hash_digest"])


logger = logging.getLogger(__name__)

@attr.s(frozen=True)
class FileInfo():
    """
    Basic information about a file in a BundleVersion.

    Backend-agnostic, so no details about exactly where or how it's stored.
    """
    path = attr.ib(type=str)
    public = attr.ib(type=bool)
    size = attr.ib(type=int)
    hash_digest = attr.ib(type=bytes)

    @classmethod
    def generate_hash(cls, file):
        """
        For a given django.core.files.File object, return a 20-byte BLAKE2 hash.
        """
        hash = hashlib.blake2b(digest_size=20)
        for chunk in file.chunks():
            hash.update(chunk)
        return hash

# @attr.s(frozen=True)
# class Link():
#     """
#     All Link references at this layer should be to BundleSnapshots, not
#     BundleVersions.
#     """
#     alias = attr.ib(type=str)
#     target = attr.ib()
#     uses = attr.ib(type=list)


# @attr.s()
# class DependencyMapping():
#     # Map of strings (no /'s allowed) to BundleVersionKey objects
#     links = attr.ib(type=dict)

#     def add_link(self, link):
#         """"""
#         pass

#     def all(self):
#         pass


@attr.s()
class BundleSnapshot():
    """
    Represents an immutable, point-in-time representation of a file tree.

    BundleSnapshots are only created for states that we want to permanently
    perserve, much like a commit in a version control system. We do not want to
    create a bunch of BundleSnapshots for intermediate versions.

    This class is a low level primitive that just stores Bundle content. Most
    metadata about a Bundle should be added to or referenced from the Bundle and
    BundleVersion models.

    Once written, a BundleSnapshot should almost never be modified or deleted,
    except in rare cases where we discover malicious or illegal content.
    """
    bundle_uuid = attr.ib()

    # Map of paths to FileInfo objects
    files = attr.ib(type=dict)

    # 20-byte BLAKE2 hash
    hash_digest = attr.ib(type=bytes)

    # Datetime with UTC Timezone
    created_at = attr.ib(type=datetime)

    @classmethod
    def create(cls, bundle_uuid, files, created_at=None):
        created_at = created_at or datetime.now(timezone.utc)
        str_to_be_hashed = json.dumps(
            [bundle_uuid, created_at, sorted(files.items())],
            cls=BundleJSONEncoder,
            indent=None,
            separators=(',', ':'),
        )
        hash_digest = hashlib.blake2b(str_to_be_hashed.encode('utf-8'), digest_size=20).digest()
        return cls(
            bundle_uuid=bundle_uuid,
            files=files,
            hash_digest=hash_digest,
            created_at=created_at,
        )

    def url(self, path):
        """Return a user-accessible URL to download a path from this Snapshot."""
        file_info = self.files[path]
        storage_path = '{}/data/{}'.format(
            self.bundle_uuid, file_info.hash_digest.hex()
        )
        return default_storage.url(storage_path)

@contextmanager
def files_from_disk(bundle_data_path):
    """
    Given a pathlib.Path, return file mapping suitable for BundleSnapshot.

    Returned dictionary will map from str to django.core.files.File objects.

    This will recursively scan subdirectories.
    """
    paths_to_files = {
        path.relative_to(*path.parts[:1]): File(open(path, "rb"))
        for path in bundle_data_path.rglob('*')
        if path.is_file()
    }
    try:
        yield paths_to_files
    finally:
        for open_file in paths_to_files.values():
            open_file.close()


class BundleJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FileInfo):
            return [
                obj.public,
                obj.size,
                obj.hash_digest.hex(),
            ]
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, BundleSnapshot):
            return {
                'bundle_uuid': obj.bundle_uuid,
                'hash_digest': obj.hash_digest.hex(),
                'files': obj.files,
                'created_at': obj.created_at,
                '_version': 1,
            }
        return json.JSONEncoder.default(self, obj)


class BundleDataStore():
    """
    This is the interface for storing the actual files that make up a Bundle.

    The responsibilities of this class are:
    * Create a new Snapshot from a set of files.
    * Generate URLs for resources within a Bundle.
    * Validate Links.

    # Important note about Versions/Snapshots:

    Numbered versions don't exist at this level -- versioning here is entirely
    based on content, so basically some kind of hash. BundleVersion is what
    manages numbered versioning and points to an entry in BundleDataStore. To
    make that distinction clearer, we'll say that BundleDataStore creates
    Snapshots, which BundleVersion will point to.

    This also helps us to mitigate the concurrency issue. Creating a snapshot
    might take a long time (say to upload all the assets). If we were assigning
    a version_num at the start of that process, we might run into a race
    condition with a process that starts a few seconds later, because they'll
    both see the database reflecting the same state. But if BundleStore creates
    only hash-versioned Snapshots, then it can do all that work and the only
    time version_num is read and incremented for a new entry is when
    BundleDataStore emits a signal that BundleVersion catches.

    # Extensibility

    Basic: We use Django's File Storage API, which means that one extension
    point is the Storages layer. This is the layer we'd plug into to start,
    using django-storages for things like S3 and equivalents, and some in-memory
    backing store for running tests.

    Advanced: It's possible that one day we'll want to swap out the entire
    BundleDataStore to adopt a radically different versioning store like git
    (+LFS). In that case, we'd create a new class that implements the same
    public BundleStore interface. To keep the option open, we'd want to make
    sure that things going in and out of BundleStore don't leak storage
    implementation details.
    """
    def snapshot(self, bundle_uuid, snapshot_digest):
        storage_path = "{}/snapshots/{}.json".format(bundle_uuid, snapshot_digest.hex())
        with default_storage.open(storage_path) as snapshot_file:
            snapshot_json = json.load(snapshot_file)

        files = {
            pathname: FileInfo(pathname, file_info[0], file_info[1], codecs.decode(file_info[2], 'hex'))
            for pathname, file_info in snapshot_json['files'].items()
        }
        hash_digest = codecs.decode(snapshot_json['hash_digest'], 'hex')

        # Python's datetime module is incapable of parsing the ISO 8601
        # timestamps that it itself produces (it can't do timezones with ":"
        # in them), so we need to only parse the part before that and then
        # manually add UTC timezone information into it.
        created_at = datetime.strptime(
            snapshot_json['created_at'], '%Y-%m-%dT%H:%M:%S.%f+00:00'
        )
        created_at = created_at.astimezone(timezone.utc)

        return BundleSnapshot(
            bundle_uuid=bundle_uuid,
            files=files,
            hash_digest=hash_digest,
            created_at=created_at,
        )

    def create_snapshot(self, bundle_uuid, paths_to_files):
        """
        paths_to_files is a dir of file paths to Django File objects
        """
        files = {}
        for path, file in paths_to_files.items():
            file_hash = FileInfo.generate_hash(file)
            data_write_location = "{}/data/{}".format(bundle_uuid, file_hash.hexdigest())
            if not default_storage.exists(data_write_location):
                default_storage.save(data_write_location, file)

            files[str(path)] = FileInfo(
                path=path, public=False, size=file.size, hash_digest=file_hash.digest()
            )

        snapshot = BundleSnapshot.create(bundle_uuid=bundle_uuid, files=files)
        summary_json_str = json.dumps(snapshot, cls=BundleJSONEncoder, indent=2, sort_keys=True)
        summary_write_location = "{}/snapshots/{}.json".format(bundle_uuid, snapshot.hash_digest.hex())

        if not default_storage.exists(summary_write_location):
            default_storage.save(summary_write_location, ContentFile(summary_json_str))

        snapshot_created.send(
            BundleDataStore,
            bundle_uuid=bundle_uuid,
            hash_digest=snapshot.hash_digest,
        )
        logger.info("Created Snapshot %s for Bundle %s", snapshot.hash_digest.hex(), bundle_uuid)

        return snapshot

"""
API Client methods for working with Blockstore bundles and drafts
"""

import base64
import re
from crum import get_current_request

from django.db.models import Q
from rest_framework import serializers

from blockstore.apps.bundles import models
from blockstore.apps.bundles.links import LinkCycleError
from blockstore.apps.bundles.store import DraftRepo, SnapshotRepo
from blockstore.apps.rest_api.v1.serializers.drafts import (
    DraftFileUpdateSerializer,
)

from .data import (
    BundleData,
    BundleVersionData,
    CollectionData,
    DraftData,
    BundleFileData,
    DraftFileData,
    BundleLinkData,
    DraftLinkData,
)
from .exceptions import (
    CollectionNotFound,
    BundleNotFound,
    BundleVersionNotFound,
    DraftNotFound,
    DraftHasNoChangesToCommit,
    BundleFileNotFound,
)


def get_collection(collection_uuid):
    """
    Retrieve metadata about the specified collection.

    Raises CollectionNotFound if collection with UUID does not exist.
    """
    collection_model = _get_collection_model(collection_uuid)
    return _collection_data_from_model(collection_model)


def create_collection(title):
    """
    Create a new collection.
    """
    collection_model = models.Collection(title=title)
    collection_model.save()
    return _collection_data_from_model(collection_model)


def update_collection(collection_uuid, title):
    """
    Update a collection's title.
    """
    collection_model = _get_collection_model(collection_uuid)
    collection_model.title = title
    collection_model.save()
    return _collection_data_from_model(collection_model)


def delete_collection(collection_uuid):
    """
    Delete a collection.
    """
    collection_model = _get_collection_model(collection_uuid)
    collection_model.delete()


def get_bundles(uuids=None, text_search=None):
    """
    Get the details of all bundles.
    """
    bundles_queryset = _bundle_queryset()
    if uuids:
        bundles_queryset = bundles_queryset.filter(uuid__in=uuids)
    if text_search:
        bundles_queryset = bundles_queryset.filter(
            Q(title__icontains=text_search) | Q(description__icontains=text_search) | Q(slug__icontains=text_search)
        )
    return [_bundle_data_from_model(bundle_model) for bundle_model in bundles_queryset]


def get_bundle(bundle_uuid):
    """
    Retrieve metadata about the specified bundle.

    Raises BundleNotFound if bundle with UUID does not exist.
    """
    bundle_model = _get_bundle_model(bundle_uuid)
    return _bundle_data_from_model(bundle_model)


def create_bundle(collection_uuid, slug, title="New Bundle", description=""):
    """
    Create a new bundle.

    Note that description is currently required.
    """
    collection_model = _get_collection_model(collection_uuid)
    bundle_model = models.Bundle(
        title=title,
        collection=collection_model,
        slug=slug,
        description=description,
    )
    bundle_model.save()
    return _bundle_data_from_model(bundle_model)


def update_bundle(bundle_uuid, **fields):
    """
    Update a bundle's title, description, slug, or collection.
    """
    bundle_model = _get_bundle_model(bundle_uuid)
    for str_field in ("title", "description", "slug"):
        if str_field in fields:
            setattr(bundle_model, str_field, fields.pop(str_field))
    if "collection_uuid" in fields:
        collection_uuid = fields.pop("collection_uuid")
        collection_model = _get_collection_model(collection_uuid)
        bundle_model.collection = collection_model
    if fields:
        raise ValueError("Unexpected extra fields passed to update_bundle: {}".format(fields.keys()))

    bundle_model.save()
    return _bundle_data_from_model(bundle_model)


def delete_bundle(bundle_uuid):
    """
    Delete a bundle.
    """
    bundle_model = _get_bundle_model(bundle_uuid)
    bundle_model.delete()


def get_draft(draft_uuid):
    """
    Retrieve metadata about the specified draft.
    If you don't know the draft's UUID, look it up using get_bundle()
    """
    draft_model = _get_draft_model(draft_uuid)
    return _draft_data_from_model(draft_model)


def get_or_create_bundle_draft(bundle_uuid, draft_name):
    """
    Retrieve metadata about the specified draft, creating a new one if it does not exist yet.
    """
    try:
        draft_model = _draft_queryset().get(bundle__uuid=bundle_uuid, name=draft_name)
    except models.Draft.DoesNotExist:
        bundle_model = _get_bundle_model(bundle_uuid)
        draft_model = models.Draft(
            bundle=bundle_model,
            name=draft_name,
        )
        draft_model.save()
    return _draft_data_from_model(draft_model)


def commit_draft(draft_uuid):
    """
    Commit all of the pending changes in the draft, creating a new version of
    the associated bundle.

    Does not return any value.
    """
    draft_repo = DraftRepo(SnapshotRepo())
    staged_draft = draft_repo.get(draft_uuid)

    if not staged_draft.files_to_overwrite and not staged_draft.links_to_overwrite:
        raise DraftHasNoChangesToCommit("Draft {} does not have any changes to commit.".format(draft_uuid))

    new_snapshot, _updated_draft = draft_repo.commit(staged_draft)
    models.BundleVersion.create_new_version(
        new_snapshot.bundle_uuid, new_snapshot.hash_digest
    )


def delete_draft(draft_uuid):
    """
    Delete the specified draft, removing any staged changes/files/deletes.

    Does not return any value.
    """
    draft_model = _get_draft_model(draft_uuid)
    draft_repo = DraftRepo(SnapshotRepo())
    draft_repo.delete(draft_uuid)
    draft_model.delete()


def get_bundle_version(bundle_uuid, version_number=None):
    """
    Get the details of the specified bundle version
    """
    bundle_version_model = _get_bundle_version_model(bundle_uuid, version_number)
    if bundle_version_model is None:
        return None
    return _bundle_version_data_from_model(bundle_version_model)


def get_bundle_version_files(bundle_uuid, version_number):
    """
    Get a list of the files in the specified bundle version
    """
    if version_number == 0:
        # There are no files in the initial version of a bundle
        return []
    bundle_version = get_bundle_version(bundle_uuid, version_number)
    return list(bundle_version.files.values() if bundle_version else [])


def get_bundle_version_links(bundle_uuid, version_number):
    """
    Get a dictionary of the links in the specified bundle version
    """
    if version_number == 0:
        # There are no links in the initial version of a bundle
        return {}
    bundle_version = get_bundle_version(bundle_uuid, version_number)
    return bundle_version.links if bundle_version else {}


def get_bundle_files_dict(bundle_uuid, use_draft=None):
    """
    Get a dict of all the files in the specified bundle or draft.

    Returns a dict where the keys are the paths (strings) and the values are
    BundleFileData or DraftFileData tuples.
    """
    if use_draft:
        try:
            draft_model = _draft_queryset().get(bundle__uuid=bundle_uuid, name=use_draft)
        except models.Draft.DoesNotExist:
            pass
        else:
            return _draft_data_from_model(draft_model).files

    bundle_version = get_bundle_version(bundle_uuid)
    return bundle_version.files if bundle_version else {}


def get_bundle_files(bundle_uuid, use_draft=None):
    """
    Get an iterator over all the files in the specified bundle or draft.
    """
    return get_bundle_files_dict(bundle_uuid, use_draft).values()


def get_bundle_links(bundle_uuid, use_draft=None):
    """
    Get a dict of all the links in the specified bundle.

    Returns a dict where the keys are the link names (strings) and the values
    are LinkDetails or DraftLinkDetails tuples.
    """
    if use_draft:
        try:
            draft_model = _draft_queryset().get(bundle__uuid=bundle_uuid, name=use_draft)
        except models.Draft.DoesNotExist:
            pass
        else:
            return _draft_data_from_model(draft_model).links

    bundle_version = get_bundle_version(bundle_uuid)
    return get_bundle_version(bundle_uuid).links if bundle_version else {}


def get_bundle_file_metadata(bundle_uuid, path, use_draft=None):
    """
    Get the metadata of the specified file.
    """
    files_dict = get_bundle_files_dict(bundle_uuid, use_draft=use_draft)
    try:
        return files_dict[path]
    except KeyError as exc:
        raise BundleFileNotFound(
            "Bundle {} (draft: {}) does not contain a file {}".format(bundle_uuid, use_draft, path)
        ) from exc


def get_bundle_file_data(bundle_uuid, path, use_draft=None):
    """
    Read all the data in the given bundle file and return it as a
    binary string.

    Do not use this for large files!
    """

    if use_draft:
        try:
            draft_model = _draft_queryset().get(bundle__uuid=bundle_uuid, name=use_draft)
        except models.Draft.DoesNotExist:
            pass
        else:
            draft_repo = DraftRepo(SnapshotRepo())
            staged_draft = draft_model.staged_draft
            with draft_repo.open(staged_draft, path) as file:
                return file.read()

    bundle_version_model = _get_bundle_version_model(bundle_uuid, 0)

    snapshot_repo = SnapshotRepo()
    snapshot = bundle_version_model.snapshot()
    with snapshot_repo.open(snapshot, path) as file:
        return file.read()


def write_draft_file(draft_uuid, path, contents):
    """
    Create or overwrite the file at 'path' in the specified draft with the given
    contents. To delete a file, pass contents=None.

    If you don't know the draft's UUID, look it up using
    get_or_create_bundle_draft()

    Does not return anything.
    """
    data = {
        'files': {
            path: _encode_str_for_draft(contents) if contents is not None else None,
        },
    }
    serializer = DraftFileUpdateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    files_to_write = serializer.validated_data['files']
    dependencies_to_write = serializer.validated_data['links']

    draft_repo = DraftRepo(SnapshotRepo())
    try:
        draft_repo.update(draft_uuid, files_to_write, dependencies_to_write)
    except LinkCycleError as exc:
        raise serializers.ValidationError("Link cycle detected: Cannot create draft.") from exc


def set_draft_link(draft_uuid, link_name, bundle_uuid, version):
    """
    Create or replace the link with the given name in the specified draft so
    that it points to the specified bundle version. To delete a link, pass
    bundle_uuid=None, version=None.

    If you don't know the draft's UUID, look it up using
    get_or_create_bundle_draft()

    Does not return anything.
    """
    data = {
        'links': {
            link_name: {"bundle_uuid": str(bundle_uuid), "version": version} if bundle_uuid is not None else None,
        },
    }
    serializer = DraftFileUpdateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    files_to_write = serializer.validated_data['files']
    dependencies_to_write = serializer.validated_data['links']

    draft_repo = DraftRepo(SnapshotRepo())
    try:
        draft_repo.update(draft_uuid, files_to_write, dependencies_to_write)
    except LinkCycleError as exc:
        raise serializers.ValidationError("Link cycle detected: Cannot create draft.") from exc


REGEX_BROWSER_URL = re.compile(r'http://edx.devstack.(studio|lms):')


def force_browser_url(blockstore_file_url):
    """
    Ensure that the given devstack URL is a URL accessible from the end user's browser.
    """
    # Hack: on some devstacks, we must necessarily use different URLs for
    # accessing Blockstore file data from within and outside of docker
    # containers, but Blockstore has no way of knowing which case any particular
    # request is for. So it always returns a URL suitable for use from within
    # the container. Only this edxapp can transform the URL at the last second,
    # knowing that in this case it's going to the user's browser and not being
    # read by edxapp.
    # In production, the same S3 URLs get used for internal and external access
    # so this hack is not necessary.
    return re.sub(REGEX_BROWSER_URL, 'http://localhost:', blockstore_file_url)


def _encode_str_for_draft(input_str):
    """
    Given a string, return UTF-8 representation that is then base64 encoded.
    """
    if isinstance(input_str, str):
        binary = input_str.encode('utf8')
    else:
        binary = input_str
    return base64.b64encode(binary)


def _get_collection_model(collection_uuid):
    """
    Get collection model from UUID.

    Raises CollectionNotFound if the collection does not exist.
    """
    try:
        collection_model = models.Collection.objects.get(uuid=collection_uuid)
    except models.Collection.DoesNotExist as exc:
        raise CollectionNotFound("Collection {} does not exist.".format(collection_uuid)) from exc
    return collection_model


def _collection_data_from_model(collection_model):
    """
    Create and return CollectionData from collection model.
    """
    return CollectionData(uuid=collection_model.uuid, title=collection_model.title)


def _bundle_queryset():
    """
    Returns the bundle model queryset.

    Prefetch the data needed to create BundleData objects.
    """
    return models.Bundle.objects.prefetch_related('drafts', 'versions')


def _get_bundle_model(bundle_uuid):
    """
    Get Bundle model from UUID.

    Raises BundleNotFound if bundle with UUID does not exist.
    """
    try:
        bundle_model = _bundle_queryset().get(uuid=bundle_uuid)
    except models.Bundle.DoesNotExist as exc:
        raise BundleNotFound("Bundle {} does not exist.".format(bundle_uuid)) from exc
    return bundle_model


def _bundle_data_from_model(bundle_model):
    """
    Create and return BundleData from bundle model.
    """
    latest_version = bundle_model.versions.order_by('-version_num').first()
    latest_version_num = latest_version.version_num if latest_version else 0

    return BundleData(
        uuid=bundle_model.uuid,
        title=bundle_model.title,
        description=bundle_model.description,
        slug=bundle_model.slug,
        drafts={draft.name: draft.uuid for draft in bundle_model.drafts.all()},
        latest_version=latest_version_num,
    )


def _draft_queryset():
    """
    Returns the draft model queryset.

    Prefetch the data needed to create DraftData objects.
    """
    return models.Draft.objects.select_related('bundle')


def _get_draft_model(draft_uuid):
    """
    Get Draft model from UUID.

    Raises DraftNotFound if draft with UUID does not exist.
    """
    try:
        draft_model = _draft_queryset().get(uuid=draft_uuid)
    except models.Draft.DoesNotExist as exc:
        raise DraftNotFound("Draft {} does not exist.".format(draft_uuid)) from exc
    return draft_model


def _build_absolute_uri(url):
    """
    Build an absolute URI from the given url, using the CRUM middleware's stored request.
    """
    request = get_current_request()
    return request.build_absolute_uri(url)


def _draft_data_from_model(draft_model):
    """
    Create and return DraftData from draft model.
    """
    draft_repo = DraftRepo(SnapshotRepo())
    staged_draft = draft_model.staged_draft

    return DraftData(
        uuid=draft_model.uuid,
        bundle_uuid=draft_model.bundle.uuid,
        name=draft_model.name,
        created_at=draft_model.staged_draft.created_at,
        updated_at=draft_model.staged_draft.updated_at,
        files={
            path: DraftFileData(
                path=path,
                size=file_info.size,
                url=_build_absolute_uri(draft_repo.url(staged_draft, path)),
                hash_digest=file_info.hash_digest,
                modified=path in draft_model.staged_draft.files_to_overwrite,
            )
            for path, file_info in staged_draft.files.items()
        },
        links={
            link.name: DraftLinkData(
                name=link.name,
                direct=link.direct_dependency,
                indirect=link.indirect_dependencies,
                modified=link.name in staged_draft.links_to_overwrite.modified_set,
            )
            for link in staged_draft.composed_links()
        }
    )


def _bundle_version_queryset():
    """
    Returns the bundle version model queryset.

    Prefetch the data needed to create BundleVersionData objects.
    """
    return models.BundleVersion.objects.select_related('bundle')


def _get_bundle_version_model(bundle_uuid, version_number=None):
    """
    Get BundleVersion from bundle UUID and version number.

    If version_number is None, returns the latest bundle version of the bundle.
    """
    filter_kwargs = {
        'bundle__uuid': bundle_uuid
    }
    if version_number:
        filter_kwargs['version_num'] = version_number

    bundle_version_model = _bundle_version_queryset().filter(**filter_kwargs).order_by('-version_num').first()
    if version_number and bundle_version_model is None:
        raise BundleVersionNotFound("Bundle Version {},{} does not exist.".format(bundle_uuid, version_number))
    return bundle_version_model


def _bundle_version_data_from_model(bundle_version_model):
    """
    Create and return BundleVersionData from bundle version model.
    """
    snapshot = bundle_version_model.snapshot()
    snapshot_repo = SnapshotRepo()

    return BundleVersionData(
        bundle_uuid=bundle_version_model.bundle.uuid,
        version=bundle_version_model.version_num,
        change_description=bundle_version_model.change_description,
        created_at=snapshot.created_at,
        files={
            path: BundleFileData(
                path=path,
                url=_build_absolute_uri(snapshot_repo.url(snapshot, path)),
                size=file_info.size,
                hash_digest=file_info.hash_digest.hex(),
            ) for path, file_info in snapshot.files.items()
        },
        links={
            link.name: BundleLinkData(
                name=link.name,
                direct=link.direct_dependency,
                indirect=link.indirect_dependencies,
            )
            for link in snapshot.links
        },
    )

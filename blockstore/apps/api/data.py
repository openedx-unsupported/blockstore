"""
Data models used for Blockstore API Client
"""

from datetime import datetime
from uuid import UUID

import attr

from blockstore.apps.bundles.links import convert_to_uuid, Dependency


@attr.s(frozen=True)
class CollectionData:
    """
    Metadata about a blockstore collection
    """
    uuid = attr.ib(type=UUID, converter=convert_to_uuid)
    title = attr.ib(type=str)


@attr.s(frozen=True)
class BundleData:
    """
    Metadata about a blockstore bundle
    """
    uuid = attr.ib(type=UUID, converter=convert_to_uuid)
    title = attr.ib(type=str)
    description = attr.ib(type=str)
    slug = attr.ib(type=str)
    drafts = attr.ib(type=dict)  # Dict of drafts, where keys are the draft names and values are draft UUIDs
    # Note that if latest_version is 0, it means that no versions yet exist
    latest_version = attr.ib(type=int, validator=attr.validators.instance_of(int))


@attr.s(frozen=True)
class DraftData:
    """
    Metadata about a blockstore draft
    """
    uuid = attr.ib(type=UUID, converter=convert_to_uuid)
    bundle_uuid = attr.ib(type=UUID, converter=convert_to_uuid)
    name = attr.ib(type=str)
    created_at = attr.ib(type=datetime, validator=attr.validators.instance_of(datetime))
    updated_at = attr.ib(type=datetime, validator=attr.validators.instance_of(datetime))
    files = attr.ib(type=dict)
    links = attr.ib(type=dict)


@attr.s(frozen=True)
class BundleVersionData:
    """
    Metadata about a blockstore bundle version.
    """
    bundle_uuid = attr.ib(type=UUID, converter=convert_to_uuid)
    version = attr.ib(type=int, validator=attr.validators.instance_of(int))
    change_description = attr.ib(type=str)
    created_at = attr.ib(type=datetime, validator=attr.validators.instance_of(datetime))
    files = attr.ib(type=dict)
    links = attr.ib(type=dict)


@attr.s(frozen=True)
class BundleFileData:
    """
    Metadata about a file in a blockstore bundle or draft.
    """
    path = attr.ib(type=str)
    size = attr.ib(type=int)
    url = attr.ib(type=str)
    hash_digest = attr.ib(type=str)


@attr.s(frozen=True)
class DraftFileData(BundleFileData):
    """
    Metadata about a file in a blockstore draft.
    """
    modified = attr.ib(type=bool)  # Was this file modified in the draft?


@attr.s(frozen=True)
class BundleLinkData:
    """
    Details about a specific link in a BundleVersion or Draft
    """
    name = attr.ib(type=str)
    direct = attr.ib(type=Dependency)
    indirect = attr.ib(type=list)  # List of Dependency objects


@attr.s(frozen=True)
class DraftLinkData(BundleLinkData):
    """
    Details about a specific link in a Draft
    """
    modified = attr.ib(type=bool)

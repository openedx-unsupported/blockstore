"""
Data models for tags
"""
from collections import namedtuple


TagPrivate = namedtuple('TagPrivate', ['taxonomy_uid', 'name'])


class Tag(TagPrivate):
    """
    A tag that can be applied to content.

    # The Unique ID of the taxonomy which owns this tag
    taxonomy_uid: int
    # The text of this tag, which also serves as its identifier.
    # Case is preserved but within a taxonomy, tags must be case-insensitively unique.
    name: str
    """

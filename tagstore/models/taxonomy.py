"""
A taxonomy is a collection of tags that can be applied to content.
"""
from typing import NamedTuple, Optional, NewType
from .user import UserId

TaxonomyId = NewType('TaxonomyId', int)


class TaxonomyMetadata(NamedTuple):
    """
    A taxonomy is a collection of tags that can be applied to content.
    """
    uid: TaxonomyId
    name: str
    owner_id: Optional[UserId]

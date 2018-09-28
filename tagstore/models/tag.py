"""
Data models for tags
"""
from typing import NamedTuple, NewType, Set


class Tag(NamedTuple):
    """
    A tag that can be applied to content.
    """
    taxonomy_id: int  # The unique ID of the taxonomy which owns this tag
    tag: str  # The text of this tag, which also serves as its identifier. Unique within this taxonomy.


TagSet = NewType('TagSet', Set[Tag])

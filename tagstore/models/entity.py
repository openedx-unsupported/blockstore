"""
This is how we model any external entity that can be tagged.
"""
from typing import NamedTuple


class EntityId(NamedTuple):
    entity_type: str
    external_id: str

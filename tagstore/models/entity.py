"""
This is how we model any external entity that can be tagged.
"""
from collections import namedtuple


EntityId = namedtuple('EntityId', ['entity_type', 'external_id'])

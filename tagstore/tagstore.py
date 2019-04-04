"""
Convenience module to make importing Tagstore easier.
"""
# pylint: disable=unused-import
from .models import (
    EntityId, Entity,
    TagId, Tag,
    TaxonomyId, Taxonomy
)
from .search import (
    get_tags_applied_to,
    get_entities_tagged_with,
    get_entities_tagged_with_all,
)

"""
Documents for search app.
"""

from .core.documents import Document
from .fieldsets import (
    AnalyticsFieldSet,
    AuthorshipFieldSet,
    EntityFieldSet,
    OwnernershipFieldSet,
    SummaryFieldSet,
    TagsFieldSet,
)


class BlockDocument(Document):
    """
    Document for entities to be indexed in BlocksIndex.
    """

    FIELD_SETS = (
        EntityFieldSet,
        SummaryFieldSet,
        OwnernershipFieldSet,
        AuthorshipFieldSet,
        TagsFieldSet,
        AnalyticsFieldSet,
    )

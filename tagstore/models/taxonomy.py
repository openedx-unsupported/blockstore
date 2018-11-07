"""
A taxonomy is a collection of tags that can be applied to content.
"""
from typing import Any, Iterator, NamedTuple, NewType, Optional, Tuple

from .tag import Tag
from .user import UserId

TaxonomyId = NewType('TaxonomyId', int)


class Taxonomy(NamedTuple):
    """
    A taxonomy is a collection of tags that can be applied to content.

    Is a NamedTuple for performance, simplicity, and immutability, but
    we can change it to a full class at some point if needed.
    """
    uid: TaxonomyId
    name: str
    owner_id: Optional[UserId]

    tagstore: Any  # Type is Tagstore but we can't define that without circular import

    # Convenience methods:

    def add_tag(self, tag: str, parent_tag: Optional[Tag] = None) -> Tag:
        """
        Add the specified tag to this given taxonomy, and retuns it.

        Will be a no-op if the tag already exists in the taxonomy (case-insensitive),
        however the returned (existing) Tag may differ in case.
        Will raise a ValueError if the specified taxonomy or parent doesn't exist.
        Will raise a ValueError if trying to add a child tag that
        already exists anywhere in the taxonomy.
        """
        return self.tagstore.add_tag_to_taxonomy(tag, self.uid, parent_tag)

    def get_tag(self, tag: str) -> Optional[Tag]:
        """
        If a tag with the specified name (case insensitive) exists in this taxonomy, get it.

        Otherwise returns None.
        """
        return self.tagstore.get_tag_in_taxonomy(tag, self.uid)

    def list_tags(self) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy, in alphabetical order.
        """
        return self.tagstore.list_tags_in_taxonomy(self.uid)

    def list_tags_hierarchically(self) -> Iterator[Tuple[Tag, Tag]]:
        """
        Get a list of all tags in the given taxonomy, in hierarchical and alphabetical order.

        Returns tuples of (Tag, parent_tag).
        This method guarantees that parent tags will be returned before their child tags.
        """
        return self.tagstore.list_tags_in_taxonomy_hierarchically(self.uid)

    def list_tags_containing(self, text: str) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy that contain the given string
        (case insensitive). This is intended to be used for auto-complete when users tag content
        by typing tags into a text field, for example.
        """
        return self.tagstore.list_tags_in_taxonomy_containing(self.uid, text)

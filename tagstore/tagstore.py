"""
A system for storing and retrieving tags related to Blockstore entities
"""

from typing import Iterator, List, Optional, Set, Tuple

from .models import EntityId, Tag, TaxonomyId, Taxonomy, UserId


class Tagstore:
    """
    Python API to store and retrieve tags and taxonomies

    This class defines the API only, and the implementation is done
    by a backend subclass.
    """

    # Taxonomy CRUD ##########################

    def create_taxonomy(self, name: str, owner_id: Optional[UserId] = None) -> Taxonomy:
        """ Create a new taxonomy with the specified name and owner. """
        raise NotImplementedError()

    def get_taxonomy(self, taxonomy_uid: TaxonomyId) -> Optional[Taxonomy]:
        """ Get metadata about the given taxonomy """
        raise NotImplementedError()

    def add_tag_to_taxonomy(self, name: str, taxonomy_uid: TaxonomyId, parent_tag: Optional[Tag] = None) -> Tag:
        """
        Add the specified tag to the given taxonomy, and retuns it.

        If a Tag already exists in the taxonomy with the given name (case-insensitive)
        and the given parent, then that Tag is returned and no changes are made.

        Will raise a ValueError if the specified taxonomy or parent doesn't exist.
        Will raise a ValueError if trying to add a child tag that
        already exists but with a different parent tag.

        Subclasses should implement this by overriding _add_tag_to_taxonomy()
        """
        if not isinstance(name, str) or len(name) < 1:
            raise ValueError("Tag name must be a (non-empty) string.")

        if name != name.strip():
            raise ValueError("Tag name cannot start or end with whitespace.")

        if any(char in name for char in ':,;\n\r\\'):
            raise ValueError("Tag name contains an invalid character.")

        parent_tag_str = None
        if parent_tag is not None:
            if parent_tag.taxonomy_uid != taxonomy_uid:
                raise ValueError("A tag cannot have a parent from another taxonomy")
            parent_tag_str = parent_tag.name

        final_name = self._add_tag_to_taxonomy(taxonomy_uid=taxonomy_uid, name=name, parent_tag=parent_tag_str)
        return Tag(taxonomy_uid=taxonomy_uid, name=final_name)

    def _add_tag_to_taxonomy(self, taxonomy_uid: TaxonomyId, name: str, parent_tag: Optional[str] = None) -> str:
        """
        Subclasses should override this method to implement adding tags to a taxonomy.

        It should return the 'name' value of the newly created tag, or the existing tag
        if a tag already exists.
        """
        raise NotImplementedError()

    def get_tag_in_taxonomy(self, name: str, taxonomy_uid: TaxonomyId) -> Optional[Tag]:
        """
        If a tag with the specified name (case insensitive) exists in this taxonomy, get it.

        Otherwise returns None.
        """
        raise NotImplementedError()

    def list_tags_in_taxonomy(self, taxonomy_uid: TaxonomyId) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy, in alphabetical order.
        """
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

    def list_tags_in_taxonomy_hierarchically(self, taxonomy_uid: TaxonomyId) -> Iterator[Tuple[Tag, Tag]]:
        """
        Get a list of all tags in the given taxonomy, in hierarchical and alphabetical order.

        Returns tuples of (Tag, parent_tag).
        This method guarantees that parent tags will be returned before their child tags.
        """
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

    def list_tags_in_taxonomy_containing(self, taxonomy_uid: TaxonomyId, text: str) -> Iterator[Tag]:
        """
        Get a (flattened) list of all tags in the given taxonomy that contain the given string
        (case insensitive). This is intended to be used for auto-complete when users tag content
        by typing tags into a text field, for example.
        """
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

    # Tagging Entities ##########################

    def add_tag_to(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Add the specified tag to the specified entity/entities.

        Will be a no-op if the tag is already applied.
        """
        raise NotImplementedError()

    def remove_tag_from(self, tag: Tag, *entity_ids: EntityId) -> None:
        """
        Remove the specified tag from the specified entity/entities

        Will be a no-op if the entities do not have that tag.
        """
        raise NotImplementedError()

    def get_tags_applied_to(self, *entity_ids: EntityId) -> Set[Tag]:
        """ Get the set of unique tags applied to any of the specified entity IDs """
        raise NotImplementedError()

    # Searching Entities ##########################

    def get_entities_tagged_with(self, tag: Tag, **kwargs) -> Iterator[EntityId]:
        """
        Get an iterator over all entities that have been tagged with the given tag.

        Also accepts the same filtering keyword arguments as
        get_entities_tagged_with_all()
        """
        # Subclasses do not generally need to override this method.
        yield from self.get_entities_tagged_with_all({tag}, **kwargs)

    def get_entities_tagged_with_all(
        self,
        tags: Set[Tag],
        entity_types: Optional[List[str]] = None,
        external_id_prefix: Optional[str] = None,
        entity_ids: Optional[List[EntityId]] = None,  # use this to filter a list of entity IDs by tag
        include_child_tags=True,  # For hierarchical taxonomies, include child tags
                                  # (e.g. search for "Animal" will return results tagged only with "Dog")
    ) -> Iterator[EntityId]:
        """
        Method for searching/filtering for entities that have all the specified tags
        and match all of the specified conditions
        """
        raise NotImplementedError()
        yield None  # Required to make this non-implementation also a generator. pylint: disable=unreachable

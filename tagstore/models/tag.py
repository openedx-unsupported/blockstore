"""
Data models for tags
"""
from typing import NamedTuple, Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, IntegrityError

from .common import MAX_CHAR_FIELD_LENGTH
from .entity import EntityId, Entity


class TagId(NamedTuple):
    """
    Idenifier for a tag that can be applied to content.
    """
    # The Unique ID of the taxonomy which owns this tag
    taxonomy_id: int
    # The text of this tag, which also serves as its identifier.
    # Case is preserved but within a taxonomy, tags must be case-insensitively unique.
    # Example: "good problem".
    name: str


class Tag(models.Model):
    """
    A tag that can be applied to content.

    A tag is a string (e.g. "difficult") and belongs to a taxonomy. The taxonomy
    may consist of a flat set of tags or a hierarchical tree of tags.
    """
    # This ID should never be used - [taxonomy, name] is a compound key that
    # should be used in all public contexts
    _id = models.BigAutoField(primary_key=True, db_column='id')
    # The taxonomy which owns this tag
    taxonomy = models.ForeignKey('Taxonomy', null=False, related_name='tags')
    # The text of this tag, which also serves as its identifier.
    # Case is preserved but within a taxonomy, tags must be case-insensitively unique.
    # Example: "good problem".
    name = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH, db_column='tag')
    # Materialized path. Always ends with ":".
    # A simple tag like "good problem" would have a path of "good problem:"
    # A tag like "mammal" that is a child of "animal" would have a path of
    # "animal:mammal:". Tags are not allowed to contain the ":" character
    # so no escaping is necessary.
    path = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH, db_index=True)

    PATH_SEP = ':'  # Character used to separate tags

    class ValidationError(DjangoValidationError):
        """ Tag-specific Validation error """

    class AlreadyExistsError(IntegrityError):
        """
        Tag-specific error raised when a tag already exists elsewhere in the
        taxonomy (i.e. with a different parent.)
        """

    class Meta:
        db_table = 'tagstore_tag'
        ordering = ('name', )
        unique_together = (
            ('taxonomy', 'name'),
            # Note that (taxonomy, path) is also unique but we don't bother
            # with an index for that.
        )

    @classmethod
    def make_path(cls, taxonomy_id: int, name: str, parent_path: str = '') -> str:
        """
        Return the full 'materialized path' for use in the path field.

        make_path(15, 'easy') -> '15:easy:'
        make_path(200, 'Lion', 'animal:mammal:') -> '200:animal:mammal:lion:'
        """
        prefix = str(taxonomy_id) + cls.PATH_SEP
        if parent_path:
            assert parent_path.startswith(prefix)
            return parent_path + name + cls.PATH_SEP
        else:
            return prefix + name + cls.PATH_SEP

    @property
    def parent_tag_id(self) -> Optional[TagId]:
        """
        Get the ID of this tag's parent, or None if it has no parent

        This model's 'path' field might look like '200:animal:mammal:lion:'
        in which case parent_tag_id will return TagId(taxonomy_id, 'mammal')
        """
        parts = self.path.split(self.PATH_SEP)
        if len(parts) <= 3:
            return None
        return TagId(taxonomy_id=self.taxonomy_id, name=parts[-3])

    @property
    def id(self) -> TagId:
        return TagId(taxonomy_id=self.taxonomy_id, name=self.name)

    def __str__(self) -> str:
        return self.name

    def add_to(self, *entity_ids: EntityId) -> None:
        """
        Add this tag to the specified entity/entities.

        Will be a no-op if the tag is already applied.
        """
        for entity_id in entity_ids:
            Entity.get(entity_id).tags.add(self)

    def remove_from(self, *entity_ids: EntityId) -> None:
        """
        Remove the specified tag from the specified entity/entities

        Will be a no-op if the entities do not have that tag or do not exist.
        """
        # This could be optimized to a single DB query, but that's probably not necessary
        for entity_id in entity_ids:
            try:
                Entity.objects.get(**entity_id._asdict()).tags.remove(self)
            except Entity.DoesNotExist:
                pass

    def clean(self):
        """
        Validate this tag's name
        """
        if not isinstance(self.name, str) or len(self.name) < 1:
            raise Tag.ValidationError("Tag name must be a (non-empty) string.")

        if self.name != self.name.strip():
            raise Tag.ValidationError("Tag name cannot start or end with whitespace.")

        if any(char in self.name for char in ':,;\n\r\\'):
            raise Tag.ValidationError("Tag name contains an invalid character.")

    @property
    def taxonomy_is_saving(self) -> bool:
        """
        This attribute is used to ensure tags are only added/deleted via
        Taxonomy.add_tag() and Taxonomy.delete_tag()
        """
        return getattr(self, "_taxonomy_is_saving", False)

    @taxonomy_is_saving.setter
    def taxonomy_is_saving(self, value: bool):
        """
        Used by Taxonomy to indicate it has verified this Tag and it can be saved.
        """
        self._taxonomy_is_saving = value  # pylint: disable=attribute-defined-outside-init

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Tag objects should never be created manually, because
        the Taxonomy needs to do a lot of validation. Use the
        Taxonomy.add_tag() method instead.
        """
        if not self.taxonomy_is_saving:
            raise Exception(Tag.save.__doc__)
        # Always clean() before saving
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, **kwargs):  # pylint: disable=arguments-differ
        """
        Delete this Tag and any sub-tags
        """
        self.taxonomy.delete_tag(self, **kwargs)  # pylint: disable=no-member

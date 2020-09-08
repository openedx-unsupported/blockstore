"""
Tagstore backend that uses the django ORM
"""
from typing import Optional

from django.db import models

from tagstore import Tagstore
from tagstore.models import EntityId, Taxonomy as TaxonomyTuple, UserId, Tag as TagTuple

# If MySQL is configured to use utf8mb4 (correct utf8), indexed
# columns have a max length of 191. Until Django supports limiting index
# length to 191 characters, we need to limit the value length to below
# 191 characters, for any column that might be indexed.
# (https://code.djangoproject.com/ticket/18392#comment:3)
MAX_CHAR_FIELD_LENGTH = 180


class Entity(models.Model):
    """
    An entity that can be tagged.
    """
    id = models.BigAutoField(primary_key=True)
    entity_type = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH)
    external_id = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH)

    tags = models.ManyToManyField('Tag')

    class Meta:
        unique_together = (
            ('entity_type', 'external_id'),
        )
        db_table = 'tagstore_entity'
        verbose_name_plural = 'Entities'

    @property
    def as_tuple(self) -> EntityId:
        return EntityId(entity_type=self.entity_type, external_id=self.external_id)

    def __str__(self) -> str:
        return "%s %s" % (self.entity_type, self.external_id)


class Taxonomy(models.Model):
    """
    A taxonomy is a collection of tags, some of which may be organized into
    a hierarchy.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH)
    owner = models.ForeignKey(Entity, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'tagstore_taxonomy'
        verbose_name_plural = 'Taxonomies'

    def as_tuple(self, tagstore: Tagstore) -> TaxonomyTuple:
        owner_id = UserId(self.owner.as_tuple) if self.owner is not None else None
        return TaxonomyTuple(uid=self.id, name=self.name, owner_id=owner_id, tagstore=tagstore)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """
    A tag within a taxonomy
    """
    id = models.BigAutoField(primary_key=True)
    taxonomy = models.ForeignKey(Taxonomy, null=False, on_delete=models.CASCADE)
    # The tag string, like "good problem".
    name = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH, db_column='tag')
    # Materialized path. Always ends with ":".
    # A simple tag like "good-problem" would have a path of "good-problem:"
    # A tag like "mammal" that is a child of "animal" would have a path of
    # "animal:mammal:". Tags are not allowed to contain the ":" character
    # so no escaping is necessary.
    path = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH, db_index=True)

    PATH_SEP = ':'  # Character used to separate tags

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
    def parent_tag_tuple(self) -> Optional[TagTuple]:
        """
        Get the Tag tuple of this tag's parent, or None if it has no parent

        This model's 'path' field might look like '200:animal:mammal:lion:'
        in which case parent_tag will return 'mammal'
        """
        parts = self.path.split(self.PATH_SEP)
        if len(parts) <= 3:
            return None
        return TagTuple(taxonomy_uid=self.taxonomy_id, name=parts[-3])

    def __str__(self) -> str:
        return self.name

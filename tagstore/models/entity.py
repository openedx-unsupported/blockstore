"""
This is how we model any external entity that can be tagged.
"""
from typing import NamedTuple

from django.db import models

from .common import MAX_CHAR_FIELD_LENGTH


class EntityId(NamedTuple):
    """
    A tuple which uniquely identifies an entity. An entity is some
    person/place/thing in an external system which has a type (e.g. "XBlock" and
    an ID).
    """
    entity_type: str
    external_id: str


class Entity(models.Model):
    """
    An entity that can be tagged. An entity is some person/place/thing in an
    external system which has a type (e.g. "XBlock" and an ID).

    Generally use Entity.get(EntityId(entity_type=..., external_id=...)) to work
    with Entity objects.
    """
    # The integer ID, used only for foreign keys. Never expose this via an
    # API, as the [entity_type, external_id] tuple is the more relevant key
    _id = models.BigAutoField(primary_key=True, db_column='id')
    entity_type = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH)
    external_id = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH)

    tags = models.ManyToManyField('Tag')

    class Meta:
        unique_together = (
            ('entity_type', 'external_id'),
        )
        db_table = 'tagstore_entity'
        verbose_name_plural = 'Entities'

    @classmethod
    def get(cls, entity_id: EntityId):
        """ Helper method to get_or_create an Entity based on its EntityId """
        entity, _ = cls.objects.get_or_create(**entity_id._asdict())
        return entity

    @property
    def id(self) -> EntityId:
        return EntityId(entity_type=self.entity_type, external_id=self.external_id)

    def __str__(self) -> str:
        return "{} Entity ({})".format(self.entity_type, self.external_id)

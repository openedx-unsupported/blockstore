""" Core models. """
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    """Custom user model for use with OpenID Connect."""
    full_name = models.CharField(_('Full Name'), max_length=255, blank=True, null=True)

    @property
    def access_token(self):
        """ Returns an OAuth2 access token for this user, if one exists; otherwise None.

        Assumes user has authenticated at least once with edX Open ID Connect.
        """
        try:
            return self.social_auth.first().extra_data[u'access_token']
        except Exception:  # pylint: disable=broad-except
            return None

    class Meta(object):
        get_latest_by = 'date_joined'

    def get_full_name(self):
        return self.full_name or super().get_full_name()

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.get_full_name())


class Tag(models.Model):
    """Tag for marking content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('name',)

    def get_full_name(self):
        return self.name

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.get_full_name())


class Unit(models.Model):
    """Learning Object: a unit of learnable content."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    summary = models.TextField()
    author = models.ForeignKey('User', models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField(Tag)

    class Meta:
        ordering = ('id',)

    def get_full_name(self):
        return self.title

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.get_full_name())


class Pathway(models.Model):
    """Learning Context: a group of units joined together into a larger learning experience."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey('User', models.SET_NULL, blank=True, null=True)
    units = models.ManyToManyField(Unit, through='PathwayUnit')
    _tags = models.ManyToManyField(Tag, through='PathwayTag')

    class Meta:
        ordering = ('id',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._first_unit = None

    def get_full_name(self):
        return _("Pathway: {title}").format(  # pylint: disable=no-member
            title=self.title,
        )

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.get_full_name())

    @property
    def first_unit(self):
        if self._first_unit is None:
            self._first_unit = self.units.first() or Unit()
        return self._first_unit

    @property
    def title(self):
        """Returns the first unit's title"""
        return self.first_unit.title

    @property
    def summary(self):
        """Returns the first unit's summary"""
        return self.first_unit.summary

    @property
    def tags(self):
        """Returns this pathway's tags combined with the tags of unit in this pathway."""
        return Tag.objects.filter(
            models.Q(unit__in=self.units.all()) |
            models.Q(id__in=self._tags.all())
         ).distinct().order_by('name')


class PathwayTag(models.Model):
    """Provides Pathway Tags"""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE)

    class Meta:
        ordering = ('tag__name', 'pathway')

    def get_full_name(self):
        return _("{pathway} -> {tag}").format(  # pylint: disable=no-member
            pathway=self.pathway,
            tag=self.tag,
        )

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.get_full_name())


class PathwayUnit(models.Model):
    """Provides (optional) ordering of units in a Pathway"""
    index = models.PositiveIntegerField(null=True, default=None)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE)

    class Meta:
        ordering = ('index', 'pathway', 'unit')

    def get_full_name(self):
        return _("{pathway}[{index}] -> {unit}").format(  # pylint: disable=no-member
            pathway=self.pathway,
            unit=self.unit,
            index=self.index,
        )

    @python_2_unicode_compatible
    def __str__(self):
        return str(self.get_full_name())

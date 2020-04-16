""" Template tags for Django admin. """
from django import template

from tagstore.backends.django import DjangoTagstore

register = template.Library()


@register.inclusion_tag('admin/tagstore_django/tag_hierarchy.html')
def tag_hierarchy(taxonomy_uid):
    """ Renders a hierarchical view in HTML of Tag objects. """
    tagstore = DjangoTagstore()
    if taxonomy_uid:
        tags = tagstore.get_tags_in_taxonomy_hierarchically_as_dict(taxonomy_uid)
        return {'tags': tags, 'taxonomy_uid': taxonomy_uid}
    else:
        return None

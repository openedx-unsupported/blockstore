""" Template tags for Django admin. """
from django import template

from tagstore.backends.django import DjangoTagstore
from tagstore.backends.tagstore_django.models import Taxonomy

register = template.Library()


@register.inclusion_tag('admin/tagstore_django/tag_hierarchy.html')
def tag_hierarchy():
    """ Renders a hierarchical view in HTML of all Tag objects. """
    tagstore = DjangoTagstore()
    taxonomies = Taxonomy.objects.all()
    tags_by_taxonomy = []
    for taxonomy in taxonomies:
        taxonomy_detail = {'name': taxonomy.name, 'id': taxonomy.id, 'tags': []}
        taxonomy_detail['tags'].append(
            tagstore.get_tags_in_taxonomy_hierarchically_as_dict(taxonomy.id)
        )
        tags_by_taxonomy.append(taxonomy_detail)
    return {'tags': tags_by_taxonomy}

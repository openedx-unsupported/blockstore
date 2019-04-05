""" Template tags for Django admin. """
from django import template

from tagstore.models import Taxonomy, TaxonomyId

register = template.Library()


@register.inclusion_tag('admin/tagstore/tag_hierarchy.html')
def tag_hierarchy(taxonomy_id: TaxonomyId):
    """ Renders a hierarchical view in HTML of Tag objects. """
    if taxonomy_id:
        taxonomy = Taxonomy.objects.get(pk=taxonomy_id)
        tags = taxonomy.get_tags_hierarchically_as_dict()
        return {'tags': tags, 'taxonomy_id': taxonomy_id}
    else:
        return

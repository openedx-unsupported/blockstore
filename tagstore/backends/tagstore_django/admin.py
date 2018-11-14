""" Admin for tags. """

from django import forms
from django.contrib import admin

from tagstore.backends.django import DjangoTagstore
# from tagstore.models import EntityId

from .models import Taxonomy, Tag, MAX_CHAR_FIELD_LENGTH


class CustomTagAdminForm(forms.ModelForm):
    """ Sets an extra field `parent` which does not exist in Tag. """
    parent = forms.CharField(max_length=MAX_CHAR_FIELD_LENGTH, required=False)

    def __init__(self, *args, **kwargs):
        """ Adds the parent name, if it exists, to the edit tag form. """
        parent_tag = ''
        if 'instance' in kwargs and kwargs['instance'] is not None:
            if kwargs['instance'].parent_tag_tuple:
                parent_tag = kwargs['instance'].parent_tag_tuple.name
        super(CustomTagAdminForm, self).__init__(*args, **kwargs)
        self.fields['parent'].widget.attrs.update({'value': parent_tag})

    # TODO: create a dry run flag for add_tag_to_taxonomy which
    # can be used to validate before attempting to save


class TagAdmin(admin.ModelAdmin):
    """ Controls display and saving of Tag model objects. """
    list_filter = ('taxonomy',)
    list_display = ('name', 'path', 'taxonomy')
    readonly_fields = ('path',)
    search_fields = ('path',)
    form = CustomTagAdminForm

    def has_change_permission(self, request, obj=None):
        """ Makes Tag objects uneditable. """
        return False

    def save_model(self, request, obj, form, change):
        """ Uses the tagstore API to save new tags to the database. """
        tagstore = DjangoTagstore()
        taxonomy = form.cleaned_data['taxonomy']
        name = form.cleaned_data['name']
        parent_tag_str = form.cleaned_data['parent']
        parent = tagstore.get_tag_in_taxonomy(parent_tag_str, taxonomy.id)
        try:
            tagstore.add_tag_to_taxonomy(name, taxonomy.id, parent)
        except ValueError:
            pass

    # def delete_model(self, request, obj):
    #     """ TODO: Uses the tagstore API to delete tags from the database. """
    #     super(TagAdmin, self).delete_model(request, obj)


class TagInline(admin.TabularInline):
    """ TODO: Allows bulk editing of Tag objects on the edit taxonomy page. """
    parent = forms.CharField(max_length=MAX_CHAR_FIELD_LENGTH, required=False)
    model = Tag
    readonly_fields = ('path',)
    form = CustomTagAdminForm


class TaxonomyAdmin(admin.ModelAdmin):
    """ Controls display and saving of Taxonomy model objects. """
    # inlines = [TagInline]
    pass


admin.site.register(Tag, TagAdmin)
# admin.site.register(Entity)
admin.site.register(Taxonomy, TaxonomyAdmin)

""" Admin for bundles. """

from pathlib import Path
import json

from django.contrib import admin
from django.utils.html import format_html, format_html_join

from .models import Bundle, BundleVersion, Collection
from .store import BundleJSONEncoder


class BundleVersionInline(admin.StackedInline):
    """ BundleVersion inline view. """

    model = BundleVersion
    readonly_fields = (
        'version_num',
        'snapshot_digest',
        'change_description',
        'snapshot_data',
        'raw_summary',
    )

    def snapshot_data(self, obj):
        """
        Readable table describing the files in the BundleSnapshot this
        BundleVersion references.
        """
        snapshot = obj.snapshot()
        header_html = format_html("<tr><th>File</th><th>Public</th><th>Size</th><th>Hash Digest</th></tr>")
        rows_html = format_html_join(
            '\n',
            '<tr><td><a href="{}" download="{}">{}</td><td>{}</td><td>{}</td><td>{}</td></tr>',
            (
                (
                    snapshot.url(info.path),
                    Path(info.path).name,
                    info.path,
                    info.public,
                    info.size,
                    info.hash_digest.hex(),
                )
                for info in sorted(snapshot.files.values())
            )
        )
        return format_html("<table>{}{}</table>", header_html, rows_html)

    def raw_summary(self, obj):
        """
        Raw dump of BundleSnapshot data, though formatted more nicely.
        """
        json_str = json.dumps(
            obj.snapshot(), cls=BundleJSONEncoder, indent=4, sort_keys=True
        )
        return format_html("<pre>{}</pre>", json_str)

    def has_add_permission(self, request):
        return False


class BundleAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'slug', 'title')
    readonly_fields = ('uuid',)
    inlines = (BundleVersionInline,)
    search_fields = ('uuid', 'title')


class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'uuid')


admin.site.register(Bundle, BundleAdmin)
admin.site.register(Collection, CollectionAdmin)

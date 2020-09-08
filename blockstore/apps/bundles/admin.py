""" Admin for bundles. """

from pathlib import Path
import json

from django.contrib import admin
from django.utils.html import format_html, format_html_join

from .models import Bundle, BundleVersion, Collection, Draft
from .store import BundleDataJSONEncoder, SnapshotRepo


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
    ordering = ('-pk',)
    classes = ['collapse']

    def snapshot_data(self, obj):
        """
        Readable table describing the files in the Snapshot this
        BundleVersion references.
        """
        snapshot = obj.snapshot()
        store = SnapshotRepo()
        header_html = format_html("<tr><th>File</th><th>Public</th><th>Size</th><th>Hash Digest</th></tr>")
        rows_html = format_html_join(
            '\n',
            '<tr><td><a href="{}" download="{}">{}</td><td>{}</td><td>{}</td><td>{}</td></tr>',
            (
                (
                    store.url(snapshot, info.path),
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
        Raw dump of Snapshot data, though formatted more nicely.
        """
        json_str = json.dumps(
            obj.snapshot(), cls=BundleDataJSONEncoder, indent=4, sort_keys=True
        )
        return format_html("<pre>{}</pre>", json_str)

    def has_add_permission(self, request, obj=None):
        return False


class DraftInline(admin.StackedInline):
    """Draft inline view. """
    model = Draft
    classes = ['collapse']

    def get_max_num(self, request, obj=None, **kwargs):
        if obj is None:
            return 3
        return max(obj.drafts.count(), 3)


class BundleAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'slug', 'title')
    readonly_fields = ('uuid',)
    inlines = (BundleVersionInline, DraftInline)
    search_fields = ('uuid', 'title')


class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'uuid')


admin.site.register(Bundle, BundleAdmin)
admin.site.register(Collection, CollectionAdmin)

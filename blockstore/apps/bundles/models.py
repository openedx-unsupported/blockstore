"""
Bundles are collections of files that are versioned together, and are the
central thing that Blockstore manages. The models are here to manage some of the
metadata around Bundles, their ownership, permissions, etc. The actual contents
of what's inside the Bundles is handled through the bundles.store module.

# Scaling Considerations

Taking edx.org as measuring stick, we want to be able to easily support:
* 10K+ courses
* 10K+ content libraries
* ~20 Sequences in each course on average, but allowing for a max of 100
* ~50+ TB of data (mostly video)
* 10s to 100s of millions of Content Bundles
* ~20-30 versions per Bundle on average
* Up to 100 files per bundle

# MySQL Notes

Note that while this data model should work in MySQL or PostgreSQL, much of it
is specifically designed around making MySQL work well at scale. Open edX by
default uses MySQL for historical reasons (PostgreSQL wasn't offered on AWS RDS
at the time edx-platform was created), and we're not looking to introduce the
operational overhead of requiring another data store.

But this will make the schema look a bit weird. Some MySQL-isms:

1) MySQL insert performance breaks down if you use UUIDs for a primary key. The
primary key is used as the clustering index, meaning that MySQL will store table
data in primary key order. If that ordering is random, your data is much more
fragmented. For that reason, when UUIDs are needed, they're used as secondary
unique indexes. Those indexes may get fragmented, but it will have less of an
impact overall, and we're never going to do range queryies on UUIDs anyhow. Side
note: If you use UUID1 and get fancy with bit re-ordering, you can get around
this, but it adds complexity to the code and prevents us from using the randomly
generated UUID4.

2) Another reason we're keeping UUIDs out of the primary key is because all
secondary keys in MySQL's InnoDB storage engine store a copy of the primary key
entry as well. A bigint is 8 bytes, and even an optimally packed UUID is still
16 bytes.

3) Our repos generally have VARCHAR(255) everywhere because MySQL's "utf8"
encoding uses a max of three bytes per character (note: meaning it's not really
UTF-8), and 255 * 3 = 765 bytes. The largest size for any column in an InnoDB
index is 767 bytes. However, if we use MySQL's "utf8mb4", a.k.a. "actually
UTF-8", that limit goes down to 191 bytes (191 * 4 = 764). Because 191 is a
peculiar and difficult to remember number for an API, I am somewhat arbitrarily
using 180 as a reasonable sounding number below the limit.

4) There are a number of models that are made bigint when they don't strictly
need to be (Bundles are unlikely to grow to that size, for instance), because
it's not *that* expensive, and migrating data once it gets that large is a pain.
"""
import uuid

from django.db import models
from django.dispatch import receiver

from .store import BundleDataStore, snapshot_created

MAX_CHAR_FIELD_LENGTH = 180


class Collection(models.Model):
    """
    Administrative grouping for Bundles: policy, permissions, licensing, etc.

    Each Bundle belongs to exactly one Collection.

    UUIDs should be treated as immutable, and external references (e.g. URLs)
    should use them.

    Target Scale: 100K rows
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH, db_index=True)

    def __str__(self):
        return "{} - {}".format(self.uuid, self.title)


class Bundle(models.Model):
    """
    The UUID of a Bundle should be treated as immutable, but any other part of
    the bundle can be modified without breaking anything.

    Target Scale: 100M rows
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=MAX_CHAR_FIELD_LENGTH, db_index=True)

    collection = models.ForeignKey(
        Collection, related_name="bundles", related_query_name="bundle", editable=False
    )

    slug = models.SlugField(allow_unicode=True, unique=True)  # For pretty URLs
    description = models.TextField(max_length=10_000)

    def __str__(self):
        return "Bundle {} - {}".format(self.uuid, self.slug)


class BundleVersion(models.Model):
    """
    The contents of a BundleVersion are immutable (the snapshot it points to),
    but the metadata about a BundleVersion (e.g. change_description) can be
    changed. Other entities in the system that need to attach metadata to
    versions of Bundles should use this model and not reference BundleSnapshots
    directly.

    Target Scale: 1B rows
    """
    id = models.BigAutoField(primary_key=True)
    bundle = models.ForeignKey(
        Bundle, related_name="versions", related_query_name="version", editable=False
    )
    version_num = models.PositiveIntegerField(editable=False)
    snapshot_digest = models.BinaryField(max_length=20, db_index=True, editable=False)
    change_description = models.TextField(max_length=1_000, blank=True)

    class Meta:
        unique_together = (
            ("bundle", "version_num"),
        )

    @staticmethod
    @receiver(snapshot_created)
    def listen_for_snapshot_creation(**kwargs):
        """
        The BundleStore layer doesn't know we exist, but it emits signals when a
        new BundleSnapshot is created. We listen for that signal and create a
        new BundleVersion that points to it.
        """
        bundle_uuid = kwargs['bundle_uuid']
        snapshot_digest = kwargs['hash_digest']

        bundle = Bundle.objects.get(uuid=bundle_uuid)
        versions = list(bundle.versions.order_by('-version_num')[:1])
        next_version_num = versions[0].version_num + 1 if versions else 1

        bundle.versions.create(
            version_num=next_version_num,
            snapshot_digest=snapshot_digest,
        )

    def snapshot(self):
        store = BundleDataStore()
        return store.snapshot(self.bundle.uuid, self.snapshot_digest)

    def __str__(self):
        return f"{self.bundle.uuid}@{self.version_num}"


class BundleLink(models.Model):
    """
    A lightweight representation of the Link between two Bundles.

    The most common lookup use case for this will be to notify or report on all
    the Bundles that link *to* a particular Bundle, for notification and
    reporting purposes. We track things at the Bundle level of granularity
    because doing so at the BundleVersion level would take up much more space
    with limited benefits. All precise version dependencies are captured at
    the BundleData layer, where it can be represented more cheaply.
    """
    id = models.BigAutoField(primary_key=True)

    # Commenting for now because we haven't really implemented any of this yet.
    # lender = models.ForeignKey(Bundle)
    # borrower = models.ForeignKey(Bundle)

    # To separate historical Links (useful for reporting) vs. actively used
    # Links (useful for notifications). If you *used* to use a Bundle but no
    # longer do, you don't care about update notifications.
    uses_latest = models.BooleanField()

#    class Meta:
#        unique_together = (
#            ("borrower", "lender")
#        )
#        index_together = (
#            ("lender", "uses_latest", "borrower")
#        )

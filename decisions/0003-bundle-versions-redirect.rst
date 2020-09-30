========================================================================
Bundle Version pointing to redirect endpoint instead of direct file path
========================================================================

-------
Problem
-------

Bundle Versions are stored as files using django's storage backend, and for this it's very common to use
AWS S3 (used by Open edX that way). To allow the content owner to control access to these files, most object
storage providers encourage or enforce the use of signed URLs that expire after a predetermined amount of time.

--------
Decision
--------

The BundleVersion endpoints should return bundle information as normal but instead of returning the direct
file path url, return a link to a new Blockstore endpoint that will redirect to the actual file path, making
the urls returned by our API always usable.

========================================================================
Bundle Version pointing to redirect endpoint instead of direct file path
========================================================================

-------
Problem
-------

Bundle Versions are stored as files using django's storage backend, and for this it's very common to use
AWS S3 (used by Open edX that way). As Blockstore can be used as an API, it's usual for clients to cache
these file urls, which could result in expired urls in the case of S3.

--------
Decision
--------

The BundleVersion endpoints should return bundle information as normal but instead of returning the bundle
file path url, return a link to a new Blockstore endpoint that will redirect to the actual file path, making
the urls returned by our API always usable.

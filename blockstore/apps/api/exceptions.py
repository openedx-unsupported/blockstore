"""
Exceptions that may be raised by the Blockstore API
"""


class BlockstoreException(Exception):
    pass


class NotFound(BlockstoreException):
    pass


class CollectionNotFound(NotFound):
    pass


class BundleNotFound(NotFound):
    pass


class BundleVersionNotFound(NotFound):
    pass


class DraftNotFound(NotFound):
    pass


class DraftHasNoChangesToCommit(Exception):
    pass


class BundleFileNotFound(NotFound):
    pass


class BundleStorageError(BlockstoreException):
    pass

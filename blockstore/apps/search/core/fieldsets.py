"""
Base FieldSets for search.
"""


class FieldSet:
    """
    A FieldSet is a collection of ElasticSearch fields which can be
    associated with an Index.
    """

    name = None  # A string used to namespace the fields.
    Document = None  # An ElasticSearch InnerDoc.
    Serializer = None  # A DRF Serializer for serializing and deserializing the Document.

The Search Engine Architecture.

Search is powered by [ElasticSearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/_basic_concepts.html).

* ES supports dynamic mapping for fields. However, dynamic mapping is not a good idea for following reasons:
  * Explicit mappings allow fine grained control over indexing and query behavior.
  * Fields have a memory and performance overhead so external services should not be allowed to add arbitrary fields.

https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html

* Each field in an index is backed by a Lucene field. Fields with the same name in different documents
  in an Index are backed by the same Lucene field and so must have the same datatype.
  https://www.elastic.co/guide/en/elasticsearch/reference/current/removal-of-types.html

* Documents in an index are distributed across shards.
  https://stackoverflow.com/a/15705989

* Relational capabilities are weak.
  https://www.elastic.co/blog/managing-relations-inside-elasticsearch

* Joins are really slow.
  https://www.elastic.co/guide/en/elasticsearch/reference/current/nested.html
  https://www.elastic.co/guide/en/elasticsearch/reference/current/parent-join.html#_parent_join_and_performance

* It is possible for a single search query to return data from multiple indexes. Whether it makes sense to have
  multiple indexes for our data can be investigated.

* Changing the number of shards or modifying existing field mappings requires creating a new index and
  copying over data. Migrations support will have to be added and will add quite a bit of complexity.
  https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html#_updating_existing_field_mappings

---------------------------------------

* Each Index has a Document class associated wih it. Each entity is denormalized into
  a single Document in an Index. It is possible to index one entity in multiple indices.

* It is expected that metadata for entities is going to come from different sources. For each source,
  there must exist a FieldSet which defines the fields for the data from that source. Each FieldSet can be
  associated with one or more Indices and is dynamically added to the Document for each of these Indices. This
  also makes it possible for FieldSets to be defined in plugins.

* The interface for both querying and modifying data in an Index is powered by DRF. Since ES stores JSON data,
  internal sources can also use the DRF views for adding metadata. This allows a single validation layer and
  uniform behavior for all sources.

* Each source should add metadata to a document via a PATCH request. Internal sources can just call the view
  methods.

* It will be possible to add a permissions layer in the future which will restrict sources to only
  be able to modify fields in certain FieldSets.

* For metadata values whose labels are mutable (e.g. author names) stable identifiers should be stored in the Index.
  This is because if the label changes, it would require updating all the related documents and have ES re-index them.

OLX Conventions
===================

* Nested XBlocks in separate OLX files can be referenced by adding a **path** attribute to the element which points
  to the relevant OLX file. The path can be to an OLX file in the same Bundle or in another Bundle.
* The path to an OLX file may be used as a component of the XBlock ID. Therefore moving an OLX file or changing its
  name will be equivalent to deleting the XBlock and creating a new one. A block element in an OLX file may
  also have an **id** attribute. The value of this attribute will be used when constructing the **block_key**.

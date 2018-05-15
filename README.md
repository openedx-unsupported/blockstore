Blockstore
==========

[![Circle CI](https://img.shields.io/circleci/project/open-craft/blockstore/master.svg)](https://circleci.com/gh/open-craft/blockstore/tree/master) 

[![Dependency Status](https://gemnasium.com/badges/github.com/open-craft/blockstore.svg)](https://gemnasium.com/github.com/open-craft/blockstore)

The `README.md` file should start with a brief description of the repository. It should make clear where this fits in to the overall Open edX codebase. You may also want to provide a brief overview of the code in this repository, including the main components and useful entry points for starting to understand the code in more detail, or link to a comparable description in your repo's docs.

How to Run
----------

This project uses python 3.  To build the requirements, run:

```bash
$ sudo apt-get install python3.x-dev libmysqlclient-dev  # replace 3.x with your version of python 3
$ mkvirtualenv --python=/path/to/python3 blockstore
(blockstore) $ make requirements
```

To run the service:
```python
(blockstore) $ ./manage.py runserver 0.0.0.0:8000
```

Visit http://localhost:8080/graphql to run the queries.  See the Docs tab for their structure.

Documentation
-------------

Documentation source is hosted in this repo's [`docs`](https://github.com/open-craft/blockstore/tree/master/docs)
directory.

To contribute, please open a PR against this repo.

License
-------

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. Please see the
[LICENSE](https://github.com/open-craft/blockstore/blob/master/LICENSE) file for details.

How To Contribute
-----------------

Contributions are welcome. Please read 
[How To Contribute](https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst) for details. Even though it was
written with ``edx-platform`` in mind, these guidelines should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email help@opencraft.com.

Get Help
--------

Ask questions and discuss this project on [Slack](https://openedx.slack.com/messages/general/) or in the 
[edx-code Google Group](https://groups.google.com/forum/#!forum/edx-code).

Blockstore
==========

[![Circle CI](https://img.shields.io/circleci/project/open-craft/blockstore/master.svg)](https://circleci.com/gh/open-craft/blockstore/tree/master) 

[![Dependency Status](https://gemnasium.com/badges/github.com/open-craft/blockstore.svg)](https://gemnasium.com/github.com/open-craft/blockstore)

Blockstore comprises Learning Units, Pathways, and various metadata used to store online learning materials.

How to Run
----------

This project uses python 3.  To build the requirements, run:

```bash
$ sudo apt-get install python3.x-dev libmysqlclient-dev  # replace 3.x with your version of python 3
$ mkvirtualenv --python=/path/to/python3 blockstore
(blockstore) $ make requirements
(blockstore) $ make migrate
(blockstore) $ ./manage.py createsuperuser  # if using Django Admin
```

To run the service:
```python
(blockstore) $ ./manage.py runserver 0.0.0.0:8000
```

Visit `/api-docs` to see the Swagger UI, or `/admin` to access the Django Admin.


Authentication
--------------

Set up an OAuth2 client on Open edX with the following settings, e.g.:

* Name: blockstore
* Url: http://localhost:18000/oauth2
* Redirect uri: http://localhost:8080/complete/edx-oidc/
* Client id: blockstore-client
* Client secret: blockstore-secret
* Client type: Confidential (Web applications)

Copy `blockstore/settings/private.py.example` to `blockstore/settings/private.py`, and update it, e.g.:
```python
SOCIAL_AUTH_EDX_OIDC_KEY = 'blockstore-client'
SOCIAL_AUTH_EDX_OIDC_SECRET = 'blockstore-secret'
SOCIAL_AUTH_EDX_OIDC_URL_ROOT = 'http://localhost:8000/oauth2'
SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL = 'http://localhost:8080/logout'
SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY = SOCIAL_AUTH_EDX_OIDC_SECRET

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
INTERNAL_IPS = ('localhost',)

# Port for running the React front-end
CORS_ORIGIN_WHITELIST = ['localhost:3000']
```

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

import os

from blockstore.settings.base import *


# MYSQL TEST DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'blockstore_test',
        'USER': environ.get('BLOCKSTORE_MYSQL_USER', 'blockstore_user'),
        'PASSWORD': environ.get('BLOCKSTORE_MYSQL_PASSWORD', 'blockstore_password'),
        'HOST': environ.get('BLOCKSTORE_MYSQL_HOST', 'datastore'),
        'PORT': int(environ.get('BLOCKSTORE_MYSQL_PORT', 3306)),
    },
}
# END MYSQL TEST DATABASE

# So we don't leave mix Bundle files from test runs with our local dev server.
DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'

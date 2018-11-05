import os

from blockstore.settings.base import *


# MYSQL TEST DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'blockstore_db'),
        'USER': os.environ.get('MYSQL_USER', 'root'),
        'PASSWORD': os.environ.get('MYSQL_ROOT_PASSWORD', ''),
        'HOST': os.environ.get('MYSQL_HOST', 'mysql'),
        'PORT': int(os.environ.get('MYSQL_PORT', '3306')),
    },
}
# END MYSQL TEST DATABASE

# So we don't leave mix Bundle files from test runs with our local dev server.
DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'

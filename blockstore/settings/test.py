import os

from blockstore.settings.base import *


# IN-MEMORY TEST DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}
# END IN-MEMORY TEST DATABASE

# So we don't leave mix Bundle files from test runs with our local dev server.
DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'

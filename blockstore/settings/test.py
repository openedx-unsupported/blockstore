from blockstore.apps.bundles.tests.storage_utils import create_timestamped_path
from blockstore.settings.base import *

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = {
    'class': 'logging.NullHandler',
}

# MYSQL TEST DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'blockstore_db'),
        'USER': os.environ.get('MYSQL_USER', 'root'),
        'PASSWORD': os.environ.get('MYSQL_ROOT_PASSWORD', ''),
        'HOST': os.environ.get('MYSQL_HOST', 'mysql57'),
        'PORT': int(os.environ.get('MYSQL_PORT', '3306')),
        'OPTIONS': {
            # Use a non-broken unicode encoding. See "mysql_unicode/migrations/0001_initial.py"
            # for details. Together with that migration, this setting will force the use of
            # the correct unicode implementation.
            # Note that this limits the length of InnoDB indexed columns to 191 characters.
            'charset': 'utf8mb4',
            'init_command': 'SET NAMES utf8mb4',
        },
    },
}
# END MYSQL TEST DATABASE

# Give each test run a separate storage space.
MEDIA_ROOT = create_timestamped_path("test_storage")

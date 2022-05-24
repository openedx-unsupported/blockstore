import os
import yaml

from blockstore.settings.base import *
from blockstore.settings.utils import get_env_setting


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

LOGGING['handlers']['local']['level'] = 'INFO'

CONFIG_FILE = get_env_setting('BLOCKSTORE_CFG')
with open(CONFIG_FILE) as f:
    config_from_yaml = yaml.safe_load(f)
    vars().update(config_from_yaml)

DB_OVERRIDES = dict(
    PASSWORD=os.environ.get('DB_MIGRATION_PASS', DATABASES['default']['PASSWORD']),
    ENGINE=os.environ.get('DB_MIGRATION_ENGINE', DATABASES['default']['ENGINE']),
    USER=os.environ.get('DB_MIGRATION_USER', DATABASES['default']['USER']),
    NAME=os.environ.get('DB_MIGRATION_NAME', DATABASES['default']['NAME']),
    HOST=os.environ.get('DB_MIGRATION_HOST', DATABASES['default']['HOST']),
    PORT=os.environ.get('DB_MIGRATION_PORT', DATABASES['default']['PORT']),
    OPTIONS=os.environ.get('DB_MIGRATION_OPTIONS', DATABASES['default']['OPTIONS']),
)

for override, value in DB_OVERRIDES.items():
    DATABASES['default'][override] = value

from os import environ
import yaml

from blockstore.settings.base import *
from blockstore.settings.utils import get_env_setting


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

LOGGING['handlers']['console']['level'] = 'INFO'

CONFIG_FILE = get_env_setting('BLOCKSTORE_CFG')
with open(CONFIG_FILE, encoding='utf-8') as f:
    config_from_yaml = yaml.load(f)
    vars().update(config_from_yaml)

DB_OVERRIDES = dict(
    PASSWORD=environ.get('DB_MIGRATION_PASS', DATABASES['default']['PASSWORD']),
    ENGINE=environ.get('DB_MIGRATION_ENGINE', DATABASES['default']['ENGINE']),
    USER=environ.get('DB_MIGRATION_USER', DATABASES['default']['USER']),
    NAME=environ.get('DB_MIGRATION_NAME', DATABASES['default']['NAME']),
    HOST=environ.get('DB_MIGRATION_HOST', DATABASES['default']['HOST']),
    PORT=environ.get('DB_MIGRATION_PORT', DATABASES['default']['PORT']),
)

for override, value in DB_OVERRIDES.items():
    DATABASES['default'][override] = value

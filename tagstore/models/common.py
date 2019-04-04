"""
Common definitions and constants used by Tagstore models
"""
# If MySQL is configured to use utf8mb4 (correct utf8), indexed
# columns have a max length of 191. Until Django supports limiting index
# length to 191 characters, we need to limit the value length to below
# 191 characters, for any column that might be indexed.
# (https://code.djangoproject.com/ticket/18392#comment:3)
MAX_CHAR_FIELD_LENGTH = 180

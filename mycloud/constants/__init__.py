import os

import appdirs

DATA_DIR = appdirs.user_data_dir('mycloud')
TOKEN_DIR = os.path.join(DATA_DIR, 'tokens')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

SERVICE_NAME = 'myCloud'
MY_CLOUD_BIG_FILE_CHUNK_SIZE = 1024 * 1024 * 256
CHUNK_SIZE = 1024
BASE_DIR = '/Drive/'
PARTIAL_EXTENSION = '.partial'
START_NUMBER_LENGTH = 8
RETRY_COUNT = 3
SAVE_FREQUENCY = 10
USE_TOKEN_CACHE = True
TOKEN_CACHE_FOLDER = TOKEN_DIR

AUTHENTICATION_INFO_LOCATION = os.path.join(DATA_DIR, 'auth.json')

WEBDAV_CONFIG_LOCATION = os.path.join(DATA_DIR, 'webdav.json')

VERSION_HASH_LENGTH = 10
METADATA_FILE_NAME = 'mycloud_metadata.json'
CACHED_TOKEN_IDENTIFIER = 'CACHED'
WAIT_TIME_MULTIPLIER = 1.1
MAX_TIMEOUT = 15

REPLACEMENT_TABLE = [
    {
        "character": "~",
        "replacement": "-"
    }
]

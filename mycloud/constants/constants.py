import appdirs
import os


data_dir = appdirs.user_data_dir('.mycloud', 'thomasgassmann')
token_dir = os.path.join(data_dir, 'tokens')


MY_CLOUD_BIG_FILE_CHUNK_SIZE = 1024 * 1024 * 256
ENCRYPTION_CHUNK_LENGTH = 1024
BASE_DIR = '/Drive/'
PARTIAL_EXTENSION = '.partial'
START_NUMBER_LENGTH = 8
RETRY_COUNT = 3
SAVE_FREQUENCY = 10
USE_TOKEN_CACHE = True
TOKEN_CACHE_FOLDER = token_dir

REQUEST_STATISTICS_LOCATION = os.path.join(data_dir, 'request_statistics.json')
REQUEST_COUNT_IDENTIFIER = 'counts'

VERSION_HASH_LENGTH = 10
METADATA_FILE_NAME = 'mycloud_metadata.json'
CACHED_TOKEN_IDENTIFIER = 'CACHED'
AES_EXTENSION = '.aes'
DEFAULT_VERSION = '1.0'
WAIT_TIME_MULTIPLIER = 1.1
MAX_THREADS_FOR_REMOTE_FILE_CONVERSION = 10
MAX_TIMEOUT = 15
RESET_SESSION_EVERY = 2500

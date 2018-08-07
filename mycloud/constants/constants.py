import appdirs
import os


data_dir = appdirs.user_data_dir('.mycloud', 'thomasgassmann')
token_dir = os.path.join(data_dir, 'tokens')


MY_CLOUD_BIG_FILE_CHUNK_SIZE = 1024 * 1024
ENCRYPTION_CHUNK_LENGTH = 1024
BASE_DIR = '/Drive/'
PARTIAL_EXTENSION = '.partial'
START_NUMBER_LENGTH = 8
RETRY_COUNT = 3
SAVE_FREQUENCY = 10
USE_TOKEN_CACHE = True
TOKEN_CACHE_FOLDER = token_dir

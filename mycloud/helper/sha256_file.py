import hashlib
import os
from mycloud.helper import operation_timeout
from mycloud.logger import log
from mycloud.constants import ENCRYPTION_CHUNK_LENGTH


cached_hashes = {
}


def sha256_file(local_file: str):
    # TODO: check possibility to read file just once in upload loop and calculate hash on the fly:
    # Problem: hash needs to be known before upload -> Upload files and rename afterwards?
    def read_file(x):
        return x['file'].read(x['length'])
    sha = hashlib.sha256()
    time = operation_timeout(lambda x: os.path.getmtime(
        x['file']), file=local_file)
    if local_file in cached_hashes and cached_hashes[local_file]['time'] >= time:
        return cached_hashes[local_file]['hash']
    stream = operation_timeout(lambda x: open(
        x['file'], 'rb'), file=local_file)
    file_buffer = operation_timeout(
        read_file, file=stream, length=ENCRYPTION_CHUNK_LENGTH)
    read_length = 0
    file_size = operation_timeout(lambda x: os.stat(x['file']).st_size, file=local_file)
    percentage = None
    while len(file_buffer) > 0:
        sha.update(file_buffer)
        file_buffer = operation_timeout(
            read_file, file=stream, length=ENCRYPTION_CHUNK_LENGTH)
        read_length += ENCRYPTION_CHUNK_LENGTH
        if (read_length / ENCRYPTION_CHUNK_LENGTH) % 1000 == 0:
            percentage = '{0:.2f}'.format((read_length / file_size) * 100)
            log(f'Hashing file {local_file}: {percentage}% complete...', end='\r')
    log(f'Hashing file {local_file}: {percentage}% complete...', end='\n')
    stream.close()
    digested = sha.hexdigest()
    cached_hashes[local_file] = {
        'hash': digested,
        'time': time
    }
    return digested

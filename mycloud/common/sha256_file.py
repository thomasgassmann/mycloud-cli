import hashlib
import os
import logging
from mycloud.common import operation_timeout
from mycloud.constants import ENCRYPTION_CHUNK_LENGTH


CACHED_HASHES = {}


def sha256_file(local_file: str):
    def read_file(params):
        return params['file'].read(params['length'])
    sha = hashlib.sha256()
    time = operation_timeout(lambda x: os.path.getmtime(
        x['file']), file=local_file)
    if local_file in CACHED_HASHES and CACHED_HASHES[local_file]['time'] >= time:
        return CACHED_HASHES[local_file]['hash']
    stream = operation_timeout(lambda x: open(
        x['file'], 'rb'), file=local_file)
    file_buffer = operation_timeout(
        read_file, file=stream, length=ENCRYPTION_CHUNK_LENGTH)
    read_length = 0
    file_size = operation_timeout(
        lambda x: os.stat(x['file']).st_size, file=local_file)
    percentage = None
    while any(file_buffer):
        sha.update(file_buffer)
        file_buffer = operation_timeout(
            read_file, file=stream, length=ENCRYPTION_CHUNK_LENGTH)
        if (read_length / ENCRYPTION_CHUNK_LENGTH) % 1000 == 0:
            percentage = '{0:.2f}'.format((read_length / file_size) * 100)
            print('Hashing file {}: {}% complete...'.format(
                local_file, percentage), end='\r')
        read_length += ENCRYPTION_CHUNK_LENGTH
    print('Hashing file {}: {}% complete...'.format(
        local_file, percentage), end='\n')
    stream.close()
    digested = sha.hexdigest()
    CACHED_HASHES[local_file] = {
        'hash': digested,
        'time': time
    }
    return digested

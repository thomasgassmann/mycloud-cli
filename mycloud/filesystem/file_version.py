from abc import ABC, abstractmethod
import hashlib
import os
from mycloud.helper import operation_timeout
from mycloud.constants import ENCRYPTION_CHUNK_LENGTH, VERSION_HASH_LENGTH


class CalculatableVersion(ABC):

    @abstractmethod
    def calculate_version(self):
        raise NotImplementedError()


class BasicStringVersion(CalculatableVersion):

    def __init__(self, version: str):
        self._version = version

    def calculate_version(self):
        return self._version


class HashCalculatedVersion(CalculatableVersion):

    def __init__(self, local_file: str):
        self.local_file = local_file
        self._cached_hash = None

    def calculate_version(self):
        if self._cached_hash is None:
            self._calculate_hash()
        return self._cached_hash

    def _calculate_hash(self):
        def read_file(x):
            return x['file'].read(x['length'])
        sha = hashlib.sha256()
        stream = operation_timeout(lambda x: open(
            x['file'], 'rb'), file=self.local_file)
        time = operation_timeout(lambda x: os.path.getmtime(
            x['file']), file=self.local_file)
        file_buffer = operation_timeout(
            read_file, file=stream, length=ENCRYPTION_CHUNK_LENGTH)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = operation_timeout(
                read_file, file=stream, length=ENCRYPTION_CHUNK_LENGTH)
        stream.close()
        sha.update(bytes(str(time).encode()))
        self._cached_hash = sha.hexdigest()[:VERSION_HASH_LENGTH]

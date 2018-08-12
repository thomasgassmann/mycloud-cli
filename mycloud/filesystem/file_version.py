from abc import ABC, abstractmethod
import hashlib
import os
from mycloud.helper import operation_timeout, sha256_file
from mycloud.logger import log
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

    def calculate_version(self):
        return sha256_file(self.local_file)[:VERSION_HASH_LENGTH]

    def get_hash(self):
        # TODO: calculate hash in main loop as well, don't read file twice
        return sha256_file(self.local_file)
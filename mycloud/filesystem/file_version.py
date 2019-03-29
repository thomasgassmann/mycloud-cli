from abc import ABC, abstractmethod
from mycloud.common import sha256_file
from mycloud.constants import VERSION_HASH_LENGTH


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
        return sha256_file(self.local_file)

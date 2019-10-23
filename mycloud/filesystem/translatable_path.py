import os
from abc import ABC, abstractmethod
from mycloud.mycloudapi import ObjectResourceBuilder
from mycloud.common import operation_timeout
from mycloud.filesystem.file_version import HashCalculatedVersion
from mycloud.constants import MY_CLOUD_BIG_FILE_CHUNK_SIZE


class TranslatablePath(ABC):

    @abstractmethod
    def calculate_remote(self):
        raise NotImplementedError()

    @abstractmethod
    def calculate_properties(self):
        raise NotImplementedError()


class BasicRemotePath(TranslatablePath):

    def __init__(self, object_resource: str):
        self._object_resource = object_resource

    def calculate_remote(self):
        return self._object_resource

    def calculate_properties(self):
        return {}


class LocalTranslatablePath(TranslatablePath):

    def __init__(self, resource_builder: ObjectResourceBuilder, local_file: str, hash_calculatable_version: HashCalculatedVersion = None):
        self._resource_builder = resource_builder
        self._local_file = local_file
        self._calculatable_version = hash_calculatable_version

    def calculate_remote(self):
        return self._resource_builder.build_remote_file(self._local_file)

    def calculate_properties(self):
        dictionary = {}
        dictionary['local'] = self._local_file
        dictionary['remote_base'] = self._resource_builder.mycloud_dir
        dictionary['local_base'] = self._resource_builder.base_dir
        dictionary['chunk_size'] = MY_CLOUD_BIG_FILE_CHUNK_SIZE
        dictionary['size'] = operation_timeout(
            lambda x: os.stat(x['path']).st_size, path=self._local_file)
        dictionary['ctime'] = operation_timeout(
            lambda x: os.path.getctime(x['file']), file=self._local_file)
        dictionary['utime'] = operation_timeout(
            lambda x: os.path.getmtime(x['file']), file=self._local_file)
        if self._calculatable_version is not None:
            dictionary['hash'] = self._calculatable_version.get_hash()
        return dictionary

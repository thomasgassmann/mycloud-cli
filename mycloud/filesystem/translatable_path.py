import os
from abc import ABC, abstractmethod
from mycloud.mycloudapi import ObjectResourceBuilder
from mycloud.helper import operation_timeout


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

    def __init__(self, resource_builder: ObjectResourceBuilder, local_file: str):
        self._resource_builder = resource_builder
        self._local_file = local_file

    def calculate_remote(self):
        return self._resource_builder.build_remote_file(self._local_file)

    def calculate_properties(self):
        dictionary = {}
        dictionary['local'] = self._local_file
        dictionary['remote_base'] = self._resource_builder.mycloud_dir
        dictionary['local_base'] = self._resource_builder.base_dir
        dictionary['ctime'] = operation_timeout(
            lambda x: os.path.getctime(x['file']), file=self._local_file)
        dictionary['utime'] = operation_timeout(
            lambda x: os.path.getmtime(x['file']), file=self._local_file)
        return dictionary

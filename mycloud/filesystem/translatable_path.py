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

    def __init__(self, local_base: str, mycloud_base: str, local_file: str):
        if not mycloud_base.endswith('/'):
            raise ValueError('mycloud_base must be a directory')
        self.local_base = local_base
        self.mycloud_base = mycloud_base
        self.local_file = local_file

    def calculate_remote(self):
        builder = ObjectResourceBuilder(self.local_base, self.mycloud_base)
        return builder.build_remote_file(self.local_file)

    def calculate_properties(self):
        dictionary = {}
        dictionary['local'] = self.local_file
        dictionary['remote_base'] = self.mycloud_base
        dictionary['local_base'] = self.local_base
        dictionary['ctime'] = operation_timeout(
            lambda x: os.path.getctime(x['file']), file=self.local_file)
        dictionary['utime'] = operation_timeout(
            lambda x: os.path.getmtime(x['file']), file=self.local_file)
        return dictionary

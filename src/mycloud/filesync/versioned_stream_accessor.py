from streamapi import CloudStreamAccessor, CloudStream
from mycloudapi import ObjectResourceBuilder
from constants import START_NUMBER_LENGTH, PARTIAL_EXTENSION
from helper import operation_timeout
import os
import hashlib as hash


class VersionedCloudStreamAccessor(CloudStreamAccessor):

    def __init__(self, object_resource: str, cloud_stream: CloudStream, version: str):
        super().__init__(object_resource, cloud_stream)
        self._version = version

    
    def get_base_path(self):
        versioned_object_resource = ObjectResourceBuilder.combine_cloud_path(self._object_resource, self._version)
        return versioned_object_resource


    def get_part_file(self, index: int):
        formatted_part_index = format(index, f'0{START_NUMBER_LENGTH}d')
        base = ObjectResourceBuilder.combine_cloud_path(self.get_base_path(), 'parts')
        return ObjectResourceBuilder.combine_cloud_path(base, f'{self._base_name}-{formatted_part_index}{PARTIAL_EXTENSION}')

    
    @staticmethod
    def derive_version_from_file(path: str):
        def open_file(dict):
            return open(dict['file'], 'rb')

        def read_file(dict):
            return dict['file'].read(dict['length'])

        def get_time(dict):
            return os.path.getmtime(dict['file'])
        
        sha = hash.sha256()
        BLOCKSIZE = 65536
        stream = operation_timeout(open_file, file=path)
        time = operation_timeout(get_time, file=path)
        file_buffer = operation_timeout(read_file, file=stream, length=BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = operation_timeout(read_file, file=stream, length=BLOCKSIZE)
        stream.close()
        sha.update(bytes(str(time).encode()))
        return sha.hexdigest()[:10]
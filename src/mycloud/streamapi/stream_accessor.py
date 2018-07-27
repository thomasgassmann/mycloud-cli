from streamapi.transforms import StreamTransform
from streamapi.stream_object import CloudStream
from mycloudapi import ObjectResourceBuilder
from constants import START_NUMBER_LENGTH, PARTIAL_EXTENSION
import os


class CloudStreamAccessor:
    
    def __init__(self, object_resource: str, cloud_stream: CloudStream):
        self._object_resource = object_resource
        self._cloud_stream = cloud_stream
        self._transforms = []
        if object_resource.endswith('/'):
            object_resource = object_resource[:-1]
        self._base_name = os.path.basename(object_resource)


    def finish(self):
        return


    def get_stream(self):
        return self._cloud_stream


    def add_transform(self, transform: StreamTransform):
        self._transforms.append(transform)


    def get_transforms(self):
        return self._transforms

    
    def get_base_path(self):
        return self._object_resource


    def get_part_file(self, index: int):
        formatted_part_index = format(index, f'0{START_NUMBER_LENGTH}d')
        return ObjectResourceBuilder.combine_cloud_path(self.get_base_path(), f'{self._base_name}-{formatted_part_index}{PARTIAL_EXTENSION}')
from mycloud.constants import PARTIAL_EXTENSION, START_NUMBER_LENGTH
from mycloud.mycloudapi import ObjectResourceBuilder
from mycloud.streamapi.stream_object import CloudStream
from mycloud.streamapi.transforms import StreamTransform


class CloudStreamAccessor:

    def __init__(self, object_resource: str, cloud_stream: CloudStream):
        self._object_resource = object_resource
        self._cloud_stream = cloud_stream
        self._transforms = []

    def get_stream(self):
        return self._cloud_stream

    def add_transform(self, transform: StreamTransform):
        self._transforms.append(transform)

    def get_transforms(self):
        return self._transforms

    def get_base_path(self):
        return self._object_resource

    def get_part_file(self, index: int):
        formatted_part_index = format(
            index, '0{}d'.format(START_NUMBER_LENGTH))
        return ObjectResourceBuilder.combine_cloud_path(
            self.get_base_path(), '{}{}'.format(formatted_part_index, PARTIAL_EXTENSION))

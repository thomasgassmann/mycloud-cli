import json
from abc import ABC, abstractmethod
from enum import Enum
from mycloudapi import ObjectResourceBuilder
from constants import START_NUMBER_LENGTH

# /Drive/object
# /Drive/object/version
# /Drive/object/version/metadata.json
# /Drive/object/version/parts
# /Drive/object/version/parts/part1.aes
# Change Tracking?

# or backwards compatibility?

class StreamDirection(Enum):
    Up = 0
    Down = 1


class StreamTransform(ABC):

    def __init__(self, name):
        self._name = name


    def get_name(self):
        return self._name


    @abstractmethod
    def reset_state(self):
        raise NotImplementedError()

    
    @abstractmethod
    def transform(self, byte_sequence: bytes) -> bytes:
        raise NotImplementedError()


class FileMetadata:
    
    def __init__(self, object_resource: str, version: str, overwrite: bool):
        self._object_resource = object_resource
        self._version = version
        self._overwrite = overwrite
        self._transforms = []
        self._properties = {}


    def add_transform(self, transform: StreamTransform):
        self._transforms.append(transform)

    
    def add_property(self, key: str, value: object):
        self._properties[key] = value


    def get_transforms(self):
        return self._transforms


    def is_overwrite_permissible(self):
        return self._overwrite


    def load_from_json_string(self, json_string: str):
        json_representation = json.loads(json_string)
        metadata = FileMetadata(json_representation['resource'], json_representation['version'], json_representation['overwritten'])

        for property_key, property_value in json_representation['properties'].iteritems():
            metadata.add_property(property_key, property_value)

        return metadata


    def get_json_representation(self):
        json_representation = {
            'version': self._version,
            'resource': self._object_resource,
            'overwritten': self._overwrite,
            'transforms': [transform.get_name() for transform in self._transforms],
            'properties': self._properties
        }
        return json_representation


    def get_metadata_location(self):
        return ObjectResourceBuilder.combine_cloud_path(self._get_versioned_base_folder(), 'mycloud_metadata.json')

    
    def get_parts_folder(self):
        return ObjectResourceBuilder.combine_cloud_path(self._get_versioned_base_folder(), 'parts')


    def get_part_file(self, index: int):
        formatted_part_index = format(index, f'0{START_NUMBER_LENGTH}d')
        return ObjectResourceBuilder.combine_cloud_path(self.get_parts_folder(), f'{formatted_part_index}.part')


    def _get_versioned_base_folder(self):
        return ObjectResourceBuilder.combine_cloud_path(self._object_resource, f'/versions/{self._version}')


class CloudStream(ABC):

    def __init__(self, stream_direction: StreamDirection, continued_append_starting_at_part_index: int):
        self.stream_direction = stream_direction
        self.continued_append_starting_at_part_index = continued_append_starting_at_part_index
        self._finished = False

    
    def finished(self):
        self._finished = True


    @abstractmethod    
    def close(self):
        raise NotImplementedError()


    def is_finished(self) -> bool:
        return self._finished


class UpStream(CloudStream):

    def __init__(self, continued_append_starting_at_part_index: int = 0):
        super().__init__(StreamDirection.Up, continued_append_starting_at_part_index)


    @abstractmethod
    def read(self, length: int):
        raise NotImplementedError()


class DownStream(CloudStream):

    def __init__(self, continued_append_starting_at_part_index: int = 0):
        super().__init__(StreamDirection.Down, continued_append_starting_at_part_index)


    @abstractmethod
    def write(self, data):
        raise NotImplementedError()
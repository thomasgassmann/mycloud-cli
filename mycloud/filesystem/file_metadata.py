import json
import time


class Version:

    def __init__(self, version: str, remote_path: str):
        self._version = version
        self._remote = remote_path
        self._part_files = []
        self._properties = {}
        self._transforms = []
        self._time = time.time()

    def add_part_file(self, remote_path: str):
        self._part_files.append(remote_path)

    def add_property(self, key: str, value: object):
        self._properties[key] = value

    def add_transform(self, name: str):
        self._transforms.append(name)

    def get_identifier(self):
        return self._version

    @staticmethod
    def _to_json_object(version):
        return {
            'version': version._version,
            'remote': version._remote,
            'uploadtime': version._time,
            'parts': version._part_files,
            'properties': version._properties,
            'transforms': version._transforms
        }

    @staticmethod
    def _from_json_object(json_object: object):
        version = Version(json_object['version'], json_object['remote'])
        version._part_files = json_object['parts']
        version._properties = json_object['properties']
        version._transforms = json_object['transforms']
        version._time = json_object['uploadtime']
        return version


class FileMetadata:

    def __init__(self):
        self._versions = {}

    def contains_version(self, identifier: str):
        return identifier in self._versions

    def get_version(self, identifier: str):
        return self._versions[identifier]

    def get_version_count(self):
        return len(self._versions)

    def update_version(self, version: Version):
        self._versions[version.get_identifier()] = version

    @staticmethod
    def to_json(file_metadata):
        version_dict = {file_metadata._versions[version].get_identifier(): Version._to_json_object(
            file_metadata._versions[version]) for version in file_metadata._versions}
        return json.dumps({
            'versions': version_dict
        })

    @staticmethod
    def from_json(json_str: str):
        json_object = json.loads(json_str)
        metadata = FileMetadata()
        for version in json_object['versions']:
            constructed_version = Version._from_json_object(
                json_object['versions'][version])
            metadata.update_version(constructed_version)
        return metadata

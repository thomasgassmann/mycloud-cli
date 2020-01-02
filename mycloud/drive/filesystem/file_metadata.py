import json
import time


class Version:

    def __init__(self, version: str, remote_path: str):
        self.version = version
        self.remote = remote_path
        self.part_files = []
        self.properties = {}
        self.transforms = []
        self.time = time.time()

    def add_part_file(self, remote_path: str):
        self.part_files.append(remote_path)

    def add_property(self, key: str, value: object):
        self.properties[key] = value

    def get_property(self, key: str):
        return self.properties[key] if key in self.properties else None

    def get_uploadtime(self):
        return self.time

    def add_transform(self, name: str):
        self.transforms.append(name)

    def get_identifier(self):
        return self.version

    def get_parts(self):
        return self.part_files

    @staticmethod
    def to_json_object(version):
        return {
            'version': version.version,
            'remote': version.remote,
            'uploadtime': version.time,
            'parts': version.part_files,
            'properties': version.properties,
            'transforms': version.transforms
        }

    @staticmethod
    def from_json_object(json_object: object):
        version = Version(json_object['version'], json_object['remote'])
        version.part_files = json_object['parts']
        version.properties = json_object['properties']
        version.transforms = json_object['transforms']
        version.time = json_object['uploadtime']
        return version


class FileMetadata:

    def __init__(self):
        self.versions = {}

    def contains_version(self, identifier: str):
        return identifier in self.versions

    def get_version(self, identifier: str):
        return self.versions[identifier]

    def get_latest_version(self):
        max_time = 0
        max_version = None
        for key in self.versions:
            version = self.versions[key]
            if version.get_uploadtime() > max_time:
                max_time = version.get_uploadtime()
                max_version = version
        return max_version

    def get_version_count(self):
        return len(self.versions)

    def update_version(self, version: Version):
        self.versions[version.get_identifier()] = version

    @staticmethod
    def to_json(file_metadata):
        version_dict = {file_metadata.versions[version].get_identifier(): Version.to_json_object(
            file_metadata.versions[version]) for version in file_metadata.versions}
        return json.dumps({
            'versions': version_dict
        })

    @staticmethod
    def from_json(json_str: str):
        json_object = json.loads(json_str)
        metadata = FileMetadata()
        for version in json_object['versions']:
            constructed_version = Version.from_json_object(
                json_object['versions'][version])
            metadata.update_version(constructed_version)
        return metadata

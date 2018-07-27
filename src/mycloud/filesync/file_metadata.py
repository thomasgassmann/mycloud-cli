import json


class Version:

    def __init__(self, version: str, local_path: str, remote_path: str):
        self._version = version
        self._local = local_path
        self._remote = remote_path
        self._part_files = []
        self._properties = {}


    def add_part_file(self, remote_path: str):
        self._part_files.append(remote_path)

    
    def add_property(self, key: str, value: object):
        self._properties[key] = value


    def get_identifier(self):
        return self._version


    @staticmethod
    def _to_json_object(version):
        return {
            'version': version._version,
            'local': version._local,
            'remote': version._remote,
            'parts': version._part_files,
            'properties': version._properties
        } 


    @staticmethod
    def _from_json_object(json_object: object):
        version = Version(json_object['version'], json_object['local'], json_object['remote'])
        version._part_files = json_object['parts']
        version._properties = json_object['properties']
        return version


class FileMetadata:
    
    def __init__(self):
        self._versions = {}


    def update_version(self, version: Version):
        self._versions[version.get_identifier()] = version

    
    @staticmethod
    def to_json(file_metadata):
        version_dict = { file_metadata._versions[version].get_identifier(): Version._to_json_object(file_metadata._versions[version]) for version in file_metadata._versions }
        return json.dumps({
            'versions': version_dict
        })


    @staticmethod
    def from_json(json_str: str):
        json_object = json.loads(json_str)
        metadata = FileMetadata()
        for version in json_object['versions']:
            constructed_version = Version._from_json_object(json_object['versions'][version])
            metadata.update_version(constructed_version)
        return metadata
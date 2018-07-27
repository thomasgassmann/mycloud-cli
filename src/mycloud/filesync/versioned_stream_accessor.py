from streamapi import CloudStreamAccessor, CloudStream, StreamDirection
from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor, GetObjectRequest, PutObjectRequest
from constants import START_NUMBER_LENGTH, PARTIAL_EXTENSION
from helper import operation_timeout
import os, hashlib, tempfile, json, time


class VersionedCloudStreamAccessor(CloudStreamAccessor):

    def __init__(self, local_file: str, object_resource: str, cloud_stream: CloudStream):
        super().__init__(object_resource, cloud_stream)
        self._local_file = local_file
        self._version = None
        self._current_version_file_parts = []

    
    def get_base_path(self):
        self._initialize_version_if_not_exists()
        versioned_object_resource = ObjectResourceBuilder.combine_cloud_path(self._object_resource, self._version)
        return versioned_object_resource

    
    def get_metadata_file_path(self):
        return ObjectResourceBuilder.combine_cloud_path(self._object_resource, 'mycloud_metadata.json')


    def finish(self, request_executor: MyCloudRequestExecutor):
        if self._cloud_stream.stream_direction != StreamDirection.Up:
            return
        self._initialize_version_if_not_exists()
        existing_metadata_file = self._get_existing_metadata_file(request_executor)
        obj = {
            'version': self._version,
            'local': self._local_file,
            'remote': self._object_resource,
            'parts': self._current_version_file_parts,
            'time': time.time()
        }
        existing_metadata_file['versions'][self._version] = obj
        self._update_metadata_file(request_executor, existing_metadata_file)

    
    def get_part_file(self, index: int):
        part_file_path = super().get_part_file(index)
        self._current_version_file_parts.append(part_file_path)
        return part_file_path

    
    def _update_metadata_file(self, request_executor: MyCloudRequestExecutor, representation):
        metadata_file_path = self.get_metadata_file_path()
        generator = VersionedCloudStreamAccessor._get_bytes(representation)
        put_request = PutObjectRequest(metadata_file_path, generator)
        _ = request_executor.execute_request(put_request)


    def _get_existing_metadata_file(self, request_executor: MyCloudRequestExecutor):
        metadata_file_path = self.get_metadata_file_path()
        get_request = GetObjectRequest(metadata_file_path, ignore_not_found=True)
        response = request_executor.execute_request(get_request)
        if response.status_code == 404:
            # Do it in class
            return {'versions':{}}
        json_data = json.loads(response.text)
        return json_data


    @staticmethod
    def _get_bytes(json_representation):
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            json.dump(json_representation, f)
        with open(filename, 'rb') as f:
            yield f.read()


    def _initialize_version_if_not_exists(self):
        if self._version is None:
            self._version = self._derive_version_from_file()

    
    def _derive_version_from_file(self):
        def open_file(dict):
            return open(dict['file'], 'rb')

        def read_file(dict):
            return dict['file'].read(dict['length'])

        def get_time(dict):
            return os.path.getmtime(dict['file'])
        
        sha = hashlib.sha256()
        BLOCKSIZE = 65536
        stream = operation_timeout(open_file, file=self._local_file)
        time = operation_timeout(get_time, file=self._local_file)
        file_buffer = operation_timeout(read_file, file=stream, length=BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = operation_timeout(read_file, file=stream, length=BLOCKSIZE)
        stream.close()
        sha.update(bytes(str(time).encode()))
        return sha.hexdigest()[:10]
from mycloudapi import ObjectResourceBuilder, MyCloudRequestExecutor, PutObjectRequest
from streamapi.transforms import StreamTransform
from streamapi import CloudStreamAccessor
from helper import operation_timeout
import os, tempfile, json


class FileMetadata:

    def __init__(self):
        self.transforms = []
        self.properties = []
        self.remote_path = None
        self.local_path = None


    def get_object_resource(self):
        return ObjectResourceBuilder.combine_cloud_path(self.remote_path, 'mycloud_metadata.json')


    def _byte_generator(self):
        representation = {
            'transforms': self.transforms,
            'properties': self.properties,
            'remote': self.remote_path,
            'local': self.local_path
        }
        fd, filename = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            json.dump(representation, f)
        with open(filename, 'rb') as f:
            yield f.read()


    @staticmethod
    def push(request_executor: MyCloudRequestExecutor, file_metadata):
        metadata_generator = file_metadata._byte_generator()
        put_request = PutObjectRequest(file_metadata.get_object_resource(), metadata_generator)
        _ = request_executor.execute_request(put_request)


    @staticmethod
    def load(request_executor: MyCloudRequestExecutor, cloud_stream_accessor: CloudStreamAccessor):
        pass


    @staticmethod
    def construct(cloud_stream_accessor: CloudStreamAccessor, local_path: str):
        metadata = FileMetadata()
        for transform in cloud_stream_accessor.get_transforms():
            metadata.transforms.append(transform.get_name())
        metadata.remote_path = cloud_stream_accessor.get_base_path()
        metadata.local_path = local_path
        def read_stat(dict):
            return os.stat(dict['file'])
        stat = operation_timeout(read_stat, file=local_path)
        for s in stat:
            metadata.properties.append(s)
        return metadata
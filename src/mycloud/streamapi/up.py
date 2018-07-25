from mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder, MetadataRequest, PutObjectRequest, GetObjectRequest
from streamapi import UpStream, FileMetadata, StreamDirection
from constants import ENCRYPTION_CHUNK_LENGTH, MY_CLOUD_BIG_FILE_CHUNK_SIZE
from helper import operation_timeout 
from io import BytesIO
import tempfile, os, json


class UpStreamExecutor:

    def __init__(self, request_executor: MyCloudRequestExecutor):
        self.request_executor = request_executor


    def upload_stream(self, file_stream: UpStream, metadata: FileMetadata):
        if file_stream.stream_direction != StreamDirection.Up:
            raise ValueError('Invalid stream direction')

        upload, _ = self._check_upload_validity_for_overwrite(metadata)
        if not upload:
            raise ValueError('Can not overwrite version. Version already exists')
        
        metadata_stream = self._get_metadata_stream(metadata)
        metadata_location = metadata.get_metadata_location()
        metadata_put_request = PutObjectRequest(metadata_location, metadata_stream)
        self.request_executor.execute_request(metadata_put_request)

        current_part_index = file_stream.continued_append_starting_at_part_index or 0
        while not file_stream.is_finished():
            for transform in metadata.get_transforms():
                transform.reset_state()
            generator = self._get_generator(file_stream, MY_CLOUD_BIG_FILE_CHUNK_SIZE, applied_transforms=metadata.get_transforms())
            upload_to = metadata.get_part_file(current_part_index)
            part_put_request = PutObjectRequest(upload_to, generator)
            _ = self.request_executor.execute_request(part_put_request)
            current_part_index += 1
        
        file_stream.close()


    def _get_generator(self, stream: UpStream, max_length=None, applied_transforms=None):
        total_read = 0
        break_execution = False
        stream_finished = False
        while True:
            read_bytes = None
            if break_execution:
                read_bytes = bytes([])
            else:
                read_bytes = stream.read(ENCRYPTION_CHUNK_LENGTH)

            if (len(read_bytes) < ENCRYPTION_CHUNK_LENGTH or read_bytes == b'' or read_bytes is None) and not break_execution:
                stream_finished = True

            if applied_transforms is not None:
                for transform in applied_transforms:
                    read_bytes = transform.transform(read_bytes)

            yield read_bytes

            if stream_finished:
                stream.finished()
                break

            if break_execution:
                break

            total_read += len(read_bytes)
            if total_read > max_length if max_length is not None else False:
                break_execution = True
        

    def _check_upload_validity_for_overwrite(self, metadata: FileMetadata):
        if metadata.is_overwrite_permissible():
            return True, None

        metadata_location = metadata.get_metadata_location()
        put_request = GetObjectRequest(metadata_location, ignore_not_found=True)
        response = self.request_executor.execute_request(put_request)
        if response.status_code == 404:
            return True, None
        
        loaded = FileMetadata.load_from_json_string(response.text)
        return False, loaded


    def _get_metadata_stream(self, metadata: FileMetadata):
        metadata_json = metadata.get_json_representation()
        metadata_stream = None
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                json.dump(metadata_json, tmp)

            with open(path, 'rb') as f:
                metadata_stream = BytesIO(f.read())
        finally:
            os.remove(path)
        return metadata_stream

    
    @staticmethod
    def _safe_file_stream_read(file_stream, length):
        def read_safe(dict):
            return dict['stream'].read(dict['len'])
        return operation_timeout(read_safe, stream=file_stream, len=length)
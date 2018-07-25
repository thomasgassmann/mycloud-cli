from mycloudapi import MyCloudRequestExecutor, GetObjectRequest
from streamapi import DownStream, FileMetadata, StreamDirection
from constants import ENCRYPTION_CHUNK_LENGTH
from helper import operation_timeout 
from io import BytesIO
import tempfile, os, json


class DownStreamExecutor:

    def __init__(self, request_executor: MyCloudRequestExecutor):
        self.request_executor = request_executor


    def download_stream(self, file_stream: DownStream, metadata: FileMetadata):
        if file_stream.stream_direction != StreamDirection.Down:
            raise ValueError('Invalid stream direction')
        
        current_part_index = file_stream.continued_append_starting_at_part_index or 0
        while not file_stream.is_finished():
            for transform in metadata.get_transforms():
                transform.reset_state()
            resource_url = metadata.get_part_file(current_part_index)
            get_request = GetObjectRequest(resource_url, ignore_not_found=True)
            response = self.request_executor.execute_request(get_request)
            if response.status_code == 404:
                file_stream.finished()
                break

            last_chunk = None

            def _transform_chunk(current_chunk, is_last):
                for transform in metadata.get_transforms():
                    current_chunk = transform.transform(current_chunk, last=is_last)
                file_stream.write(current_chunk)

            for chunk in response.iter_content(chunk_size=ENCRYPTION_CHUNK_LENGTH):
                if last_chunk is None:
                    last_chunk = chunk
                    continue

                _transform_chunk(last_chunk, is_last=False)
                last_chunk = chunk            

            _transform_chunk(last_chunk, is_last=True)
            current_part_index += 1

        file_stream.close()


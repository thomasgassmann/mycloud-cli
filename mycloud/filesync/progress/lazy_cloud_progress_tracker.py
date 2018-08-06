from filesync.progress import ProgressTracker
from filesync import VersionedCloudStreamAccessor
from mycloudapi import MyCloudRequestExecutor, MetadataRequest
from mycloudapi.auth import MyCloudAuthenticator
from dateutil import parser
from logger import log
import os
import arrow


class LazyCloudProgressTracker(ProgressTracker):
    def __init__(self, request_executor: MyCloudRequestExecutor):
        super().__init__()
        self._request_executor = request_executor
        self._files = {}
        self._fetched_directories = []

    def file_handled(self, file_path: str, cloud_name: str):
        VersionedCloudStreamAccessor.
        directory = os.path.dirname(cloud_name)
        if not directory.endswith('/'):
            directory += '/'
        if directory in self._fetched_directories:
            if cloud_name in self._files:
                time = self._files[cloud_name]
                update_date = os.path.getmtime(file_path)
                return not update_date > time
            return False, -1
        self._search_directory(directory)
        return self.file_handled(file_path, cloud_name)

    def _search_directory(self, cloud_directory):
        log(f'Searching directory {cloud_directory}...')
        request = MetadataRequest(cloud_directory, ignore_not_found=True)
        response = self._request_executor.execute_request(request)
        (_, fetched_files) = MetadataRequest.format_response(response)
        for fetched_file in fetched_files:
            path = fetched_file['Path']
            modification_time = fetched_file['ModificationTime']
            datetime = parser.parse(modification_time)
            timestamp = arrow.get(datetime).timestamp
            self._files[path] = timestamp
        self._fetched_directories.append(cloud_directory)

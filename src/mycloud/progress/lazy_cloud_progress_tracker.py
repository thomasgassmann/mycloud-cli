from progress import ProgressTracker
from mycloudapi import MetadataRequest
from dateutil import parser
from logger import log
import os, arrow


class LazyCloudProgressTracker(ProgressTracker):
    def __init__(self, bearer):
        super().__init__()
        self.files = {}
        self.bearer_token = bearer
        self.fetched_directories = []


    def file_handled(self, file_path, cloud_name):
        directory = os.path.dirname(cloud_name)
        if not directory.endswith('/'):
            directory += '/'
        if directory in self.fetched_directories:
            if cloud_name in self.files:
                time = self.files[cloud_name]
                update_date = os.path.getmtime(file_path)
                return not update_date > time
            return False
        self.__search_directory(directory)
        return self.file_handled(file_path, cloud_name)


    def __search_directory(self, cloud_directory):
        log(f'Searching directory {cloud_directory}...')
        request = MetadataRequest(cloud_directory, self.bearer_token)
        (_, fetched_files) = request.get_contents(ignore_not_found=True)
        for fetched_file in fetched_files:
            path = fetched_file['Path']
            modification_time = fetched_file['ModificationTime']
            datetime = parser.parse(modification_time)
            timestamp = arrow.get(datetime).timestamp
            self.files[path] = timestamp
        self.fetched_directories.append(cloud_directory)
from mycloudapi import MyCloudRequestExecutor
from filesync.progress.progress_tracker import ProgressTracker
from helper import get_all_files_recursively
from dateutil import parser
import arrow


class CloudProgressTracker(ProgressTracker):
    def __init__(self, request_executor: MyCloudRequestExecutor, mycloud_base_directory):
        super().__init__()
        self.request_executor = request_executor
        self.mycloud_base_directory = mycloud_base_directory

    def load_if_exists(self):
        self.load()

    def load(self):
        self.files = {}
        for file in get_all_files_recursively(self.request_executor, self.mycloud_base_directory):
            datetime = parser.parse(file['ModificationTime'])
            timestamp = arrow.get(datetime).timestamp
            self.files[file['Path']] = timestamp

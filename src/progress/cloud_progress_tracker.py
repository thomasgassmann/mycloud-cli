from progress_tracker import ProgressTracker
from src.helper import directory_list
from dateutil import parser
import arrow


class CloudProgressTracker(ProgressTracker):
    def __init__(self, bearer_token, mycloud_base_directory):
        super().__init__('progress')
        self.bearer_token = bearer_token
        self.mycloud_base_directory = mycloud_base_directory


    def load_if_exists(self):
        self.load()


    def load(self):
        files_list = []
        self.files = {}
        directory_list.recurse_directory(files_list, self.mycloud_base_directory, self.bearer_token, ['Path', 'ModificationTime'])
        for file in files_list:
            datetime = parser.parse(file[1])
            timestamp = arrow.get(datetime).timestamp
            self.files[file[0]] = timestamp